import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
print(f"Current working directory: {os.getcwd()}")
print(f"Looking for .env file...")

# Read .env file directly
env_path = os.path.join(os.getcwd(), '.env')
env_vars = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
            except ValueError:
                continue

# Get storage connection string and container name
connection_string = env_vars.get("STORAGE_CONNECTION_STRING")
container_name = env_vars.get("STORAGE_CONTAINER")

print(f"Testing storage connection...")
print(f"Container name: {container_name}")
print(f"Connection string length: {len(connection_string) if connection_string else 0}")
print(f"First 50 chars of connection string: {connection_string[:50] if connection_string else 'None'}")

try:
    # Create blob service client
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Test connection by listing containers
    containers = list(blob_service_client.list_containers())
    print("Successfully connected to storage account!")
    
    # Check if container exists
    container_client = blob_service_client.get_container_client(container_name)
    if container_client.exists():
        print(f"Container '{container_name}' exists!")
    else:
        print(f"Container '{container_name}' does not exist. Creating it...")
        container_client.create_container()
        print("Container created successfully!")
        
except Exception as e:
    print(f"Error: {str(e)}")
    if "ResourceNotFound" in str(e):
        print("\nPossible issues:")
        print("1. The storage account does not exist")
        print("2. The storage account name is incorrect")
        print("3. The connection string is invalid")
    elif "AuthenticationFailed" in str(e):
        print("\nPossible issues:")
        print("1. The storage account key is incorrect")
        print("2. The storage account key has been regenerated")
        print("3. The connection string is not properly formatted") 