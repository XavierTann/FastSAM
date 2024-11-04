from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import os
import glob

# Import the SamGeo class for raster-to-vector conversion
from samgeo.fast_sam import SamGeo
import matplotlib.pyplot as plt

# Import LANGSAM
from samgeo.text_sam import LangSAM

# for transforming geographic coords to pixel coords
import rasterio
import math
from pyproj import Transformer

# for preview
from rasterio.windows import Window

# for converting geotiff to geojson
import json

# LOGGING #
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG level to capture all levels of logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Customize the log format
    handlers=[
        logging.FileHandler("server.log"),  # Logs output to a file named 'server.log'
        logging.StreamHandler()  # Also outputs to the console
    ]
)
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

def extract_patch(
    input_path: str,
    output_path: str,
    position: str = "top_left",  # Position options (use any one):
                                # "top_left"      - Starts from (0,0)
                                # "top_right"     - Starts from (width-patch_size, 0)
                                # "bottom_left"   - Starts from (0, height-patch_size)
                                # "bottom_right"  - Starts from (width-patch_size, height-patch_size)
                                # "center"        - Starts from ((width-patch_size)/2, (height-patch_size)/2)
    patch_size: int = 1024       # Size options:
                               # 256 - for 256x256 pixel patch
                               # 512 - for 512x512 pixel patch
):
    """
    Extract a patch from specified position of the image.
    
    Args:
        input_path (str): Path to input raster file
        output_path (str): Path to save the extracted patch
        position (str): Position to extract patch from
            Valid options:
            - "top_left": Extract from top left corner
            - "top_right": Extract from top right corner
            - "bottom_left": Extract from bottom left corner
            - "bottom_right": Extract from bottom right corner
            - "center": Extract from center of image
        patch_size (int): Size of the patch (256 or 512)
    
    Returns:
        Tuple[int, int]: The (x, y) starting position of the extracted patch
        
    Example usage:
        # For top left 256x256 patch:
        extract_patch("input.tif", "output.tif", position="top_left", patch_size=256)
        
        # For bottom right 512x512 patch:
        extract_patch("input.tif", "output.tif", position="bottom_right", patch_size=512)
        
        # For center 256x256 patch:
        extract_patch("input.tif", "output.tif", position="center", patch_size=256)
    """
    
    
    # Valid position options
    valid_positions = {
        "top_left": "Extract from top left (0,0)",
        "top_right": "Extract from top right (width-patch_size, 0)",
        "bottom_left": "Extract from bottom left (0, height-patch_size)",
        "bottom_right": "Extract from bottom right (width-patch_size, height-patch_size)",
        "center": "Extract from center ((width-patch_size)/2, (height-patch_size)/2)"
    }
    
    # Validate position
    if position not in valid_positions:
        raise ValueError(
            f"Invalid position. Please use one of: {', '.join(valid_positions.keys())}"
        )
    
    try:
        with rasterio.open(input_path) as src:
            # Get image dimensions
            height = src.height
            width = src.width
            
            # Validate input image size
            if height < patch_size or width < patch_size:
                raise ValueError(
                    f"Input image ({width}x{height}) is smaller than "
                    f"the requested patch size ({patch_size}x{patch_size})"
                )
            
            # Calculate start position based on chosen position
            if position == "top_left":
                start_x, start_y = 0, 0
            elif position == "top_right":
                start_x, start_y = width - patch_size, 0
            elif position == "bottom_left":
                start_x, start_y = 0, height - patch_size
            elif position == "bottom_right":
                start_x, start_y = width - patch_size, height - patch_size
            else:  # center
                start_x = (width - patch_size) // 2
                start_y = (height - patch_size) // 2
            
            # Define the window for extraction
            window = Window(start_x, start_y, patch_size, patch_size)
            
            # Read the data within the window
            data = src.read(window=window)
            
            # Update the transform for the new window
            transform = rasterio.windows.transform(window, src.transform)
            
            # Create the output raster with updated metadata
            kwargs = src.meta.copy()
            kwargs.update({
                'height': patch_size,
                'width': patch_size,
                'transform': transform
            })
            
            # Write the output file
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                dst.write(data)
            
            return start_x, start_y
            
    except rasterio.errors.RasterioIOError:
        raise FileNotFoundError(f"Could not open input file: {input_path}")
    except Exception as e:
        raise RuntimeError(f"Error processing image: {str(e)}")

