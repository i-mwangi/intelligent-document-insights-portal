import os
import asyncio
import logging
import tempfile
from typing import Dict, List, Any, Optional
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from azure.ai.formrecognizer.aio import DocumentAnalysisClient
from azure.ai.textanalytics import TextAnalyticsClient, RecognizeEntitiesAction, AbstractiveSummaryAction
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.translation.document import DocumentTranslationClient
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig
from azure.cognitiveservices.speech.audio import AudioInputStream, PushAudioInputStream
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient
from azure.identity import ClientSecretCredential
from datetime import datetime, timedelta
import json
import requests
from dotenv import load_dotenv
import azure.core.exceptions

class MultiModalAIProcessor:
    """
    Multi-modal AI processor that integrates various Azure AI services
    to process different types of content: text, images, documents, and audio.
    
    This class demonstrates the use of Azure's Responsible AI tools and
    multi-modal capabilities in a single cohesive service.
    """
    
    def __init__(self, config: Dict[str, str]):
        """Initialize the processor with configuration values"""
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Log configuration values (without sensitive data)
        self.logger.info("Initializing MultiModalAIProcessor with configuration:")
        self.logger.info(f"Form Recognizer endpoint: {config.get('FORM_RECOGNIZER_ENDPOINT')}")
        self.logger.info(f"Form Recognizer key length: {len(config.get('FORM_RECOGNIZER_KEY', ''))}")
        self.logger.info(f"Storage container: {config.get('STORAGE_CONTAINER')}")
        self.logger.info(f"Text Analytics endpoint: {config.get('TEXT_ANALYTICS_ENDPOINT')}")
        self.logger.info(f"Speech region: {config.get('SPEECH_REGION')}")
        self.logger.info(f"Content Safety endpoint: {config.get('CONTENT_SAFETY_ENDPOINT')}")
        self.logger.info(f"Document Translation endpoint: {config.get('DOCUMENT_TRANSLATION_ENDPOINT')}")
        self.logger.info(f"Cosmos DB endpoint: {config.get('COSMOS_ENDPOINT')}")
        self.logger.info(f"Cosmos DB database: {config.get('COSMOS_DATABASE')}")
        self.logger.info(f"Cosmos DB container: {config.get('COSMOS_CONTAINER')}")
        
        # Initialize Azure Form Recognizer
        try:
            self.logger.info("Initializing Form Recognizer client...")
            self.form_recognizer_client = DocumentAnalysisClient(
                endpoint=config["FORM_RECOGNIZER_ENDPOINT"],
                credential=AzureKeyCredential(config["FORM_RECOGNIZER_KEY"])
            )
            self.logger.info("Form Recognizer client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Form Recognizer: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Initialize Azure Storage
        try:
            self.logger.info("Initializing Azure Storage client...")
            self.blob_service_client = BlobServiceClient.from_connection_string(config["STORAGE_CONNECTION_STRING"])
            self.container_client = self.blob_service_client.get_container_client(config["STORAGE_CONTAINER"])
            
            # Verify container exists and is accessible
            try:
                container_properties = self.container_client.get_container_properties()
                self.logger.info(f"Container {config['STORAGE_CONTAINER']} exists and is accessible")
                self.logger.info(f"Container last modified: {container_properties.last_modified}")
                self.logger.info(f"Container ETag: {container_properties.etag}")
            except azure.core.exceptions.ResourceNotFoundError:
                self.logger.warning(f"Container {config['STORAGE_CONTAINER']} not found, creating it...")
                self.container_client = self.blob_service_client.create_container(config["STORAGE_CONTAINER"])
                self.logger.info(f"Container {config['STORAGE_CONTAINER']} created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure Storage: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Initialize Azure Text Analytics
        self.text_analytics_client = TextAnalyticsClient(
            endpoint=config["TEXT_ANALYTICS_ENDPOINT"],
            credential=AzureKeyCredential(config["TEXT_ANALYTICS_KEY"])
        )
        
        # Initialize Azure Speech Services
        self.speech_config = SpeechConfig(
            subscription=config["SPEECH_KEY"],
            region=config["SPEECH_REGION"]
        )
        
        # Initialize Azure Content Safety
        self.content_safety_client = ContentSafetyClient(
            endpoint=config["CONTENT_SAFETY_ENDPOINT"],
            credential=AzureKeyCredential(config["CONTENT_SAFETY_KEY"])
        )
        
        # Initialize Azure Document Translation
        self.document_translation_client = DocumentTranslationClient(
            endpoint=config["DOCUMENT_TRANSLATION_ENDPOINT"],
            credential=AzureKeyCredential(config["DOCUMENT_TRANSLATION_KEY"])
        )
        
        # Initialize Azure Cosmos DB
        self.cosmos_client = CosmosClient(
            url=config["COSMOS_ENDPOINT"],
            credential=config["COSMOS_KEY"]
        )
        
        # Add SAS token validity duration (1 hour)
        self.sas_token_validity = timedelta(hours=1)

    def _generate_sas_url(self, blob_client) -> str:
        """
        Generate a SAS URL for blob access
        
        Parameters:
            blob_client: Azure Blob client
            
        Returns:
            SAS URL string
        """
        try:
            # Get blob name and container name
            blob_name = blob_client.blob_name
            container_name = blob_client.container_name
            account_name = blob_client.account_name
            
            self.logger.info(f"Generating SAS URL for blob: {blob_name}")
            self.logger.info(f"Container: {container_name}")
            self.logger.info(f"Account: {account_name}")
            
            # Generate SAS token with read permissions
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
            
            # Log success (without exposing sensitive data)
            self.logger.info("Generated SAS URL successfully")
            self.logger.info(f"SAS URL length: {len(sas_url)}")
            self.logger.info(f"SAS URL starts with: {sas_url[:50]}...")
            
            # Test the URL
            try:
                response = requests.head(sas_url)
                response.raise_for_status()
                self.logger.info(f"SAS URL is accessible. Status code: {response.status_code}")
                self.logger.info(f"Response headers: {dict(response.headers)}")
            except Exception as e:
                self.logger.error(f"Failed to verify SAS URL accessibility: {str(e)}")
                self.logger.error(f"Error type: {type(e).__name__}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            return sas_url
            
        except Exception as e:
            self.logger.error(f"Error generating SAS URL: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def process_image(self, image_url: str) -> Dict[str, Any]:
        """
        Process an image using Azure AI Vision
        
        Parameters:
            image_url: URL of the image to process
            
        Returns:
            Dictionary containing image analysis results
        """
        self.logger.info(f"Processing image: {image_url}")
        
        try:
            # Create image analysis options
            analysis_options = {
                "features": [
                    VisualFeatureTypes.objects,
                    VisualFeatureTypes.tags,
                    VisualFeatureTypes.description,
                    VisualFeatureTypes.faces,
                    VisualFeatureTypes.text
                ]
            }

            # Analyze the image
            result = await self.vision_client.analyze_image_async(
                image_url=image_url,
                options=analysis_options
            )

            # Check content safety (Responsible AI)
            safety_result = await self._check_image_safety(image_url)
            
            # Combine all results
            analysis_result = {
                "objects": result.objects,
                "tags": result.tags,
                "caption": result.caption,
                "people": result.people,
                "text": result.text,
                "safety": safety_result
            }
            
            return analysis_result
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            return {"error": str(e)}

    async def process_document(self, document_url: str) -> Dict[str, Any]:
        """Process a document using Form Recognizer"""
        try:
            self.logger.info("=== Starting Document Processing ===")
            self.logger.info(f"Processing document from URL: {document_url[:50]}...")
            
            # Start the long-running operation
            self.logger.info("Starting Form Recognizer analysis...")
            async with self.form_recognizer_client:
                poller = await self.form_recognizer_client.begin_analyze_document_from_url(
                    "prebuilt-document",
                    document_url
                )
                self.logger.info("Waiting for Form Recognizer analysis to complete...")
                result = await poller.result()
            
            # Process the results
            self.logger.info("Processing Form Recognizer results...")
            processed_result = {
                "pages": [],
                "tables": [],
                "paragraphs": [],
                "key_value_pairs": [],
                "entities": []  # initialize entities as empty by default
            }
            
            # Extract pages
            for page in result.pages:
                try:
                    style_name = page.appearance.style.name if page.appearance and page.appearance.style else None
                    style_confidence = page.appearance.style.confidence if page.appearance and page.appearance.style else None
                except AttributeError:
                    style_name = None
                    style_confidence = None
                
                page_info = {
                    "page_number": page.page_number,
                    "lines": [line.content for line in page.lines],
                    "words": [word.content for word in page.words],
                    "appearance": {
                        "style": style_name,
                        "style_confidence": style_confidence
                    }
                }
                processed_result["pages"].append(page_info)
            
            # Extract tables
            for table in result.tables:
                table_info = {
                    "cells": [
                        {
                            "content": cell.content,
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                            "row_span": cell.row_span,
                            "column_span": cell.column_span
                        }
                        for cell in table.cells
                    ],
                    "row_count": table.row_count,
                    "column_count": table.column_count
                }
                processed_result["tables"].append(table_info)
            
            # Extract paragraphs with safe access to attributes
            for paragraph in result.paragraphs:
                # Safely extract style
                try:
                    style_name = paragraph.style.name if paragraph.style else None
                except AttributeError:
                    style_name = None
                
                # Safely extract confidence via try/except
                try:
                    conf = paragraph.confidence
                except AttributeError:
                    conf = None

                # Safely extract bounding_box if available
                try:
                    bb = paragraph.bounding_box
                except AttributeError:
                    bb = None

                # Create paragraph info with safe attribute access
                paragraph_info = {
                    "content": paragraph.content,
                    "bounding_box": bb,
                    "role": paragraph.role,
                    "style": style_name,
                    "confidence": conf
                }
                processed_result["paragraphs"].append(paragraph_info)
            
            # Extract key-value pairs (using getattr for safe access)
            for kv_pair in result.key_value_pairs:
                kv_info = {
                    "key": {
                        "content": kv_pair.key.content,
                        "bounding_box": getattr(kv_pair.key, "bounding_box", None),
                        "confidence": getattr(kv_pair.key, "confidence", None)
                    },
                    "value": {
                        "content": kv_pair.value.content,
                        "bounding_box": getattr(kv_pair.value, "bounding_box", None),
                        "confidence": getattr(kv_pair.value, "confidence", None)
                    },
                    "confidence": getattr(kv_pair, "confidence", None)
                }
                processed_result["key_value_pairs"].append(kv_info)
            
            # Conditionally extract entities only if they exist
            if hasattr(result, "entities"):
                for entity in result.entities:
                    entity_info = {
                        "category": entity.category,
                        "sub_category": entity.sub_category,
                        "content": entity.content,
                        "confidence": getattr(entity, "confidence", None),
                        "bounding_box": getattr(entity, "bounding_box", None)
                    }
                    processed_result["entities"].append(entity_info)
            else:
                self.logger.info("No entities attribute on the result; skipping entity extraction.")
            
            self.logger.info("Document processing completed successfully")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Error in process_document: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def process_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Process an audio file using Azure Speech Services
        
        Parameters:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription and analysis
        """
        self.logger.info(f"Processing audio: {audio_file_path}")
        
        # Configure audio source
        audio_config = AudioConfig(filename=audio_file_path)
        speech_recognizer = SpeechRecognizer(
            speech_config=self.speech_config, 
            audio_config=audio_config
        )
        
        # Transcribe audio
        result = await self._transcribe_audio(speech_recognizer)
        
        if result.text:
            # Analyze the transcribed text
            text_analysis = await self._analyze_text(result.text)
            
            # Check content safety (Responsible AI)
            safety_result = await self._check_text_safety(result.text)
            
            # Combine results
            audio_analysis = {
                "transcription": result.text,
                "entities": text_analysis.get("entities", []),
                "summary": text_analysis.get("summary", ""),
                "language": text_analysis.get("language", ""),
                "safety": safety_result,
                "durationInSeconds": result.duration.total_seconds() if hasattr(result, "duration") else None
            }
            
            return audio_analysis
        else:
            self.logger.error("Audio transcription failed")
            raise Exception("Audio transcription failed")

    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text using Azure Text Analytics Services"""
        if not text or len(text.strip()) == 0:
            return {}
        
        try:
            # Start multiple analyses in parallel
            poller = self.text_analytics_client.begin_analyze_actions(
                [text],
                actions=[
                    RecognizeEntitiesAction(),
                    AbstractiveSummaryAction()
                ]
            )
            
            # Get the results
            document_results = await poller.result()
            
            # Process results
            results = {}
            for result in document_results:
                if result.kind == "RecognizeEntities":
                    results["entities"] = [
                        {"text": entity.text, "category": entity.category}
                        for entity in result.entities
                    ]
                elif result.kind == "AbstractiveSummary":
                    results["summary"] = result.sentences[0].text if result.sentences else ""
                    
            return results
        except Exception as e:
            self.logger.error(f"Error analyzing text: {str(e)}")
            return {"error": str(e)}

    async def _transcribe_audio(self, speech_recognizer) -> Any:
        """Transcribe audio using Azure Speech Services"""
        done = asyncio.Event()
        result = None
        
        def recognized_cb(evt):
            nonlocal result
            result = evt
            done.set()
        
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.start_continuous_recognition()
        
        await done.wait()
        speech_recognizer.stop_continuous_recognition()
        
        return result

    async def _check_text_safety(self, text: str) -> Dict[str, Any]:
        """Check text for harmful content using Azure Content Safety"""
        # This is simplified for example purposes
        response = self.content_safety_client.analyze_text(
            text=text,
            categories=["Hate", "SelfHarm", "Sexual", "Violence"]
        )
        
        return {
            "is_safe": all(category.severity < 4 for category in response.categories),
            "categories": [
                {"category": category.category, "severity": category.severity}
                for category in response.categories
            ]
        }

    async def _check_image_safety(self, image_url: str) -> Dict[str, Any]:
        """Check image for harmful content using Azure Content Safety"""
        # This is simplified for example purposes
        response = self.content_safety_client.analyze_image_url(
            image_url={"url": image_url},
            categories=["Hate", "SelfHarm", "Sexual", "Violence"]
        )
        
        return {
            "is_safe": all(category.severity < 4 for category in response.categories),
            "categories": [
                {"category": category.category, "severity": category.severity}
                for category in response.categories
            ]
        }

    async def translate_document(self, source_url: str, target_language: str) -> str:
        """
        Translate a document to the target language
        
        Parameters:
            source_url: URL of the document to translate
            target_language: Target language code (e.g., 'es' for Spanish)
            
        Returns:
            URL of the translated document
        """
        self.logger.info(f"Translating document to {target_language}: {source_url}")
        
        # Generate unique source and target container names
        source_container_name = f"source-{os.urandom(4).hex()}"
        target_container_name = f"target-{os.urandom(4).hex()}"
        
        try:
            # Create source and target containers
            source_container = self.blob_service_client.create_container(source_container_name)
            target_container = self.blob_service_client.create_container(target_container_name)
            
            # Upload the source document
            blob_name = os.path.basename(source_url)
            blob_client = source_container.get_blob_client(blob_name)
            
            # Create the translation operation
            poller = self.document_translation_client.begin_translation(
                source_container_url=source_container.url,
                target_container_url=target_container.url,
                target_language=target_language
            )
            
            result = poller.result()
            
            # Get the URL of the translated document
            translated_blob = target_container.get_blob_client(blob_name)
            translated_url = translated_blob.url
            
            return translated_url
            
        finally:
            # Clean up containers
            self.blob_service_client.delete_container(source_container_name)
            self.blob_service_client.delete_container(target_container_name)

    async def process_multimodal_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multi-modal content with different types of media
        
        Parameters:
            content: Dictionary with URLs for different media types:
                    {
                        "document_url": str,
                        "image_url": str,
                        "audio_file_path": str
                    }
                    
        Returns:
            Combined analysis results from all modalities
        """
        self.logger.info("Processing multi-modal content")
        
        tasks = []
        
        # Process each modality if provided
        if "document_url" in content and content["document_url"]:
            tasks.append(self.process_document(content["document_url"]))
            
        if "image_url" in content and content["image_url"]:
            tasks.append(self.process_image(content["image_url"]))
            
        if "audio_file_path" in content and content["audio_file_path"]:
            tasks.append(self.process_audio(content["audio_file_path"]))
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error processing content: {str(result)}")
                continue
                
            if "document_url" in content and i == 0:
                combined_results["document_analysis"] = result
            elif "image_url" in content and (i == 1 if "document_url" in content else i == 0):
                combined_results["image_analysis"] = result
            elif "audio_file_path" in content:
                combined_results["audio_analysis"] = result
        
        return combined_results 