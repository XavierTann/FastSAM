import requests
import os

# URL of the file (public link from Google Cloud Storage)
url = "https://storage.googleapis.com/raster-datasources/FastSam_Sample_Image-2.tif"

# Define the local output path
output_folder = "./output"
os.makedirs(output_folder, exist_ok=True)  # Create the folder if it doesn't exist

# Set the full path where the file will be saved
output_file_path = os.path.join(output_folder, "FastSam_Sample_Image-2.tif")

# Download the file from the public URL
response = requests.get(url)

# Save the file to the output folder
with open(output_file_path, "wb") as f:
    f.write(response.content)

print(f"File downloaded successfully to: {output_file_path}")
