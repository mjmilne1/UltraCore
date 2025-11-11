"""
Channel Integration for Multi-Modal Service
Connect all customer touchpoints
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import websockets
from pathlib import Path

# ============================================================================
# CHANNEL ADAPTERS
# ============================================================================

class WebChatAdapter:
    """Web chat with rich media support"""
    
    def __init__(self, service_hub):
        self.hub = service_hub
        self.active_sessions = {}
    
    async def handle_connection(self, websocket, path):
        """Handle WebSocket connection"""
        
        # Start session
        customer_id = await self.authenticate(websocket)
        session_id, welcome = await self.hub.start_session(
            customer_id,
            ServiceChannel.WEB_CHAT,
            Modality.TEXT
        )
        
        # Send welcome
        await websocket.send(json.dumps(welcome))
        
        # Handle messages
        try:
            async for message in websocket:
                data = json.loads(message)
                
                # Determine modality
                if data.get("type") == "text":
                    result = await self.hub.process_input(
                        session_id,
                        data["content"],
                        Modality.TEXT
                    )
                elif data.get("type") == "image":
                    # Decode base64 image
                    image_data = base64.b64decode(data["content"])
                    result = await self.hub.process_input(
                        session_id,
                        image_data,
                        Modality.VISION
                    )
                elif data.get("type") == "audio":
                    # Decode audio
                    audio_data = base64.b64decode(data["content"])
                    result = await self.hub.process_input(
                        session_id,
                        audio_data,
                        Modality.VOICE
                    )
                else:
                    result = {"error": "Unknown message type"}
                
                # Send response
                await websocket.send(json.dumps(result))
                
        except websockets.exceptions.ConnectionClosed:
            # Clean up session
            del self.active_sessions[session_id]


class MobileAppAdapter:
    """Mobile app with native features"""
    
    def __init__(self, service_hub):
        self.hub = service_hub
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mobile app API request"""
        
        customer_id = request["customer_id"]
        session_id = request.get("session_id")
        
        # Start or continue session
        if not session_id:
            session_id, welcome = await self.hub.start_session(
                customer_id,
                ServiceChannel.MOBILE_APP,
                Modality.TEXT
            )
            return {"session_id": session_id, "welcome": welcome}
        
        # Process based on request type
        if request["type"] == "biometric_auth":
            # Handle face/fingerprint auth
            return await self.handle_biometric(request)
        elif request["type"] == "camera_capture":
            # Handle document scan
            return await self.handle_camera(request)
        elif request["type"] == "voice_note":
            # Handle voice message
            return await self.hub.process_input(
                session_id,
                request["audio_data"],
                Modality.VOICE
            )
        else:
            # Text message
            return await self.hub.process_input(
                session_id,
                request["message"],
                Modality.TEXT
            )
    
    async def handle_biometric(self, request: Dict) -> Dict[str, Any]:
        """Handle biometric authentication"""
        
        # Would integrate with device biometric API
        return {
            "authenticated": True,
            "auth_level": 3,
            "method": request.get("biometric_type", "face")
        }
    
    async def handle_camera(self, request: Dict) -> Dict[str, Any]:
        """Handle camera capture for documents"""
        
        image_data = base64.b64decode(request["image"])
        
        # Process with vision
        result = await self.hub.process_input(
            request["session_id"],
            image_data,
            Modality.VISION
        )
        
        # Add mobile-specific features
        result["mobile_actions"] = [
            "Retake photo",
            "Use gallery",
            "Scan barcode"
        ]
        
        return result


