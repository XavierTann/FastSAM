from flask import Flask, request, jsonify, send_file
import os
from fastsam import FastSAM, FastSAMPrompt  # Import your SAM model
from PIL import Image
import io
import logging
from samgeo.fast_sam import SamGeo 

import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for non-GUI rendering

# Configure logging
logging.basicConfig(level=logging.DEBUG)
# Initialize Flask app
app = Flask(__name__)



# Path to your SAM model (make sure it's the correct path)
model_path = './weights/FastSAM-s.pt'  
model = FastSAM(model_path)

# Define the /segment endpoint
@app.route('/segment', methods=['POST'])
def segment():
    logging.debug("Connection established.")

    data = request.get_json()
    signed_url = data.get('signedUrl')

    output_folder = "./output"

    output_file_path = os.path.join(output_folder, "FastSam_Sample_Image-2.tif")

    # Download the file from the public URL
    response = requests.get(signed_url)

    # Save the file to the output folder
    with open(output_file_path, "wb") as f:
        f.write(response.content)

    

# # Save the uploaded image temporarily
#     input_image_path = './images/uploaded_image.tif'
#     image.save(input_image_path)

#     # Initialize SamGeo with the local FastSAM model
#     sam = SamGeo(model="FastSAM-x.pt")
    
#     # Set the image for segmentation
#     sam.set_image(input_image_path)

#     # Perform the segmentation using the "everything" prompt
#     output_raster = './output/mask.tif'  # Output path for the raster mask (GeoTIFF)
#     sam.everything_prompt(output=output_raster)

#     # Convert the raster segmentation result to a vector format (GeoJSON)
#     output_vector = './output/vector_sample_image.geojson'
#     sam.raster_to_vector(output_raster, output_vector)

#     # Send the vector file (GeoJSON) back to the client
#     return send_file(output_vector, mimetype='application/geo+json')

    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
