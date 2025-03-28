import requests

def analyze_text(text, azure_endpoint, azure_key):
    """
    Sends the extracted text to Azure Text Analytics for sentiment analysis.

    Args:
        text (str): The extracted text to be analyzed.
        azure_endpoint (str): The Azure Text Analytics endpoint.
        azure_key (str): The Azure API subscription key.

    Returns:
        dict: The response from the Azure API or an error message.
    """
    # Define headers for the API request
    headers = {
        'Ocp-Apim-Subscription-Key': azure_key,
        'Content-Type': 'application/json'
    }

    # Define the body of the API request
    body = {
        "documents": [
            {"id": "1", "language": "en", "text": text}
        ]
    }

    try:
        # Send the POST request to the Azure endpoint
        response = requests.post(azure_endpoint, headers=headers, json=body)
        response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        # Handle request exceptions
        print(f"Azure API Request Error: {e}")
        return {"error": str(e)}