class VideoBankingAdapter:
    """Video banking with screen sharing"""
    
    def __init__(self, service_hub):
        self.hub = service_hub
        self.active_calls = {}
        
    async def start_video_call(
        self,
        customer_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start video banking session"""
        
        # Start session
        session_id, welcome = await self.hub.start_session(
            customer_id,
            ServiceChannel.VIDEO_CALL,
            Modality.VIDEO
        )
        
        # Create call room
        call_id = f"CALL_{session_id}"
        self.active_calls[call_id] = {
            "session_id": session_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "start_time": datetime.now(),
            "recording": agent_id is not None  # Record if agent present
        }
        
        return {
            "call_id": call_id,
            "session_id": session_id,
            "welcome": welcome,
            "features": [
                "screen_share",
                "document_share", 
                "co_browse",
                "digital_signature"
            ]
        }
    
    async def process_video_stream(
        self,
        call_id: str,
        video_stream: AsyncGenerator
    ) -> Dict[str, Any]:
        """Process live video stream"""
        
        call_info = self.active_calls.get(call_id)
        if not call_info:
            return {"error": "Invalid call ID"}
        
        # Process video
        result = await self.hub.process_input(
            call_info["session_id"],
            video_stream,
            Modality.VIDEO
        )
        
        # Add video-specific features
        result["video_features"] = {
            "blur_background": True,
            "virtual_background": ["office", "home", "neutral"],
            "screen_annotation": True
        }
        
        return result


class WhatsAppAdapter:
    """WhatsApp Business API integration"""
    
    def __init__(self, service_hub):
        self.hub = service_hub
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WhatsApp message"""
        
        phone = message["from"]
        customer_id = await self.get_customer_by_phone(phone)
        
        # Get or create session
        session_id = self.get_session(phone)
        if not session_id:
            session_id, _ = await self.hub.start_session(
                customer_id,
                ServiceChannel.WHATSAPP,
                Modality.TEXT
            )
            self.store_session(phone, session_id)
        
        # Process based on message type
        if message["type"] == "text":
            result = await self.hub.process_input(
                session_id,
                message["text"]["body"],
                Modality.TEXT
            )
        elif message["type"] == "image":
            # Download and process image
            image_data = await self.download_media(message["image"]["id"])
            result = await self.hub.process_input(
                session_id,
                image_data,
                Modality.VISION
            )
        elif message["type"] == "audio":
            # Download and process audio
            audio_data = await self.download_media(message["audio"]["id"])
            result = await self.hub.process_input(
                session_id,
                audio_data,
                Modality.VOICE
            )
        else:
            result = {"error": "Unsupported message type"}
        
        # Format for WhatsApp
        return self.format_whatsapp_response(result)
    
    def format_whatsapp_response(self, result: Dict) -> Dict[str, Any]:
        """Format response for WhatsApp API"""
        
        response = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "type": "text",
            "text": {
                "preview_url": False,
                "body": result.get("text", "")
            }
        }
        
        # Add quick reply buttons if available
        if result.get("quick_actions"):
            response["type"] = "interactive"
            response["interactive"] = {
                "type": "button",
                "body": {"text": result["text"]},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": f"btn_{i}", "title": action}}
                        for i, action in enumerate(result["quick_actions"][:3])
                    ]
                }
            }
        
        return response


class SmartATMInterface:
    """Smart ATM with video assistance"""
    
    def __init__(self, service_hub):
        self.hub = service_hub
        self.atm_sessions = {}
        
    async def start_atm_session(
        self,
        atm_id: str,
        card_number: str
    ) -> Dict[str, Any]:
        """Start smart ATM session"""
        
        # Get customer from card
        customer_id = await self.get_customer_by_card(card_number)
        
        # Start session with video capability
        session_id, welcome = await self.hub.start_session(
            customer_id,
            ServiceChannel.SMART_ATM,
            Modality.MULTI
        )
        
        self.atm_sessions[atm_id] = {
            "session_id": session_id,
            "customer_id": customer_id,
            "authenticated": False
        }
        
        return {
            "session_id": session_id,
            "welcome": welcome,
            "features": [
                "video_assistance",
                "document_scanning",
                "check_deposit",
                "cardless_withdrawal"
            ]
        }
    
    async def process_atm_interaction(
        self,
        atm_id: str,
        interaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process ATM interaction"""
        
        session_info = self.atm_sessions.get(atm_id)
        if not session_info:
            return {"error": "Invalid ATM session"}
        
        # Handle different interactions
        if interaction["type"] == "pin_entry":
            # Authenticate
            session_info["authenticated"] = True
            return {"authenticated": True, "menu": self.get_atm_menu()}
            
        elif interaction["type"] == "video_help":
            # Start video assistance
            return await self.start_video_assistance(session_info["session_id"])
            
        elif interaction["type"] == "document_scan":
            # Scan check or document
            image_data = interaction["image"]
            return await self.hub.process_input(
                session_info["session_id"],
                image_data,
                Modality.VISION
            )
        
        else:
            # Process as text command
            return await self.hub.process_input(
                session_info["session_id"],
                interaction["command"],
                Modality.TEXT
            )
