#!/bin/bash

# This script sets up Azure resources for the Intelligent Document Insights Portal
# It requires the Azure CLI to be installed and authenticated

# Variables - change these as needed
RESOURCE_GROUP="document-insights-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="docinsightsstorage$RANDOM"
COSMOS_ACCOUNT="docinsightsdb$RANDOM"
FORM_RECOGNIZER="docinsights-form-recognizer"
TEXT_ANALYTICS="docinsights-text-analytics"
VISION_SERVICE="docinsights-vision"
SPEECH_SERVICE="docinsights-speech"
CONTENT_SAFETY="docinsights-content-safety"
APP_SERVICE_PLAN="docinsights-app-plan"
FUNCTION_APP="docinsights-functions"
APP_SERVICE="docinsights-app"

echo "Creating Azure resources for Intelligent Document Insights Portal..."

# Create Resource Group
echo "Creating Resource Group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Storage Account
echo "Creating Storage Account: $STORAGE_ACCOUNT"
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2 \
    --https-only true \
    --min-tls-version TLS1_2

# Get Storage Connection String
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString \
    --output tsv)

# Create Storage Container
echo "Creating Storage Container: documents"
az storage container create \
    --name documents \
    --connection-string "$STORAGE_CONNECTION_STRING"

# Create Cosmos DB Account
echo "Creating Cosmos DB Account: $COSMOS_ACCOUNT"
az cosmosdb create \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --locations regionName=$LOCATION \
    --default-consistency-level Session

# Create Cosmos DB Database
echo "Creating Cosmos DB Database: documentinsights"
az cosmosdb sql database create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --name documentinsights

# Create Cosmos DB Container
echo "Creating Cosmos DB Container: documents"
az cosmosdb sql container create \
    --account-name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --database-name documentinsights \
    --name documents \
    --partition-key-path "/id"

# Get Cosmos DB Endpoint and Key
COSMOS_ENDPOINT=$(az cosmosdb show \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query documentEndpoint \
    --output tsv)
    
COSMOS_KEY=$(az cosmosdb keys list \
    --name $COSMOS_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query primaryMasterKey \
    --output tsv)

# Create Form Recognizer
echo "Creating Form Recognizer: $FORM_RECOGNIZER"
az cognitiveservices account create \
    --name $FORM_RECOGNIZER \
    --resource-group $RESOURCE_GROUP \
    --kind FormRecognizer \
    --sku S0 \
    --location $LOCATION \
    --yes

# Get Form Recognizer Endpoint and Key
FORM_RECOGNIZER_ENDPOINT=$(az cognitiveservices account show \
    --name $FORM_RECOGNIZER \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)
    
FORM_RECOGNIZER_KEY=$(az cognitiveservices account keys list \
    --name $FORM_RECOGNIZER \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

# Create Text Analytics
echo "Creating Text Analytics: $TEXT_ANALYTICS"
az cognitiveservices account create \
    --name $TEXT_ANALYTICS \
    --resource-group $RESOURCE_GROUP \
    --kind TextAnalytics \
    --sku S0 \
    --location $LOCATION \
    --yes

# Get Text Analytics Endpoint and Key
TEXT_ANALYTICS_ENDPOINT=$(az cognitiveservices account show \
    --name $TEXT_ANALYTICS \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)
    
TEXT_ANALYTICS_KEY=$(az cognitiveservices account keys list \
    --name $TEXT_ANALYTICS \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

# Create Vision Service
echo "Creating Vision Service: $VISION_SERVICE"
az cognitiveservices account create \
    --name $VISION_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --kind ComputerVision \
    --sku S1 \
    --location $LOCATION \
    --yes

# Get Vision Service Endpoint and Key
VISION_ENDPOINT=$(az cognitiveservices account show \
    --name $VISION_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)
    
VISION_KEY=$(az cognitiveservices account keys list \
    --name $VISION_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

# Create Speech Service
echo "Creating Speech Service: $SPEECH_SERVICE"
az cognitiveservices account create \
    --name $SPEECH_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --kind SpeechServices \
    --sku S0 \
    --location $LOCATION \
    --yes

# Get Speech Service Key
SPEECH_KEY=$(az cognitiveservices account keys list \
    --name $SPEECH_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

# Create Content Safety Service
echo "Creating Content Safety Service: $CONTENT_SAFETY"
az cognitiveservices account create \
    --name $CONTENT_SAFETY \
    --resource-group $RESOURCE_GROUP \
    --kind ContentSafety \
    --sku S0 \
    --location $LOCATION \
    --yes

# Get Content Safety Endpoint and Key
CONTENT_SAFETY_ENDPOINT=$(az cognitiveservices account show \
    --name $CONTENT_SAFETY \
    --resource-group $RESOURCE_GROUP \
    --query properties.endpoint \
    --output tsv)
    
CONTENT_SAFETY_KEY=$(az cognitiveservices account keys list \
    --name $CONTENT_SAFETY \
    --resource-group $RESOURCE_GROUP \
    --query key1 \
    --output tsv)

# Create App Service Plan
echo "Creating App Service Plan: $APP_SERVICE_PLAN"
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1

# Create Function App
echo "Creating Function App: $FUNCTION_APP"
az functionapp create \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --storage-account $STORAGE_ACCOUNT \
    --plan $APP_SERVICE_PLAN \
    --runtime python \
    --runtime-version 3.9 \
    --functions-version 4

# Create Web App
echo "Creating Web App: $APP_SERVICE"
az webapp create \
    --name $APP_SERVICE \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON|3.9"

# Create .env file with configuration values
echo "Creating .env file with configuration values"
cat > .env << EOF
# Azure Vision API
VISION_ENDPOINT=$VISION_ENDPOINT
VISION_KEY=$VISION_KEY

# Azure Form Recognizer
FORM_RECOGNIZER_ENDPOINT=$FORM_RECOGNIZER_ENDPOINT
FORM_RECOGNIZER_KEY=$FORM_RECOGNIZER_KEY

# Azure Text Analytics
TEXT_ANALYTICS_ENDPOINT=$TEXT_ANALYTICS_ENDPOINT
TEXT_ANALYTICS_KEY=$TEXT_ANALYTICS_KEY

# Azure Speech Services
SPEECH_KEY=$SPEECH_KEY
SPEECH_REGION=$LOCATION

# Azure Content Safety
CONTENT_SAFETY_ENDPOINT=$CONTENT_SAFETY_ENDPOINT
CONTENT_SAFETY_KEY=$CONTENT_SAFETY_KEY

# Azure Storage
STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION_STRING
STORAGE_CONTAINER=documents

# Azure Cosmos DB
COSMOS_ENDPOINT=$COSMOS_ENDPOINT
COSMOS_KEY=$COSMOS_KEY
COSMOS_DATABASE=documentinsights
COSMOS_CONTAINER=documents

# Application Settings
DEBUG=True
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
EOF

echo "Azure resources created successfully!"
echo "Configuration has been saved to .env file"
echo ""
echo "Next steps:"
echo "1. Copy the .env file to your project root directory"
echo "2. Install required Python packages: pip install -r requirements.txt"
echo "3. Start the application: python app.py" 