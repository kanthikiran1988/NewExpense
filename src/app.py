"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import sys
import traceback
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
import json

from bot import bot_app
from config import Config
from botbuilder.core import TurnContext
from langchain_handler import message_handler  # Import the new handler

# Create the web app
APP = web.Application(middlewares=[aiohttp_error_middleware])

# Load configuration
CONFIG = Config()

# Create adapter with app credentials
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Basic health check endpoint
async def health_check(req: Request) -> Response:
    return Response(status=200, text="Bot is running!")

# Main bot message handler
async def messages(req: Request) -> Response:
    print("\n=== INCOMING REQUEST DEBUG ===")
    print(f"Method: {req.method}")
    print(f"Headers: {dict(req.headers)}")
    
    try:
        body = await req.json()
        print(f"Request body: {json.dumps(body, indent=2)}")
        
        activity = Activity().deserialize(body)
        print(f"\n=== ACTIVITY DEBUG ===")
        print(f"Activity type: {activity.type}")
        print(f"Activity text: {activity.text if hasattr(activity, 'text') else 'No text'}")
        print(f"Has attachments: {bool(activity.attachments)}")
        
        # Get auth header
        auth_header = req.headers.get("Authorization", "")
        
        async def bot_logic(turn_context: TurnContext):
            print("\n=== BOT LOGIC STARTED ===")
            
            # Initialize variables
            message_text = turn_context.activity.text or ""
            image_url = None
            
            # Check for image attachments
            if turn_context.activity.attachments:
                for attachment in turn_context.activity.attachments:
                    # Check if it's an image
                    if attachment.content_type.startswith('image/'):
                        print(f"Found image attachment: {attachment.content_type}")
                        image_url = attachment.content_url
                        break
                    # Check if it's a Teams file of image type
                    elif attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                        file_type = attachment.content.get('fileType', '').lower()
                        if file_type in ['jpg', 'jpeg', 'png', 'gif']:
                            print(f"Found Teams image file: {file_type}")
                            image_url = attachment.content.get('downloadUrl')
                            break
            
            # Process with Langchain handler
            print(f"Processing with Langchain - Text: {message_text}, Has Image: {bool(image_url)}")
            result = await message_handler.process_message(message_text, image_url)
            
            if result["success"]:
                # Send the response back to the user
                await turn_context.send_activity(result["response"])
            else:
                error_message = f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
                await turn_context.send_activity(error_message)
                
            print("=== BOT LOGIC COMPLETED ===")
        
        # Process activity
        print("\n=== PROCESSING ACTIVITY ===")
        await ADAPTER.process_activity(activity, auth_header, bot_logic)
        print("Activity processing completed")
        
        return Response(status=200)
    except Exception as e:
        print("\n=== ERROR DEBUG ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        traceback.print_exc()
        return Response(status=500, text=str(e))

# Add routes
APP.router.add_get("/health", health_check)
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=3978)
    except Exception as error:
        print(f"Error running app: {error}")
        raise error