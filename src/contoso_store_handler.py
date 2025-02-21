"""
Contoso Store API Handler
"""

import aiohttp
import json
from typing import Dict, Any
from datetime import datetime

class ContosoStoreHandler:
    def __init__(self):
        self.api_url = "https://newhscontosochatpoc-ca.yellowhill-7d24b3f1.francecentral.azurecontainerapps.io/api/create_response"
        self.timeout = aiohttp.ClientTimeout(total=120)  # 120 seconds timeout
        self.customer_id = "6"  # Fixed customer ID

    async def get_store_response(self, question: str) -> Dict[str, Any]:
        """
        Get response from Contoso store API
        
        Args:
            question (str): The user's question about the store
            
        Returns:
            Dict[str, Any]: Response containing success status and either answer or error
        """
        try:
            payload = {
                "question": question,
                "customer_id": self.customer_id,
                "chat_history": "[]"  # Empty chat history as per requirement
            }
            
            print(f"\n=== CONTOSO STORE API REQUEST ===")
            print(f"Question: {question}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"API Response received: {json.dumps(data, indent=2)}")
                        
                        # Extract just the answer from the response
                        if "answer" in data:
                            return {
                                "success": True,
                                "response": data["answer"]
                            }
                        else:
                            return {
                                "success": False,
                                "error": "No answer in API response"
                            }
                    else:
                        error_msg = f"API request failed with status {response.status}"
                        print(f"Error: {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg
                        }
                        
        except Exception as e:
            error_msg = f"Error accessing store information: {str(e)}"
            print(f"Exception: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

# Create singleton instance
store_handler = ContosoStoreHandler() 