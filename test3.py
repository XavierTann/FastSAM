import rasterio
from rasterio.windows import Window
from rasterio.windows import from_bounds

geo_tiff_path = './images/FastSam_Sample_Image-2.tif'
input_geotiff = geo_tiff_path
output_geotiff = './output/preview.tif'

with rasterio.open(input_geotiff) as src:
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