def delete_all_output_files(folder_path):
    # Use glob to get all files in the folder
    files = glob.glob(os.path.join(folder_path, '*'))  # Adjust pattern if you want specific file types (e.g., '*.txt')
    
    for file_path in files:
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# for point and box prompt.
def geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
            # Calculate the x pixel coordinate
            x = math.floor(((lon - minlon) / (maxlon - minlon)) * imagepxwidth)
            # Calculate the y pixel coordinate
            y = math.floor(((maxlat - lat) / (maxlat - minlat))
                           * imagepxheight)

            return x, y

# for box prompt
def polygon_to_bbox(polygon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
            """
            Convert a geographic polygon to a bounding box in pixel coordinates.
            polygon: List of (lon, lat) tuples defining the polygon's vertices.
            Returns: [x_min, y_min, x_max, y_max] for each polygon's bounding box.
            """
            pixel_coords = [geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight)
                            for lon, lat in polygon]
            xs, ys = zip(*pixel_coords)
            return [min(xs), min(ys), max(xs), max(ys)]

def get_preview(file_path):
    sam = SamGeo(model="FastSAM-x.pt")
    cropped_output_path = './output/preview_before_sam.tif'
    POSITION = 'center'
    extract_patch(file_path, cropped_output_path, POSITION)

    sam.set_image(cropped_output_path)

    output_path_after_sam = './output/preview_after_sam3.tif'
    sam.everything_prompt(output=output_path_after_sam)

    return output_path_after_sam

def point_prompt(file_path, positivePoints, negativePoints):
        # Initialize an empty list for all points
        all_points = []

        # Extract coordinates from each point and add to all_points
        for point in positivePoints:
            coordinates = point['geometry']['coordinates']  # Extract coordinates
            all_points.append(coordinates)  # Append to all_points
        
        for point in negativePoints:
            coordinates = point['geometry']['coordinates']  # Extract coordinates
            all_points.append(coordinates)  # Append to all_points

        
        # Create labels: 1 for each positive point, -1 for each negative point
        pointlabel = [1] * len(positivePoints) + [-1] * len(negativePoints)
        print(all_points)
        print(pointlabel)

        transformer = Transformer.from_crs(
            "EPSG:3857", "EPSG:4326", always_xy=True)
        with rasterio.open(file_path) as dataset:
            # Get image dimensions
            imagepxwidth = dataset.width  # Image width in pixels
            imagepxheight = dataset.height  # Image height in pixels

            # Get the affine transformation (transform matrix) to relate pixel coordinates to geographic coordinates
            transform = dataset.transform

            # Get the four corner coordinates of the image (in geographic coordinates)
            minlon, maxlat = transform * (0, 0)
            maxlon, minlat = transform * (imagepxwidth, imagepxheight)

            # Convert the coordinates to latitude and longitude (degrees)
            minlon, maxlat = transformer.transform(
                minlon, maxlat)  # Convert top-left corner
            maxlon, minlat = transformer.transform(
                maxlon, minlat)  # Convert bottom-right corner

        points = [geographic_to_pixel(
            lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) for lon, lat in all_points]

        sam = SamGeo(model="FastSAM-x.pt")
        sam.set_image(file_path)
        output_path = "./output/point_segmentation2.tif"
        sam.point_prompt(points=points, pointlabel=pointlabel, output = output_path)
        return output_path

