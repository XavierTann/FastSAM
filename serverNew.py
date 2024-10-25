from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import logging
import requests
import os

# Import the SamGeo class for raster-to-vector conversion
from samgeo.fast_sam import SamGeo
import matplotlib.pyplot as plt

# for transforming geographic coords to pixel coords
import rasterio
import math
from pyproj import Transformer


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS more specifically
CORS(app, resources={
    r"/test": {
        # Adjust this to match your frontend URL
        "origins": ["http://localhost:3000"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})


@app.route('/test', methods=['POST'])
def test():
    try:

        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        signed_url = data.get('signedUrl')

        fileName = data.get('fileName')

        textPrompt = data.get('textPrompt')

        listOfPoints = data.get('listOfPoints')

        # Download the file from the signed URL
        response = requests.get(signed_url, stream=True)

        output_folder = "./output"

        original_file_path = os.path.join(output_folder, fileName)

        # Download the file from the public URL
        response = requests.get(signed_url)

        # Save the file to the output folder
        with open(original_file_path, "wb") as f:
            f.write(response.content)

        # Output path for the raster mask (GeoTIFF)
        output_raster = './output/output_raster.tif'
        # Output path for the vector file (GeoJSON)
        output_vector = './output/output_vector.geojson'

        sam = SamGeo(model="FastSAM-x.pt")

        # POINT PROMPT #

        # TRANSOFRMING GEOG TO PIXEL COORDS
        geo_tiff_path = original_file_path
        transformer = Transformer.from_crs(
            "EPSG:3857", "EPSG:4326", always_xy=True)
        with rasterio.open(geo_tiff_path) as dataset:
            # Get image dimensions
            imagepxwidth = dataset.width  # Image width in pixels
            imagepxheight = dataset.height  # Image height in pixels

            # Get the affine transformation (transform matrix) to relate pixel coordinates to geographic coordinates
            transform = dataset.transform

            # Get the four corner coordinates of the image (in geographic coordinates)
            # Top-left corner (minlon, maxlat)
            minlon, maxlat = transform * (0, 0)
            # Bottom-right corner (maxlon, minlat)
            maxlon, minlat = transform * (imagepxwidth, imagepxheight)

        # Convert the coordinates to latitude and longitude (degrees)
            minlon, maxlat = transformer.transform(
                minlon, maxlat)  # Convert top-left corner
            maxlon, minlat = transformer.transform(
                maxlon, minlat)  # Convert bottom-right corner

            # Print the image size and geographic bounding box
            print(f"Image dimensions: Width={imagepxwidth} pixels, Height={imagepxheight} pixels")
            print(f"Top-left corner: Longitude={minlon}, Latitude={maxlat}")
            print(
                f"Bottom-right corner: Longitude={maxlon}, Latitude={minlat}")

        def geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
            # Calculate the x pixel coordinate
            x = math.floor(((lon - minlon) / (maxlon - minlon)) * imagepxwidth)
            # Calculate the y pixel coordinate
            y = math.floor(((maxlat - lat) / (maxlat - minlat))
                           * imagepxheight)

            return x, y
        pixel_coordinates = [geographic_to_pixel(
            lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) for lon, lat in listOfPoints]

        sam.set_image(original_file_path)
        # positive_points = [[450, 300], [400, 200], [500, 200], [450, 450]]
        # positive_points = pixel_coordinates
        points = pixel_coordinates
        negative_points = [[100, 100], [550, 600], [300, 350]]  # Areas to exclude (background and red object)
        # Define the labels for the points: 1 for positive points, 0 for negative points
        point_labels = [1, 1, 1]  # 1: Positive, 0: Negative
        sam.point_prompt(points=points, pointlabel=point_labels)
        # Save the result as an image (e.g., PNG)
        output_image = "./output/output_segmentation_with_points.tif"
        sam.show_anns(output_image)

        # # Perform segmentation based on the text prompt using langsam
        # sam.predict(output_file_path, textPrompt, box_threshold=0.24, text_threshold=0.24)

        # # Save the result to a raster file (GeoTIFF)
        # sam.show_anns(
        #     cmap="Greys_r",
        #     add_boxes=False,
        #     alpha=1,
        #     title="Segmentation Result",
        #     blend=False,
        #     output=output_raster
        # )

        # Convert the raster result to vector format
        # sam.raster_to_vector(output_raster, output_vector)

        # sam = SamGeo(model="FastSAM-x.pt")

        # sam.set_image(output_file_path)

        # sam.everything_prompt(output=output_raster)

        # sam.raster_to_vector(output_raster, output_vector)

        response = make_response(jsonify({
            "status": "success",
            "message": "File processed successfully"
        }))
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        return response

    except Exception as e:
        logger.exception("Error processing request")
        return jsonify({
            "status": "error",
            "message": str(e),
            "type": str(type(e).__name__)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
