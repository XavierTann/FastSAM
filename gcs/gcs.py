import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Google Cloud service account JSON from the environment
GOOGLE_CLOUD_SERVICE_ACCOUNT = os.getenv("GOOGLE_CLOUD_SERVICE_ACCOUNT")

# Function to load Google Cloud credentials from environment
def get_google_credentials(credentials_json_string):
    if not credentials_json_string:
        raise ValueError("Missing Google Cloud service account credentials")

    # Parse the JSON string into a dictionary
    credentials_dict = json.loads(credentials_json_string)
    return service_account.Credentials.from_service_account_info(credentials_dict)

# Authenticate using the service account JSON from environment variable
credentials = get_google_credentials(GOOGLE_CLOUD_SERVICE_ACCOUNT)

# Initialize the GCS client with the authenticated credentials
storage_client = storage.Client(credentials=credentials)

# Function to download a file from GCS
def download_gcs_file(bucket_name, blob_name, destination_file_path):
    try:
        # Get the bucket
        bucket = storage_client.get_bucket(bucket_name)
        
        # Get the blob (file) from the bucket
        blob = bucket.blob(blob_name)
        
        # Download the blob to the specified local path
        blob.download_to_filename(destination_file_path)
        
        print(f"Downloaded {blob_name} from bucket {bucket_name} to {destination_file_path}")
    except Exception as e:
        print(f"Error downloading file: {e}")

# Example usage
if __name__ == "__main__":
    # Define your bucket name, blob name, and local destination file path
    bucket_name = 'your-bucket-name'  # Replace with your bucket name
    blob_name = 'path/to/your/file/in/gcs'  # Replace with the file path in GCS
    destination_file_path = 'local/path/for/downloaded/file'  # Local path to save the file
    
    # Call the function to download the file
    download_gcs_file(bucket_name, blob_name, destination_file_path)
