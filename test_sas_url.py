import os
import logging
import requests
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_sas_url")

def generate_sas_url(blob_client, container_name, account_name):
    """Generate a SAS URL for blob access"""
    try:
        # Get blob name
        blob_name = blob_client.blob_name
        logger.info(f"Generating SAS URL for blob: {blob_name}")
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
            start=datetime.utcnow() - timedelta(minutes=5)
        )
        
        # Construct SAS URL
        sas_url = f"{blob_client.url}?{sas_token}"
        logger.info(f"Generated SAS URL successfully")
        logger.info(f"SAS URL length: {len(sas_url)}")
        logger.info(f"SAS URL starts with: {sas_url[:50]}...")
        
        return sas_url
    except Exception as e:
        logger.error(f"Error generating SAS URL: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def test_sas_url():
    """Test SAS URL generation and access"""
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
        
        # Parse connection string to get account name
        connection_string_parts = dict(part.split('=', 1) for part in connection_string.split(';'))
        account_name = connection_string_parts.get('AccountName')
        account_key = connection_string_parts.get('AccountKey')
        
        if not account_name or not account_key:
            logger.error("Missing account name or key in connection string")
            return
        
        logger.info(f"Storage account: {account_name}")
        logger.info(f"Container name: {container_name}")
        
        # Create blob service client
        logger.info("Creating blob service client...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        logger.info(f"Getting container client for: {container_name}")
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create a test file
        test_file_path = "test_sas.txt"
        logger.info(f"Creating test file: {test_file_path}")
        with open(test_file_path, "w") as f:
            f.write("This is a test file for SAS URL generation.")
        
        # Generate unique blob name
        blob_name = f"test_sas_{os.urandom(8).hex()}.txt"
        logger.info(f"Generated blob name: {blob_name}")
        
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the file
        logger.info(f"Uploading file to blob storage as: {blob_name}")
        with open(test_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        logger.info("File uploaded successfully")
        
        # Generate SAS URL
        logger.info("=== Generating SAS URL ===")
        sas_url = generate_sas_url(blob_client, container_name, account_name)
        
        # Test SAS URL access
        logger.info("=== Testing SAS URL Access ===")
        try:
            response = requests.get(sas_url)
            response.raise_for_status()
            logger.info(f"SAS URL is accessible. Status code: {response.status_code}")
            logger.info(f"Response content: {response.text}")
            logger.info(f"Response headers: {dict(response.headers)}")
        except Exception as e:
            logger.error(f"Failed to access SAS URL: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Clean up test file
        os.remove(test_file_path)
        logger.info(f"Cleaned up test file: {test_file_path}")
        
        logger.info("=== SAS URL Test Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error in test_sas_url: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=== SAS URL Test Failed ===")

if __name__ == "__main__":
    test_sas_url() 