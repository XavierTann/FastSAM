import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
import math

# Define your GeoTIFF path
geo_tiff_path = './images/FastSam_Sample_Image-2.tif'

# Define polygons with inverted latitude and longitude
listOfPolygons = [
    [
        [25.73991774402617, -80.3339022780406],
        [25.73986225454644, -80.38222408137973],
        [25.740653646440444, -80.38196613939832],
        [25.74046563007891, -80.3832802280463],
        [25.73991774402617, -80.3339022780406]  # Closing the polygon
    ],
    [
        [25.74499251367703, -80.38092995298622],
        [25.743577128750844, -80.38096632472456],
        [25.743898018146436, -80.3800936165897],
        [25.74585570027001, -80.38017016383242],
        [25.74499251367703, -80.38092995298622]  # Closing the polygon
    ]
]

# Function to convert geographic to pixel coordinates
def geographic_to_pixel(lon, lat, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
    # Convert geographic coordinates (with swapped lat and lon) to pixel coordinates
    x = math.floor(((lat - minlon) / (maxlon - minlon)) * imagepxwidth)
    y = math.floor(((maxlat - lon) / (maxlat - minlat)) * imagepxheight)
    return x, y

# Open the GeoTIFF image
with rasterio.open(geo_tiff_path) as dataset:
    # Get the dimensions and affine transform
    imagepxwidth = dataset.width
    imagepxheight = dataset.height
    transform = dataset.transform
    
    # Calculate geographic bounds of the image
    minlat, maxlon = transform * (0, 0)  # Top-left corner (inverted)
    maxlat, minlon = transform * (imagepxwidth, imagepxheight)  # Bottom-right corner (inverted)
    
    # Convert bounds to geographic coordinates (latitude and longitude)
    minlat, maxlon = dataset.xy(0, 0)
    maxlat, minlon = dataset.xy(imagepxheight, imagepxwidth)

    # Display the GeoTIFF image
    fig, ax = plt.subplots(figsize=(10, 10))
    show(dataset, ax=ax, title="Polygons Overlayed on GeoTIFF Image")

    # Convert each polygon's points to pixel coordinates and plot them
    for polygon in listOfPolygons:
        pixel_coords = [geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) 
                        for lat, lon in polygon]
        
        # Separate the x and y coordinates for plotting
        xs, ys = zip(*pixel_coords)
        
        # Plot the polygon points and connect them to form the shape
        ax.plot(xs, ys, marker='o', markersize=5, linestyle='-', color='red', label='Polygon')
    
    plt.legend()
    plt.show()
