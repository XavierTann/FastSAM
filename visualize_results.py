# Import the SamGeo class for raster-to-vector conversion
from samgeo.fast_sam import SamGeo
from samgeo import tms_to_geotiff
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import requests
import os
import clip
from PIL import Image
import rasterio
import math
from pyproj import Transformer

# FOR PREVIEW
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import Affine
from rasterio.windows import Window
from rasterio.mask import mask

# Specify the model path and image path
model_path = './weights/FastSAM-x.pt'  # Path to the FastSAM model
# Output path for the raster mask (GeoTIFF)
output_raster = './output/output_raster.jpg'
# Output path for the vector file (GeoJSON)
output_vector = './output/output_vector.geojson'

# Step 2: Initialize the model (SamGeo) with the FastSAM model
sam = SamGeo(model="FastSAM-x.pt")  # Initialize SamGeo with the FastSAM model


# Define the local output path
output_folder = "./output"
output_file_path = os.path.join(output_folder, "initial_file.tif")
geo_tiff_path = './images/FastSam_Sample_Image-2.tif'

# # Download the file from the public URL
# url = "https://storage.googleapis.com/raster-datasources/FastSam_Sample_Image-2.tif"
# response = requests.get(url)
# with open(output_file_path, "wb") as f:
#     f.write(response.content)
# print(f"File downloaded successfully to: {output_file_path}")
# # Set the image for segmentation using the full downloaded image path
# sam.set_image(output_file_path)

# image_path = './output/FastSam_Sample_Image-2.tif'
image_path = './images/cat.jpg'
sam.set_image(image_path)



### CONVERTING FROM GEO COORDINATES TO PIXEL COORDINATES ###
# # Load the GeoTIFF file path
# geo_tiff_path = './images/FastSam_Sample_Image-2.tif'
# # Create a transformer to convert from the current projection (assuming EPSG:3857) to EPSG:4326 (lat/lon)
# transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
# with rasterio.open(geo_tiff_path) as dataset:
#     # Get image dimensions
#     imagepxwidth = dataset.width  # Image width in pixels
#     imagepxheight = dataset.height  # Image height in pixels

#     # Get the affine transformation (transform matrix) to relate pixel coordinates to geographic coordinates
#     transform = dataset.transform

#     # Get the four corner coordinates of the image (in geographic coordinates)
#     minlon, maxlat = transform * (0, 0)  # Top-left corner (minlon, maxlat)
#     # Bottom-right corner (maxlon, minlat)
#     maxlon, minlat = transform * (imagepxwidth, imagepxheight)

#    # Convert the coordinates to latitude and longitude (degrees)
#     minlon, maxlat = transformer.transform(
#         minlon, maxlat)  # Convert top-left corner
#     maxlon, minlat = transformer.transform(
#         maxlon, minlat)  # Convert bottom-right corner

#     # Print the image size and geographic bounding box
#     print(f"Image dimensions: Width={
#           imagepxwidth} pixels, Height={imagepxheight} pixels")
#     print(f"Top-left corner: Longitude={minlon}, Latitude={maxlat}")
#     print(f"Bottom-right corner: Longitude={maxlon}, Latitude={minlat}")


# def geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
#     # Calculate the x pixel coordinate
#     x = math.floor(((lon - minlon) / (maxlon - minlon)) * imagepxwidth)
#     # Calculate the y pixel coordinate
#     y = math.floor(((maxlat - lat) / (maxlat - minlat)) * imagepxheight)

#     return x, y


# list_of_points = [
#     (-80.38231955557056, 25.74206442455916),
#     (-80.38340203074395, 25.739572430294025),
#     (-80.3831423585816, 25.73956440038416),
#     (-80.38335191539677, 25.739495833626222),
#     (-80.38312474090651, 25.739515942379313)]

# pixel_coordinates = [geographic_to_pixel(
#     lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) for lon, lat in list_of_points]
# # Optionally, print pixel coordinates for reference
# print("Converted pixel coordinates:")
# for i, coord in enumerate(pixel_coordinates):
#     print(f"Point {i+1}: X={coord[0]}, Y={coord[1]}")

# img = Image.open(geo_tiff_path)
# # Plot the image and overlay the points
# fig, ax = plt.subplots()
# ax.imshow(img)

# # Plot each point on the image as red circles
# for pixel_x, pixel_y in pixel_coordinates:
#     # 'ro' means red circle marker
#     ax.plot(pixel_x, pixel_y, 'ro', markersize=8)

# # Turn off the axis to focus on the image
# plt.axis('off')

# # Show the plot with points
# plt.show()

### END OF CONVERTING FROM GEO COORDINATES TO PIXEL COORDINATES ###


