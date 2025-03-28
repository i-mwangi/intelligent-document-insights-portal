import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from pathlib import Path
from azure.storage.blob import BlobServiceClient
import time
import azure.core.exceptions
import sys
import fastapi
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from ai_services.multimodal_processor import MultiModalAIProcessor

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Constants for file validation
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    # Additional document types
    ".rtf": "application/rtf",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
}

# Load environment variables from the correct path
env_path = Path(__file__).parent / '.env'
logger.info(f"Loading environment variables from: {env_path}")
logger.info(f"File exists: {env_path.exists()}")

# Load environment variables
with open(env_path) as f:
    env_vars = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
            except ValueError:
                continue

# Log the environment variables being used (without sensitive values)
logger.info("Loading configuration from environment variables...")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Environment file path: {env_path.absolute()}")
logger.info(f"Form Recognizer Endpoint: {env_vars.get('FORM_RECOGNIZER_ENDPOINT')}")
logger.info(f"Form Recognizer Key length: {len(env_vars.get('FORM_RECOGNIZER_KEY', ''))}")
logger.info(f"Storage Connection String length: {len(env_vars.get('STORAGE_CONNECTION_STRING', ''))}")
logger.info(f"Environment variables loaded from: {os.getcwd()}")

# Initialize the FastAPI app
app = FastAPI(
    title="Intelligent Document Insights Portal",
    description="A multi-modal document analysis platform powered by Azure AI services",
    version="1.0.0",
)

# Create a separate Flask app for frontend
flask_app = Flask(__name__, 
                 static_folder='static',
                 template_folder='templates')
flask_app.secret_key = "my_secret_key_for_session_management"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize Azure clients
config = {
    "VISION_ENDPOINT": env_vars.get("VISION_ENDPOINT", ""),
    "VISION_KEY": env_vars.get("VISION_KEY", ""),
    "FORM_RECOGNIZER_ENDPOINT": env_vars.get("FORM_RECOGNIZER_ENDPOINT", ""),
    "FORM_RECOGNIZER_KEY": env_vars.get("FORM_RECOGNIZER_KEY", ""),
    "TEXT_ANALYTICS_ENDPOINT": env_vars.get("TEXT_ANALYTICS_ENDPOINT", ""),
    "TEXT_ANALYTICS_KEY": env_vars.get("TEXT_ANALYTICS_KEY", ""),
    "SPEECH_KEY": env_vars.get("SPEECH_KEY", ""),
    "SPEECH_REGION": env_vars.get("SPEECH_REGION", ""),
    "CONTENT_SAFETY_ENDPOINT": env_vars.get("CONTENT_SAFETY_ENDPOINT", ""),
    "CONTENT_SAFETY_KEY": env_vars.get("CONTENT_SAFETY_KEY", ""),
    "DOCUMENT_TRANSLATION_ENDPOINT": env_vars.get("DOCUMENT_TRANSLATION_ENDPOINT", ""),
    "DOCUMENT_TRANSLATION_KEY": env_vars.get("DOCUMENT_TRANSLATION_KEY", ""),
    "STORAGE_CONNECTION_STRING": env_vars.get("STORAGE_CONNECTION_STRING", ""),
    "STORAGE_CONTAINER": env_vars.get("STORAGE_CONTAINER", ""),
    "COSMOS_ENDPOINT": env_vars.get("COSMOS_ENDPOINT", ""),
    "COSMOS_KEY": env_vars.get("COSMOS_KEY", ""),
    "COSMOS_DATABASE": env_vars.get("COSMOS_DATABASE", ""),
    "COSMOS_CONTAINER": env_vars.get("COSMOS_CONTAINER", "")
}

# Log Azure services configuration
logger.info("Azure Services Configuration:")
logger.info(f"Storage Account: {config['STORAGE_CONNECTION_STRING'].split(';')[0].split('=')[1]}")
logger.info(f"Storage Container: {config['STORAGE_CONTAINER']}")
logger.info(f"Cosmos DB Endpoint: {config['COSMOS_ENDPOINT']}")
logger.info(f"Cosmos DB Database: {config['COSMOS_DATABASE']}")
logger.info(f"Cosmos DB Container: {config['COSMOS_CONTAINER']}")
logger.info(f"Form Recognizer Endpoint: {config['FORM_RECOGNIZER_ENDPOINT']}")
logger.info(f"Text Analytics Endpoint: {config['TEXT_ANALYTICS_ENDPOINT']}")
logger.info(f"Speech Region: {config['SPEECH_REGION']}")
logger.info(f"Content Safety Endpoint: {config['CONTENT_SAFETY_ENDPOINT']}")
logger.info(f"Document Translation Endpoint: {config['DOCUMENT_TRANSLATION_ENDPOINT']}")

