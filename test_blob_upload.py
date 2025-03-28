import os
import logging
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_blob_upload")

def test_blob_upload():
    """Test blob upload functionality"""
    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_dotenv()
        
        # Get connection string and container name
        connection_string = os.getenv("STORAGE_CONNECTION_STRING")
        container_name = os.getenv("STORAGE_CONTAINER")
        
        if not connection_string or not container_name:
            logger.error("Missing required environment variables")
            logger.error(f"Connection string present: {bool(connection_string)}")
            logger.error(f"Container name present: {bool(container_name)}")
            return
        
        # Log connection details (without sensitive data)
        logger.info(f"Container name: {container_name}")
        logger.info(f"Connection string length: {len(connection_string)}")
        
        # Create blob service client
        logger.info("Creating blob service client...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        logger.info(f"Getting container client for: {container_name}")
        container_client = blob_service_client.get_container_client(container_name)
        
        # Test container access
        try:
            container_properties = container_client.get_container_properties()
            logger.info(f"Container {container_name} exists and is accessible")
            logger.info(f"Container last modified: {container_properties.last_modified}")
            logger.info(f"Container ETag: {container_properties.etag}")
        except Exception as e:
            logger.error(f"Container {container_name} is not accessible: {str(e)}")
            return
        
        # Create a test file
        test_file_path = "test_upload.txt"
        logger.info(f"Creating test file: {test_file_path}")
        with open(test_file_path, "w") as f:
            f.write("This is a test file for blob storage upload.")
        
        # Generate unique blob name
        blob_name = f"test_{os.urandom(8).hex()}.txt"
        logger.info(f"Generated blob name: {blob_name}")
        
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the file
        logger.info(f"Uploading file to blob storage as: {blob_name}")
        with open(test_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        logger.info("File uploaded successfully")
        
        # Verify the upload
        try:
            blob_properties = blob_client.get_blob_properties()
            logger.info(f"Blob exists and is accessible")
            logger.info(f"Blob size: {blob_properties.size} bytes")
            logger.info(f"Blob last modified: {blob_properties.last_modified}")
            logger.info(f"Blob ETag: {blob_properties.etag}")
        except Exception as e:
            logger.error(f"Failed to verify blob: {str(e)}")
        
        # Clean up test file
        os.remove(test_file_path)
        logger.info(f"Cleaned up test file: {test_file_path}")
        
        logger.info("=== Blob Upload Test Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error in test_blob_upload: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=== Blob Upload Test Failed ===")

if __name__ == "__main__":
    test_blob_upload() 