"""Webhook Service"""
import asyncio
import hashlib
import hmac
from typing import List, Dict
from datetime import datetime
import aiohttp

class WebhookService:
    """Service for managing and delivering webhooks"""
    
    def __init__(self):
        """Initialize webhook service"""
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # seconds
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def deliver_webhook(self, webhook_url: str, event_type: str,
                             payload: Dict, secret: str,
                             delivery_id: str) -> Dict:
        """Deliver webhook with retries"""
        import json
        
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str, secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type,
            "X-Webhook-Delivery-ID": delivery_id
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = datetime.utcnow()
                    
                    async with session.post(
                        webhook_url,
                        data=payload_str,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                        
                        if response.status < 300:
                            return {
                                "success": True,
                                "status_code": response.status,
                                "response_time_ms": response_time_ms,
                                "attempt": attempt + 1
                            }
                        else:
                            error_message = await response.text()
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.retry_delays[attempt])
                                continue
                            
                            return {
                                "success": False,
                                "status_code": response.status,
                                "error_message": error_message,
                                "attempt": attempt + 1
                            }
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delays[attempt])
                    continue
                
                return {
                    "success": False,
                    "error_message": str(e),
                    "attempt": attempt + 1
                }
        
        return {
            "success": False,
            "error_message": "Max retries exceeded",
            "attempt": self.max_retries
        }
    
    async def trigger_webhooks(self, event_type: str, payload: Dict,
                              webhooks: List[Dict]) -> List[Dict]:
        """Trigger all webhooks subscribed to event type"""
        results = []
        
        for webhook in webhooks:
            if event_type in webhook.get("events", []):
                delivery_id = f"{webhook['webhook_id']}_{datetime.utcnow().timestamp()}"
                
                result = await self.deliver_webhook(
                    webhook["url"],
                    event_type,
                    payload,
                    webhook["secret"],
                    delivery_id
                )
                
                results.append({
                    "webhook_id": webhook["webhook_id"],
                    "delivery_id": delivery_id,
                    **result
                })
        
        return results
