# Intelligent Document Insights Portal

A powerful document analysis system powered by Azure AI services that helps organizations extract valuable insights from their documents. This system processes various document types (PDF, Word, text, images), analyzes them using advanced AI, and presents results in an intuitive dashboard.

## Features

- **Document Recognition**: Extract text, tables, key-value pairs, and entities from documents
- **Asynchronous Processing**: Background processing of documents without blocking user operations
- **Multi-format Support**: Process PDF, Word, text, and image documents
- **Comprehensive Dashboard**: Visual representation of document insights
- **Easy Navigation**: User-friendly interface to upload and view analyzed documents
- **Secure Authentication**: User authentication to protect sensitive data
- **Real-time Status**: Track processing status of all documents

## System Architecture

### Backend Components
- **FastAPI Backend**: Handles API requests and document processing workflows
- **Flask Frontend**: User interface for document uploading and result viewing
- **Azure AI Integration**: Leverages Azure Form Recognizer for document analysis
- **Thread-based Processing**: Asynchronous document handling for optimal performance

### Azure Services Integration
- **Azure Form Recognizer**: Advanced document analysis service for extracting text and data
- **Azure Blob Storage**: Secure storage for uploaded documents
- **Azure Cosmos DB**: Database for storing analysis results

## Installation

### Prerequisites
- Python 3.8 or higher
- Azure subscription with the following services:
  - Azure Form Recognizer
  - Azure Blob Storage
  - Azure Cosmos DB
  - Azure Content Safety
  - Azure Text Analytics

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/your-username/intelligent-document-insights-portal.git
cd intelligent-document-insights-portal
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Configure environment variables by creating a `.env` file:
```
FORM_RECOGNIZER_ENDPOINT=https://your-form-recognizer.cognitiveservices.azure.com/
FORM_RECOGNIZER_KEY=your-form-recognizer-key
STORAGE_CONNECTION_STRING=your-storage-connection-string
STORAGE_CONTAINER=documents
COSMOS_ENDPOINT=https://your-cosmos-db.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
COSMOS_DATABASE=documentinsights
COSMOS_CONTAINER=documents
TEXT_ANALYTICS_ENDPOINT=https://your-text-analytics.cognitiveservices.azure.com/
TEXT_ANALYTICS_KEY=your-text-analytics-key
SPEECH_KEY=your-speech-key
SPEECH_REGION=your-speech-region
CONTENT_SAFETY_ENDPOINT=https://your-content-safety.cognitiveservices.azure.com/
CONTENT_SAFETY_KEY=your-content-safety-key
DOCUMENT_TRANSLATION_ENDPOINT=https://your-translator.cognitiveservices.azure.com/
DOCUMENT_TRANSLATION_KEY=your-document-translation-key
```

5. Run the application:
```bash
python app.py
```

6. Access the application in your browser at:
```
http://localhost:5000
```

## Usage Guide

### Uploading Documents
1. Log in to the portal using your credentials
2. Navigate to the dashboard
3. Click on the "Process Document" button
4. Select a document from your computer
5. Wait for the analysis to complete (processing happens in the background)

### Viewing Results
1. Once processing is complete, documents appear in the "Recent Documents" section
2. Click "View Details" to see the comprehensive analysis
3. Explore extracted text, tables, key-value pairs, and entities

### Document Details Page
The document details page provides:
- Extracted page content
- Recognized tables with structure preserved
- Key-value pairs extracted from forms
- Named entities detected in the document
- Raw JSON data for developer use

## Development

### Project Structure
```
intelligent-document-insights-portal/
├── ai_services/
│   └── multimodal_processor.py  # Core AI processing logic
├── static/
│   ├── css/
│   │   └── style.css            # Styling for the application
│   └── images/                  # Image assets
├── templates/
│   ├── index.html               # Dashboard template
│   ├── login.html               # Login page
│   ├── document_details.html    # Document analysis view
│   └── forgot_password.html     # Password recovery
├── app.py                       # Main application file
├── requirements.txt             # Dependencies
└── .env                         # Environment variables (not in repo)
```

### Key Components
- **MultiModalAIProcessor**: Core class handling AI service integration
- **process_document**: Main method for analyzing documents
- **ThreadPoolExecutor**: Handles background processing
- **Flask routes**: Handle UI interaction
- **FastAPI endpoints**: Provide API functionality

## Technologies Used

- **Python**: Primary programming language
- **Flask**: Web framework for the frontend
- **FastAPI**: API framework for the backend
- **Azure AI Services**: Document intelligence capabilities
- **ThreadPoolExecutor**: Concurrent processing
- **asyncio**: Asynchronous operations
- **Jinja2**: Templating engine for HTML

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- Azure AI services for document intelligence capabilities
- FastAPI and Flask for web framework functionality
- All contributors who have helped shape this project
