from flask import Flask, request, jsonify
import sys
import os

# Simple relative import since api is in the same directory as main.py
from api import document_processing, azure_integration

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Intelligent Document Insights Portal!"

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    # Check if a file is included in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
   
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Extract text from the uploaded PDF using a custom function
    pdf_text = document_processing.extract_text_from_pdf(file)

    # Analyze the extracted text using an Azure API (e.g., sentiment analysis)
    azure_endpoint = "https://<YOUR_REGION>.api.cognitive.microsoft.com/text/analytics/v3.0/sentiment"
    azure_key = "<YOUR_AZURE_TEXT_ANALYTICS_KEY>"
    analysis = azure_integration.analyze_text(pdf_text, azure_endpoint, azure_key)

    # Return the extracted text and Azure analysis result
    return jsonify({
        "extracted_text": pdf_text,
        "azure_analysis": analysis
    })

if __name__ == '__main__':
    app.run(debug=True)