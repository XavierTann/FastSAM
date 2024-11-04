import math
import rasterio
from pyproj import Transformer
from samgeo.fast_sam import SamGeo


# Load the GeoTIFF file and convert geographic coordinates to pixel coordinates
geo_tiff_path = './images/FastSam_Sample_Image-2.tif'
transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

with rasterio.open(geo_tiff_path) as dataset:
    # Get image dimensions
    imagepxwidth = dataset.width
    imagepxheight = dataset.height
    # Get the affine transformation
    transform = dataset.transform
    # Calculate the image's bounding box in geographic coordinates
    minlon, maxlat = transform * (0, 0)  # Top-left corner
    maxlon, minlat = transform * (imagepxwidth, imagepxheight)  # Bottom-right corner

    # Convert coordinates to latitude and longitude (degrees)
    maxlat, minlon = transformer.transform(minlon, maxlat)
    minlat, maxlon = transformer.transform(maxlon, minlat)

    # Print the geographic bounding box for reference
    print(f"Image dimensions: Width={imagepxwidth} pixels, Height={imagepxheight} pixels")
    print(f"Top-left corner: Longitude={minlon}, Latitude={maxlat}")
    print(f"Bottom-right corner: Longitude={maxlon}, Latitude={minlat}")

def geographic_to_pixel(lat, lon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight):
    # Convert geographic coordinates to pixel coordinates
    x = math.floor(((lon - minlon) / (maxlon - minlon)) * imagepxwidth)
    y = math.floor(((maxlat - lat) / (maxlat - minlat)) * imagepxheight)
    return x, y

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

# Define the polygons from the console output
listOfPolygons = [
    [
        [25.742938617862812, -80.38361598162668],
        [25.742923507899654, -80.38202041998855],
        [25.74507875232093, -80.38208053195311],
        [25.745088910289628, -80.38372063809841],
        [25.742938617862812, -80.38361598162668]  # Closing the polygon
    ]
]


# Convert each polygon to a bounding box
bboxes = [polygon_to_bbox(polygon, minlat, maxlat, minlon, maxlon, imagepxwidth, imagepxheight) for polygon in listOfPolygons]
print(bboxes)
# Use the bounding boxes with the box_prompt function
sam = SamGeo(model="FastSAM-x.pt")
sam.set_image(geo_tiff_path)
output_image = './output/box_segmentation1.tif'
sam.box_prompt(bboxes=bboxes, output=output_image)
