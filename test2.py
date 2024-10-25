import rasterio
from rasterio.mask import mask

geo_tiff_path = './images/FastSam_Sample_Image-2.tif'
input_geotiff = geo_tiff_path
output_geotiff = './output/preview.tif'

with rasterio.open(input_geotiff) as src:
    xmin, ymin, xmax, ymax = src.bounds
    print(xmin, ymin, xmax, ymax)
    # Get image dimensions
    x_range = xmax - xmin
    y_range = ymax-ymin

    xmin = xmin+(x_range / 3)
    ymin = ymin+(y_range/3)
    xmax = xmax - (x_range/3)
    ymax = ymax - (y_range/3)

    my_geojson = [{
        "type": "Polygon",
        "coordinates": [
            [
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax],
                [xmin, ymin]
            ],
        ]
    }]

    clipped, transform = mask(src, my_geojson, crop=True)

    imagepxwidth = src.width  # Image width in pixels
    imagepxheight = src.height  # Image height in pixels

    # Get the affine transformation (transform matrix) to relate pixel coordinates to geographic coordinates
    transform = src.transform

    profile = src.profile

    profile.update({
        'height': clipped.shape[1],
        'width': clipped.shape[2],
        'transform': transform,

    })

    # Write the cropped image to a new GeoTIFF
    with rasterio.open(output_geotiff, 'w', **profile) as dst:
        dst.write(clipped)
