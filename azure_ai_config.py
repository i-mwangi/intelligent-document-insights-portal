from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

class AzureAIServices:
    def __init__(self):
        # Initialize Azure AI services clients
        self.vision_client = ComputerVisionClient(
            endpoint="YOUR_VISION_ENDPOINT",
            credential=AzureKeyCredential("YOUR_VISION_KEY")
        )
        
        self.speech_config = SpeechConfig(
            subscription="YOUR_SPEECH_KEY",
            region="YOUR_SPEECH_REGION"
        )
        
        self.text_analytics_client = TextAnalyticsClient(
            endpoint="YOUR_TEXT_ANALYTICS_ENDPOINT",
            credential=AzureKeyCredential("YOUR_TEXT_ANALYTICS_KEY")
        )
        
        self.form_recognizer_client = DocumentAnalysisClient(
            endpoint="YOUR_FORM_RECOGNIZER_ENDPOINT",
            credential=AzureKeyCredential("YOUR_FORM_RECOGNIZER_KEY")
        )
    
    async def analyze_image(self, image_url):
        """Analyze image using Azure Computer Vision"""
        result = await self.vision_client.analyze_image_async(
            image_url,
            visual_features=["Categories", "Description", "Tags", "Objects", "Faces"]
        )
        return result
    
    async def transcribe_audio(self, audio_file):
        """Transcribe audio using Azure Speech Services"""
        speech_recognizer = SpeechRecognizer(speech_config=self.speech_config)
        result = await speech_recognizer.recognize_once_async()
        return result.text
    
    async def analyze_text(self, text):
        """Analyze text using Azure Language Services"""
        result = await self.text_analytics_client.analyze_sentiment(
            documents=[text]
        )
        return result[0]
    
    async def analyze_document(self, document_url):
        """Analyze document using Azure Form Recognizer"""
        poller = await self.form_recognizer_client.begin_analyze_document(
            "prebuilt-document",
            document_url
        )
        result = await poller.result()
        return result 