# # CROPPPING IMAGE FOR PREVIEW
# Define the path to the input and output GeoTIFF files
input_geotiff = geo_tiff_path
output_geotiff = './output/preview.tif'
# Open the input GeoTIFF
with rasterio.open(input_geotiff) as src:
    # xmin, ymin, xmax, ymax = src.bounds
    # print(xmin, ymin, xmax, ymax)
    # # Get image dimensions
    # x_range = xmax - xmin
    # y_range = ymax-ymin

    # xmin = xmin+(x_range / 3)
    # ymin = ymin+(y_range/3)
    # xmax = xmax - (x_range/3)
    # ymax = ymax - (y_range/3)

    # my_geojson = [{
    #     "type": "Polygon",
    #     "coordinates": [
    #         [
    #             [xmin, ymin],
    #             [xmax, ymin],
    #             [xmax, ymax],
    #             [xmin, ymax],
    #             [xmin, ymin]
    #         ],
    #     ]
    # }]
    # print(my_geojson)

    # clipped, transform = mask(src, my_geojson, crop=True)
    # print(clipped)

    imagepxwidth = src.width  # Image width in pixels
    imagepxheight = src.height  # Image height in pixels
    print(imagepxwidth)
    print(imagepxheight)

    # Get the affine transformation (transform matrix) to relate pixel coordinates to geographic coordinates
    transform = src.transform
    print(transform)

    profile = src.profile

    # Get the bottom-left corner (pixel coordinates: (0, image height))
    bottom_left_webmerc = transform * (0, imagepxheight)
    minlon, minlat = bottom_left_webmerc  # Bottom-left corner in Web Mercator

    # Calculate the upper-right corner for a 500x500 pixel crop starting from the bottom-left
    upper_right_webmerc = transform * (1000, imagepxheight-1000)  # (500px to the right and 500px up)
    maxlon, maxlat = upper_right_webmerc  # Upper-right corner in Web Mercator
    window = from_bounds(minlon, minlat, maxlon, maxlat, transform)

    # Get the affine transform, CRS, and other metadata
    crs = src.crs
    profile = src.profile
    print("OLD PROFILE")
    print(profile)

    print(crs)

    # Compute the window (pixel coordinates) for the specified geographic bounding box

    window_width = 2000  # Increase from 500 to 2000 to make the crop larger
    window_height = 2000  # Increase from 500 to 2000
    window = Window(0, imagepxheight - window_height, window_width, window_height)

    # Read the data within the window
    cropped_data = src.read(window=window)
    print(cropped_data.shape[1])
    print(cropped_data.shape[2])

    # Update the transform to account for the crop
    new_transform = src.window_transform(window)
    print(new_transform)

    # Update the metadata profile
    profile.update({
        'height': cropped_data.shape[1],
        'width': cropped_data.shape[2],
        'transform': transform,

    })
    print("NEW PROFILE  ")
    print(profile)

    # Write the cropped image to a new GeoTIFF
    with rasterio.open(output_geotiff, 'w', **profile) as dst:
        dst.write(cropped_data)


print(f'Cropped GeoTIFF saved to {output_geotiff}')

# image = Image.open(image_path)
# width, height = image.size
# crop_area = (0, 0, width-200, height-200)  # Left: 0, Top: height-200, Right: 200, Bottom: height
# cropped_image = image.crop(crop_area)
# cropped_image.save('./images/cropped_image.jpg')
# sam.set_image('./images/cropped_image.jpg')

# #"everything" prompt
# sam.everything_prompt(output='./output/cropped_image.jpg')  # Output the mask as a GeoTIFF

# # text prompt
# sam.text_prompt(text = "just the eyes", output = './output/text_segmentation.jpg')
# sam.show_anns('./output/text_segmentation.png')

# # point prompt
# positive_points = [[450, 300], [400, 200], [500, 200], [450, 450]]  # Areas to include (head, ears, body)
# negative_points = [[100, 100], [550, 600], [300, 350]]  # Areas to exclude (background and red object)
# # Define the labels for the points: 1 for positive points, 0 for negative points
# point_labels = [1, 1, 1, 1, 0, 0, 0]  # 1: Positive, 0: Negative
# sam.point_prompt(points=positive_points + negative_points, pointlabel=point_labels)
# # Save the result as an image (e.g., PNG)
# output_image = "cat_segmentation_with_points.png"
# sam.show_anns(output_image)

# # Visualizing the points on the output image
# img = Image.open(output_image)
# fig, ax = plt.subplots(1)
# ax.imshow(img)
# for point in positive_points:
#     ax.plot(point[0], point[1], 'go', markersize=10, label="Positive Points")
# for point in negative_points:
#     ax.plot(point[0], point[1], 'ro', markersize=10, label="Negative Points")
# ax.axis('off')
# plt.show()

# # Box Prompt
# img = Image.open(image_path)
# # Get image dimensions
# image_width, image_height = img.size
# preview_width = 700
# preview_height = 2000
# box = [0, image_height-preview_height, preview_width, preview_height]
# print("Bounding box:", box)

# boxes = [box]  # Format: [x_min, y_min, width, height]
# boxes = [[0, 442, 700, 2000]]
# sam.box_prompt(bboxes=boxes, conf=0.1, iou=0.9)
# # Save the result as an image (e.g., PNG)
# output_image = "./output/box_segmentation.png"
# sam.show_anns(output = output_image)# Plot the segmentation result and add bounding boxes

# # Plot the segmentation result and add bounding boxes
# fig, ax = plt.subplots(1)
# img = plt.imread(output_image)  # Load the saved segmentation result
# ax.imshow(img)

# # Draw each bounding box on the image
# for box in boxes:
#     x_min, y_min, width, height = box
#     rect = patches.Rectangle((x_min, y_min), width, height, linewidth=2, edgecolor='r', facecolor='none')
#     ax.add_patch(rect)

# # Show the image with bounding boxes
# plt.show()


# Step 3: Convert the raster segmentation result to a vector format
# sam.raster_to_vector(output_raster, output_vector)  # Convert GeoTIFF to GeoJSON


# # (Optional) Display the output raster image for reference using matplotlib
# img = plt.imread(output_raster)
# plt.imshow(img)
# plt.axis('off')
# plt.show()

print(f"Vector file saved as: {output_vector}")