def box_prompt(file_path, listOfPolygons):
        
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    with rasterio.open(file_path) as dataset:
            # Get image dimensions
            imagepxwidth = dataset.width
            imagepxheight = dataset.height
            # Get the affine transformation
            transform = dataset.transform
            # Calculate the image's bounding box in geographic coordinates
            minlon, maxlat = transform * (0, 0)  # Top-left corner
            maxlon, minlat = transform * (imagepxwidth, imagepxheight)  # Bottom-right corner

            # Convert coordinates to latitude and longitude (degrees)
            minlon,maxlat  = transformer.transform(minlon, maxlat)
            maxlon, minlat  = transformer.transform(maxlon, minlat)

    # Convert each polygon to a bounding box
    bboxes = [polygon_to_bbox(polygon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) for polygon in listOfPolygons]
    print(bboxes)
        # Use the bounding boxes with the box_prompt function
    sam = SamGeo(model="FastSAM-x.pt")
    sam.set_image(file_path)
    output_path = './output/box_segmentation3.tif'
    sam.box_prompt(bboxes=bboxes, output=output_path)
    return output_path


def text_prompt(file_path, text_prompt):
    sam = LangSAM()
    output_path = './output/text_segmentation5.tif'
    sam.predict(file_path, text_prompt, box_threshold=0.30, text_threshold=0.30, output = output_path)
    return output_path

def everything_prompt(file_path): 
     sam = SamGeo(model="FastSAM-x.pt")
     sam.set_image(file_path)
     output_path = './output/everything_segmentation1.tif'
     sam.everything_prompt(output=output_path)
     return output_path

def download_file(signed_url, fileName):
      # Download the file from the signed URL
        response = requests.get(signed_url, stream=True)

        images_folder = "./images"

        original_file_path = os.path.join(images_folder, fileName)

        # Download the file from the public URL
        response = requests.get(signed_url)

        # Save the file to the images folder
        with open(original_file_path, "wb") as f:
            f.write(response.content)   
        
        return original_file_path


@app.route('/test', methods=['POST'])
def test():
    try:

        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        signed_url = data.get('signedUrl')
        fileName = data.get('fileName')
        original_file_path = download_file(signed_url, fileName)

        # Check if the original file path is provided
        if not original_file_path:
            raise ValueError("Missing parameter: original file path is required.")

        folder_path = './output'
        delete_all_output_files(folder_path)

        

        mode = data.get('mode')
        match mode:
            case 'text_prompt':
                textPrompt = data.get('textPrompt')
                if not textPrompt:
                    raise ValueError("Missing parameter: 'textPrompt' is required for text mode.")
                output_path = text_prompt(original_file_path, textPrompt)

            case 'point_prompt':
                positivePoints = data.get('positivePoints')
                negativePoints = data.get('negativePoints')
                # if not positivePoints or negativePoints: 
                #      logger.error('No Points detected.')
                output_path = point_prompt(original_file_path, positivePoints, negativePoints)

            case 'box_prompt':
                listOfPolygons = data.get('listOfPolygons')
                if not listOfPolygons:
                    raise ValueError("Missing parameter: 'listOfPolygons' is required for polygon mode.")
                output_path = box_prompt(original_file_path, listOfPolygons)

            case 'everything_prompt':
                output_path = everything_prompt(original_file_path)

            case 'preview':
                output_path = get_preview(original_file_path)

            case _:
                raise ValueError("Invalid mode provided.")

        data_format = data.get('data_format') 
        if data_format == 'vector':
            
            output_raster = output_path
            output_vector = './output/output_vector.geojson'
            sam = SamGeo(model="FastSAM-x.pt")
            sam.raster_to_vector(output_raster, output_vector)

            listOfFeatures = []
            
            # comment this out 
            # output_vector = './images/sample_image.geojson'

            # Open and read the output_vector GeoJSON file
            with open(output_vector, 'r') as file:
                geojson_data = json.load(file)

                # Check if the data is in the correct format
                if 'features' in geojson_data:
                    # Iterate through each feature and add it to the list
                    for feature in geojson_data['features']:
                        listOfFeatures.append(feature)


             

        response = make_response(jsonify({
            "status": "success",
            "message": "File processed successfully",
            "features": listOfFeatures 
        
        }))
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        return response

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "type": str(type(e).__name__)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

        
