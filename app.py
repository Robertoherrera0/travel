import requests
import os
import folium
import matplotlib.pyplot as plt
from folium.plugins import MarkerCluster
from flask import Flask, render_template, send_from_directory
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)

# Function to get aurora data for all locations and generate visualizations
def get_aurora_data_for_all_locations():
    locations_url = "http://api.auroras.live/v1/?type=locations"
    
    try:
        # Fetch the locations data
        response = requests.get(locations_url)
        response.raise_for_status()
        locations_data = response.json()

        # Remove 'message' key if it exists, because it's not a location
        if 'message' in locations_data:
            del locations_data['message']

        # Data holders
        locations = []
        aurora_probabilities = []
        map_data = []

        # Iterate over the locations and get data for each one
        for idx, loc in locations_data.items():  
            lat, long = loc['lat'], loc['long']
            country = loc['country']  # Get the country information
            url = f"http://api.auroras.live/v1/?type=all&lat={lat}&long={long}&weather=true&probability=true&forecast=false&threeday=true"
            
            # Fetch aurora data for each location
            data_response = requests.get(url)
            data_response.raise_for_status()
            data = data_response.json()

            # Extract probability and color
            probability = data['probability'].get('value', 0)
            colour = data['probability'].get('colour', 'N/A')

            # Append data for plotting
            locations.append(f"{loc['name']}, {country}")  # Include the country in the name
            aurora_probabilities.append(probability)

            # Add data to map visualization
            map_data.append({
                "name": loc['name'],
                "lat": lat,
                "long": long,
                "probability": probability,
                "colour": colour,
                "country": country  # Include the country in the map data
            })

        # Format the date for a more readable format
        formatted_time = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S+00:00").strftime("%B %d, %Y - %H:%M:%S UTC")
        
        # Plot the aurora visibility probabilities for all locations
        plt.figure(figsize=(10, 6))
        plt.barh(locations, aurora_probabilities, color='skyblue')
        plt.title(f"Aurora Visibility Probability by Location ({formatted_time})")
        plt.xlabel("Probability (%)")
        plt.ylabel("Location (City, Country)")
        
        # Save the plot as an image in the 'static' folder
        plot_path = os.path.join('static', 'probability_plot.png')
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        # Create a map to visualize the locations
        map_center = [0, 0]  # Starting position of the map (0,0)
        m = folium.Map(location=map_center, zoom_start=2)

        marker_cluster = MarkerCluster().add_to(m)

        # Add markers for each location to the map
        for location in map_data:
            folium.Marker(
                location=[location["lat"], location["long"]],
                popup=f"{location['name']} - Country: {location['country']} - Probability: {location['probability']}%, Colour: {location['colour']}",
            ).add_to(marker_cluster)

        # Save the map as an HTML file in the 'static' folder
        map_path = os.path.join('static', 'aurora_map.html')
        m.save(map_path)

        return plot_path, map_path

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, None

# Route to the home page
@app.route('/')
def index():
    # Get the data, generate the plot, and map
    plot_url, map_url = get_aurora_data_for_all_locations()
    return render_template('index.html', plot_url=plot_url, map_url=map_url)

# Route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Ensure the 'static' folder exists
    if not os.path.exists('static'):
        os.makedirs('static')

    # Run the Flask app
    app.run(debug=True)
