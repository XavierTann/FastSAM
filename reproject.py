import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

def reproject_to_4326(input_path, output_path):
    """
    Reproject a raster file to EPSG:4326 (WGS84)
    
    Parameters:
    input_path (str): Path to input raster file
    output_path (str): Path to save the reprojected raster
    """
    # Open the input raster
    with rasterio.open(input_path) as src:
        # Calculate the transform and dimensions for the new projection
        transform, width, height = calculate_default_transform(
            src.crs,                    # Source CRS
            'EPSG:4326',               # Destination CRS
            src.width,                 # Source width
            src.height,                # Source height
            *src.bounds                # Source bounds
        )
        
        # Set up the keyword arguments for the output raster
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': 'EPSG:4326',
            'transform': transform,
            'width': width,
            'height': height
        })
        
        # Create the output raster
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            # Reproject each band
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs='EPSG:4326',
                    resampling=Resampling.bilinear
                )

# Example usage
input_file = './images/FastSam_Sample_Image-2.tif'
output_file = './output/FastSam_output1.tif'
reproject_to_4326(input_file, output_file)