# Initialize Azure Storage client and verify container
try:
    logger.info("Initializing Azure Storage client...")
    blob_service_client = BlobServiceClient.from_connection_string(config["STORAGE_CONNECTION_STRING"])
    container_client = blob_service_client.get_container_client(config["STORAGE_CONTAINER"])
    
    # Verify container exists and is accessible
    try:
        container_properties = container_client.get_container_properties()
        logger.info(f"Container {config['STORAGE_CONTAINER']} exists and is accessible")
        logger.info(f"Container last modified: {container_properties.last_modified}")
        logger.info(f"Container ETag: {container_properties.etag}")
    except azure.core.exceptions.ResourceNotFoundError:
        logger.warning(f"Container {config['STORAGE_CONTAINER']} not found, creating it...")
        container_client = blob_service_client.create_container(config["STORAGE_CONTAINER"])
        logger.info(f"Container {config['STORAGE_CONTAINER']} created successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize Azure Storage: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

# Initialize AI processor
ai_processor = MultiModalAIProcessor(config)

# Validate required configurations
if not config["FORM_RECOGNIZER_ENDPOINT"] or "your-form-recognizer" in config["FORM_RECOGNIZER_ENDPOINT"]:
    raise ValueError("Form Recognizer endpoint is using placeholder URL. Please update the .env file with the correct endpoint.")

if not config["FORM_RECOGNIZER_KEY"] or len(config["FORM_RECOGNIZER_KEY"]) < 32:
    raise ValueError("Form Recognizer key is invalid or missing. Please check your .env file.")

# Log the configuration being passed to MultiModalAIProcessor
logger.info("Configuration being passed to MultiModalAIProcessor:")
logger.info(f"Form Recognizer Endpoint: {config['FORM_RECOGNIZER_ENDPOINT']}")
logger.info(f"Form Recognizer Key length: {len(config['FORM_RECOGNIZER_KEY'])}")
logger.info(f"Storage Connection String length: {len(config['STORAGE_CONNECTION_STRING'])}")
logger.info(f"Storage Container: {config['STORAGE_CONTAINER']}")

# Dependency to get AI processor
async def get_ai_processor():
    return MultiModalAIProcessor(config)

# Request models
class DocumentRequest(BaseModel):
    document_url: Optional[str] = None
    image_url: Optional[str] = None
    audio_file_path: Optional[str] = None
    target_language: Optional[str] = None

# Add status tracking
processing_status = {}

# Login required decorator for Flask
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.get("/")
@login_required
async def root():
    return {"message": "Welcome to Intelligent Document Insights Portal API"}

@app.post("/api/analyze/document")
async def analyze_document(
    request: DocumentRequest,
    ai_processor: MultiModalAIProcessor = Depends(get_ai_processor)
):
    """Analyze a document from a URL"""
    try:
        result = await ai_processor.process_document(request.document_url)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/image")
async def analyze_image(
    request: DocumentRequest,
    ai_processor: MultiModalAIProcessor = Depends(get_ai_processor)
):
    """Analyze an image from a URL"""
    try:
        result = await ai_processor.process_image(request.image_url)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/multimodal")
async def analyze_multimodal(
    request: DocumentRequest,
    ai_processor: MultiModalAIProcessor = Depends(get_ai_processor)
):
    """Process multi-modal content including documents, images, audio, and video"""
    try:
        # Process content based on provided URLs
        content = {
            "document_url": request.document_url,
            "image_url": request.image_url,
            "audio_file_path": request.audio_file_path
        }
        
        # Start processing in background
        ai_processor.process_multimodal_content(content)
        
        return {"message": "Processing started successfully"}
        
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    ai_processor: MultiModalAIProcessor = Depends(get_ai_processor)
):
    """Upload and analyze a document synchronously"""
    temp_file_path = None
    try:
        logger.info("=== Starting Synchronous Document Upload Process ===")
        logger.info(f"Received file upload request for: {file.filename}")
        logger.info(f"Content type: {file.content_type}")
        
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        logger.info(f"File extension: {file_extension}")
        
        if file_extension not in ALLOWED_EXTENSIONS:
            logger.error(f"Invalid file type: {file_extension}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        
        # Validate content type
        if file.content_type not in ALLOWED_EXTENSIONS.values():
            logger.error(f"Invalid content type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type. Allowed types: {', '.join(ALLOWED_EXTENSIONS.values())}"
            )
        
        # Validate file size
        content = await file.read()
        file_size = len(content)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            logger.error(f"File size exceeds limit: {file_size} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds the {MAX_FILE_SIZE / (1024 * 1024)}MB limit"
            )
        
        if file_size == 0:
            logger.error("Empty file received")
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )
        
        # Save the file temporarily
        temp_file_path = f"temp_{file.filename}"
        logger.info(f"Saving file temporarily: {temp_file_path}")
        
        try:
            with open(temp_file_path, "wb") as f:
                f.write(content)
                logger.info(f"File saved successfully. Size: {file_size} bytes")
        except Exception as e:
            logger.error(f"Error saving temporary file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save temporary file: {str(e)}"
            )
        
        # Upload to blob storage and get URL
        logger.info("=== Starting Blob Storage Upload ===")
        try:
            blob_service_client = BlobServiceClient.from_connection_string(config["STORAGE_CONNECTION_STRING"])
            container_client = blob_service_client.get_container_client(config["STORAGE_CONTAINER"])
            
            blob_name = f"{os.urandom(8).hex()}_{file.filename}"
            logger.info(f"Generated blob name: {blob_name}")
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload the file
            logger.info(f"Uploading file to blob storage as: {blob_name}")
            try:
                with open(temp_file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                    logger.info("File uploaded successfully to blob storage")
            except Exception as upload_error:
                logger.error(f"Error during blob upload: {str(upload_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file to blob storage: {str(upload_error)}"
                )
            
            # Generate SAS URL for Form Recognizer access
            logger.info("=== Generating SAS URL ===")
            try:
                sas_url = ai_processor._generate_sas_url(blob_client)
                logger.info("Generated SAS URL successfully")
            except Exception as sas_error:
                logger.error(f"Error generating SAS URL: {str(sas_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate SAS URL: {str(sas_error)}"
                )
            
        except Exception as e:
            logger.error(f"Error in blob storage operations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process file in blob storage: {str(e)}"
            )
        
        # Process document synchronously
        logger.info("=== Starting Document Processing ===")
        try:
            start_time = time.time()
            result = await ai_processor.process_document(sas_url)
            end_time = time.time()
            
            processing_time = end_time - start_time
            logger.info(f"Document processing completed in {processing_time:.2f} seconds")
            
            return {
                "message": "File processed successfully",
                "result": result,
                "status": "completed",
                "processing_time": f"{processing_time:.2f} seconds",
                "file_info": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": file_size,
                    "extension": file_extension
                }
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in upload_document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")
        logger.info("=== Document Upload Process Completed ===")

@app.post("/api/translate")
async def translate_document(request: DocumentRequest):
    """Translate a document to the target language"""
    try:
        if not request.document_url or not request.target_language:
            raise HTTPException(status_code=400, detail="Document URL and target language are required")
            
        translated_url = await ai_processor.translate_document(
            request.document_url,
            request.target_language
        )
        
        return {"translated_url": translated_url}
        
    except Exception as e:
        logger.error(f"Error translating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{job_id}")
async def get_processing_status(job_id: str):
    """Get the status of a processing job"""
    try:
        if job_id not in processing_status:
            raise HTTPException(status_code=404, detail="Job not found")
            
        status = processing_status[job_id]
        
        # Clean up completed or failed jobs after 1 hour
        if status["status"] in ["completed", "failed"]:
            if time.time() - status["start_time"] > 3600:
                del processing_status[job_id]
                
        return status
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add cleanup task for old status entries
@app.on_event("startup")
async def startup_event():
    """Clean up old status entries on startup"""
    current_time = time.time()
    for job_id in list(processing_status.keys()):
        if current_time - processing_status[job_id]["start_time"] > 3600:
            del processing_status[job_id]

# Mount static files for frontend
app.mount("/", StaticFiles(directory="client/build", html=True), name="static")

# Add a catch-all route to serve React app
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Serve React app for all other routes"""
    try:
        return FileResponse("client/build/index.html")
    except Exception as e:
        logger.error(f"Error serving React app: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving frontend application")

# Sample user credentials (in a real app, these would be in a database)
SAMPLE_USERS = {
    "admin@example.com": "password"
}

# Store processed document results (in a real app, these would be in a database)
PROCESSED_DOCUMENTS = {}

@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check against our sample users
        if email in SAMPLE_USERS and SAMPLE_USERS[email] == password:
            session['user_id'] = email
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html', now=datetime.now())

@flask_app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

@flask_app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html', now=datetime.now())

@flask_app.route('/')
@login_required
def index():
    """Display landing page with list of processed documents"""
    return render_template('index.html', documents=PROCESSED_DOCUMENTS, now=datetime.now())

@flask_app.route('/api/upload/document', methods=['POST'])
def flask_upload_document():
    """Upload and analyze a document via Flask"""
    try:
        logger.info("=== Starting Flask Document Upload Process ===")
        
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to upload documents', 'error')
            return redirect(url_for('login'))
        
        # Check if file is present in request
        if 'file' not in request.files:
            flash('No file provided', 'error')
            return redirect(url_for('index'))
            
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
            
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        logger.info(f"File extension: {file_extension}")
        
        if file_extension not in ALLOWED_EXTENSIONS:
            flash(f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}", 'error')
            return redirect(url_for('index'))
        
        # Validate content type
        if file.content_type not in ALLOWED_EXTENSIONS.values():
            flash(f"Invalid content type: {file.content_type}", 'error')
            return redirect(url_for('index'))
        
        # Save the file temporarily
        temp_file_path = os.path.join(os.getcwd(), f"temp_{file.filename}")
        logger.info(f"Saving file temporarily: {temp_file_path}")
        file.save(temp_file_path)
        
        # Process the file with AI - upload to blob storage
        try:
            logger.info("=== Starting Blob Storage Upload from Flask ===")
            blob_service_client = BlobServiceClient.from_connection_string(config["STORAGE_CONNECTION_STRING"])
            container_client = blob_service_client.get_container_client(config["STORAGE_CONTAINER"])
            
            blob_name = f"{os.urandom(8).hex()}_{file.filename}"
            logger.info(f"Generated blob name: {blob_name}")
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload the file
            with open(temp_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                logger.info("File uploaded successfully to blob storage from Flask")
            
            # Generate SAS URL for Form Recognizer access
            logger.info("=== Generating SAS URL from Flask ===")
            sas_url = ai_processor._generate_sas_url(blob_client)
            logger.info("Generated SAS URL successfully from Flask")
            
            # Create a function to process the document in a separate thread
            def process_document_thread(url, file_path):
                try:
                    logger.info(f"=== Starting Document Processing in Thread for {file_path} ===")
                    # Create an event loop for the thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Create a new instance of the processor for this thread
                    thread_processor = MultiModalAIProcessor(config)
                    
                    # Run the document processing in the event loop
                    result = loop.run_until_complete(thread_processor.process_document(url))
                    
                    # Log the result
                    logger.info(f"Document processing completed for {file_path}")
                    logger.info(f"Processing result: {result}")
                    
                    # Store the result in PROCESSED_DOCUMENTS
                    document_id = os.path.basename(file_path).replace('temp_', '')
                    PROCESSED_DOCUMENTS[document_id] = {
                        'id': document_id,
                        'filename': document_id,
                        'result': result,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'completed'
                    }
                    logger.info(f"Document result stored with ID: {document_id}")
                    
                    # Clean up
                    loop.close()
                except Exception as e:
                    logger.error(f"Error processing document in thread: {str(e)}")
                    # Store the error information
                    document_id = os.path.basename(file_path).replace('temp_', '')
                    PROCESSED_DOCUMENTS[document_id] = {
                        'id': document_id,
                        'filename': document_id,
                        'error': str(e),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'failed'
                    }
                finally:
                    # Clean up temporary file
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"Cleaned up temporary file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error cleaning up temporary file: {str(e)}")
            
            # Start processing in a separate thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(process_document_thread, sas_url, temp_file_path)
            
            flash('File uploaded successfully! Processing has started. Please check back later for results.', 'success')
            return redirect(url_for('index'))
            
        except Exception as processing_error:
            logger.error(f"Error processing document: {str(processing_error)}")
            flash(f"Error processing document: {str(processing_error)}", 'error')
            return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error in Flask upload: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('index'))

# Error handlers for Flask app
@flask_app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found", now=datetime.now()), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error", now=datetime.now()), 500

@flask_app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message="Access forbidden", now=datetime.now()), 403

@flask_app.route('/documents')
@login_required
def documents_list():
    """Display list of processed documents"""
    return render_template('documents.html', documents=PROCESSED_DOCUMENTS, now=datetime.now())

@flask_app.route('/documents/<document_id>')
@login_required
def document_details(document_id):
    """Display details of a processed document"""
    if document_id not in PROCESSED_DOCUMENTS:
        flash('Document not found', 'error')
        return redirect(url_for('documents_list'))
    
    document = PROCESSED_DOCUMENTS[document_id]
    return render_template('document_details.html', document=document, now=datetime.now())

@flask_app.route('/api/documents')
@login_required
def api_documents_list():
    """API endpoint to get list of documents as JSON"""
    return jsonify(list(PROCESSED_DOCUMENTS.values()))

@flask_app.route('/api/documents/<document_id>')
@login_required
def api_document_details(document_id):
    """API endpoint to get document details as JSON"""
    if document_id not in PROCESSED_DOCUMENTS:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify(PROCESSED_DOCUMENTS[document_id])

if __name__ == "__main__":
    # Check which server to run based on command line argument
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # Run the FastAPI application for backend
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
    else:
        # Run the Flask application for frontend
        flask_app.run(host="0.0.0.0", port=5000, debug=True) 