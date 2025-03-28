import logging
import azure.functions as func
import json
import os
import datetime
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient

def main(req: func.HttpRequest, msg: func.Out[func.QueueMessage]) -> func.HttpResponse:
    """
    Azure Function to process documents
    Triggered by HTTP request, processes document with Form Recognizer,
    and stores results in Cosmos DB
    """
    logging.info('Document processing request received')
    
    try:
        # Get request body
        req_body = req.get_json()
        document_url = req_body.get('documentUrl')
        document_id = req_body.get('documentId')
        
        if not document_url or not document_id:
            return func.HttpResponse(
                "Please provide documentUrl and documentId in the request body",
                status_code=400
            )
        
        # Initialize Form Recognizer client
        form_recognizer_client = DocumentAnalysisClient(
            endpoint=os.environ["FORM_RECOGNIZER_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["FORM_RECOGNIZER_KEY"])
        )
        
        # Analyze document
        poller = form_recognizer_client.begin_analyze_document_from_url(
            "prebuilt-document", document_url
        )
        document_analysis = poller.result()
        
        # Extract key information
        document_text = " ".join([page.content for page in document_analysis.pages])
        key_phrases = extract_key_phrases(document_text)
        document_type = classify_document(document_analysis)
        
        # Store results in Cosmos DB
        save_to_cosmos_db(document_id, {
            "id": document_id,
            "url": document_url,
            "text": document_text[:1000],  # Store first 1000 chars as preview
            "keyPhrases": key_phrases,
            "documentType": document_type,
            "pageCount": len(document_analysis.pages),
            "processedDate": datetime.datetime.utcnow().isoformat()
        })
        
        # Queue message for further processing
        msg.set(json.dumps({
            "documentId": document_id,
            "status": "processed",
            "nextStep": "classification"
        }))
        
        return func.HttpResponse(
            json.dumps({
                "documentId": document_id,
                "status": "processed",
                "keyPhrases": key_phrases,
                "documentType": document_type,
                "pageCount": len(document_analysis.pages)
            }),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        return func.HttpResponse(
            f"Error processing document: {str(e)}",
            status_code=500
        )

def extract_key_phrases(text):
    """Extract key phrases from document text"""
    # This is a placeholder. In a real implementation, this would use
    # Azure Text Analytics or a similar service
    return ["sample phrase 1", "sample phrase 2"]

def classify_document(document_analysis):
    """Classify document type based on content and structure"""
    # This is a placeholder. In a real implementation, this would use
    # a custom classification model
    return "invoice"

def save_to_cosmos_db(document_id, document_data):
    """Save document data to Cosmos DB"""
    cosmos_client = CosmosClient(
        url=os.environ["COSMOS_ENDPOINT"],
        credential=os.environ["COSMOS_KEY"]
    )
    database = cosmos_client.get_database_client(os.environ["COSMOS_DATABASE"])
    container = database.get_container_client(os.environ["COSMOS_CONTAINER"])
    container.upsert_item(document_data) 