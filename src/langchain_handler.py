from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, Optional
import json
from datetime import datetime
from config import Config
import base64
from aiohttp import ClientSession
from contoso_store_handler import store_handler

class LangchainMessageHandler:
    def __init__(self):
        config = Config()
        self.llm = AzureChatOpenAI(
            deployment_name=config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME,
            openai_api_version="2024-02-15-preview",
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.7,
            streaming=True
        )
        print(f"LangchainMessageHandler initialized with model: {config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME}")

    async def process_message(self, message_text: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Process a message and optional image using Langchain and return the response"""
        print(f"\n=== LANGCHAIN MESSAGE PROCESSING ===")
        print(f"Input message: {message_text}")
        print(f"Has image: {bool(image_url)}")
        
        try:
            if image_url:
                # Download and encode image
                image_data = await self._download_image(image_url)
                if not image_data:
                    return {
                        "success": False,
                        "error": "Failed to download image",
                        "metadata": {
                            "processed_at": datetime.utcnow().isoformat(),
                            "error_type": "ImageDownloadError"
                        }
                    }
                
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                messages = [
                    SystemMessage(content="""You are an expert expense analyzer. When analyzing receipts or invoices:
                    1. Identify the vendor/merchant name
                    2. Find the total amount
                    3. Locate the date of transaction
                    4. List any itemized expenses if present
                    5. Note any special charges, taxes, or tips
                    Be clear and organized in your response."""),
                    HumanMessage(content=[
                        {"type": "text", "text": message_text if message_text else "Please analyze this receipt/invoice and provide the key details."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ])
                ]
            else:
                messages = [
                    SystemMessage(content="""You are a helpful AI assistant with access to Contoso store information through a specialized API. 
                    Your task is to:
                    1. Determine if the user's question is about products, store information, or shopping at Contoso
                    2. For store-related queries, respond with: {"use_store_api": true, "query": "<user's question>"}
                    3. For non-store queries about expense management, help with:
                       - Understanding receipts and invoices
                       - Categorizing expenses
                       - Providing expense insights
                       - Answering questions about expense policies
                    Be concise but informative in your responses."""),
                    HumanMessage(content=message_text)
                ]

            print("Sending to LLM for processing...")
            response = await self.llm.ainvoke(messages)
            print("Received response from LLM")
            print(f"Response: {response.content}")

            # Check if the response indicates we should use the store API
            try:
                if not image_url and response.content.__contains__('"use_store_api": true'):
                    print("Using store API...")
                    api_response = json.loads(response.content)
                    if api_response.get("use_store_api"):
                        # Call the store API
                        try:
                            store_result = await store_handler.get_store_response(api_response["query"])
                            if store_result["success"]:
                                return {
                                    "success": True,
                                    "response": store_result["response"]
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": "Unable to access store information at this time. Please try again later."
                                }
                        except Exception as e:
                            print(f"Error calling store API: {str(e)}")
                            return {
                                "success": False,
                                "error": "Error calling store API",
                                "metadata": {
                                    "processed_at": datetime.utcnow().isoformat(),
                                    "error_type": type(e).__name__
                                }
                            }
            except:
                pass  # If parsing fails, treat it as a normal response


            return {
                "success": True,
                "response": response.content,
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "model": "gpt-4o",
                    "type": "image_analysis" if image_url else "text_response"
                }
            }
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "error_type": type(e).__name__
                }
            }

    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            print(f"Downloading image from: {url}")
            async with ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        print(f"Successfully downloaded image: {len(content)} bytes")
                        return content
                    else:
                        print(f"Failed to download image. Status: {response.status}")
                        return None
        except Exception as e:
            print(f"Error downloading image: {str(e)}")
            return None

# Create a singleton instance
message_handler = LangchainMessageHandler() 