import rasterio
from rasterio.windows import Window
from typing import Tuple
from samgeo.fast_sam import SamGeo


def extract_patch(
    input_path: str,
    output_path: str,
    position: str = "top_left",  # Position options (use any one):
                                # "top_left"      - Starts from (0,0)
                                # "top_right"     - Starts from (width-patch_size, 0)
                                # "bottom_left"   - Starts from (0, height-patch_size)
                                # "bottom_right"  - Starts from (width-patch_size, height-patch_size)
                                # "center"        - Starts from ((width-patch_size)/2, (height-patch_size)/2)
    patch_size: int = 256       # Size options:
                               # 256 - for 256x256 pixel patch
                               # 512 - for 512x512 pixel patch
) -> Tuple[int, int]:
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
    # Validate patch size
    if patch_size not in [256, 512]:
        raise ValueError("Patch size must be either 256 or 512")
    
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


if __name__ == "__main__":
    # Example usage - modify these variables as needed
    INPUT_FILE = './images/FastSam_Sample_Image-2.tif'
    OUTPUT_FILE = './output/FastSam_output1.tif'
    
    # CHANGE THESE VALUES AS NEEDED:
    PATCH_SIZE = 256  # Options: 256 or 512
    
    # Position options (choose one):
    # "top_left"     - Extract from top left corner
    # "top_right"    - Extract from top right corner
    # "bottom_left"  - Extract from bottom left corner
    # "bottom_right" - Extract from bottom right corner
    # "center"       - Extract from center of image
    POSITION = "center" #bottom left did not work.
    
    try:
        # # Extract patch
        # x_pos, y_pos = extract_patch(
        #     input_path=INPUT_FILE,
        #     output_path=OUTPUT_FILE,
        #     position=POSITION,
        #     patch_size=PATCH_SIZE
        # )
        # print(f"Successfully extracted {PATCH_SIZE}x{PATCH_SIZE} patch from {POSITION}")
        # print(f"Patch starts at position ({x_pos}, {y_pos})")

        
        extract_patch(INPUT_FILE, OUTPUT_FILE,POSITION, PATCH_SIZE)

    
        
    except Exception as e:
        print(f"Error: {str(e)}")

sam = SamGeo(model="FastSAM-x.pt")

sam.set_image(OUTPUT_FILE)

output_path_after_sam = './output/preview_after_sam.tif'
sam.everything_prompt(output='./output/preview_after_sam_new.tif')