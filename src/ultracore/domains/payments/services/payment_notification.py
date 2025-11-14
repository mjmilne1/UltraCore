"""
Payment Notification Service.

Handles payment notifications and alerts.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

from ..models.payment import Payment
from ..models.enums import PaymentStatus


class PaymentNotificationService:
    """Service for sending payment notifications."""
    
    def __init__(self):
        """Initialize notification service."""
        pass
    
    async def notify_payment_created(
        self,
        payment: Payment,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Notify customer that payment was created.
        
        Args:
            payment: Payment that was created
            customer_email: Customer email
            customer_phone: Customer phone
            
        Returns:
            Notification result
        """
        notification = {
            "type": "payment_created",
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "description": payment.description,
            "status": payment.status,
            "timestamp": datetime.utcnow()
        }
        
        results = []
        
        # Send email
        if customer_email:
            email_result = await self._send_email(
                to=customer_email,
                subject=f"Payment Created - {payment.amount} {payment.currency}",
                template="payment_created",
                data=notification
            )
            results.append({"channel": "email", "result": email_result})
        
        # Send SMS for high-value payments
        if customer_phone and payment.amount >= Decimal("10000"):
            sms_result = await self._send_sms(
                to=customer_phone,
                message=f"High-value payment of {payment.amount} {payment.currency} created. Ref: {payment.payment_id[:8]}"
            )
            results.append({"channel": "sms", "result": sms_result})
        
        # Send push notification
        push_result = await self._send_push(
            customer_id=payment.from_customer_id,
            title="Payment Created",
            body=f"{payment.amount} {payment.currency} payment to {payment.description}",
            data=notification
        )
        results.append({"channel": "push", "result": push_result})
        
        return {
            "success": True,
            "notifications_sent": len([r for r in results if r["result"]["success"]]),
            "results": results
        }
    
    async def notify_payment_completed(
        self,
        payment: Payment,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Notify customer that payment was completed.
        
        Args:
            payment: Payment that was completed
            customer_email: Customer email
            customer_phone: Customer phone
            
        Returns:
            Notification result
        """
        notification = {
            "type": "payment_completed",
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "description": payment.description,
            "completed_at": payment.completed_at,
            "timestamp": datetime.utcnow()
        }
        
        results = []
        
        # Send email with receipt
        if customer_email:
            email_result = await self._send_email(
                to=customer_email,
                subject=f"Payment Completed - {payment.amount} {payment.currency}",
                template="payment_completed",
                data=notification,
                attachments=["receipt.pdf"]  # TODO: Generate receipt
            )
            results.append({"channel": "email", "result": email_result})
        
        # Send SMS
        if customer_phone:
            sms_result = await self._send_sms(
                to=customer_phone,
                message=f"Payment of {payment.amount} {payment.currency} completed. Ref: {payment.payment_id[:8]}"
            )
            results.append({"channel": "sms", "result": sms_result})
        
        # Send push notification
        push_result = await self._send_push(
            customer_id=payment.from_customer_id,
            title="Payment Completed",
            body=f"{payment.amount} {payment.currency} payment completed successfully",
            data=notification
        )
        results.append({"channel": "push", "result": push_result})
        
        return {
            "success": True,
            "notifications_sent": len([r for r in results if r["result"]["success"]]),
            "results": results
        }
    
    async def notify_payment_failed(
        self,
        payment: Payment,
        error_message: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Notify customer that payment failed.
        
        Args:
            payment: Payment that failed
            error_message: Error message
            customer_email: Customer email
            customer_phone: Customer phone
            
        Returns:
            Notification result
        """
        notification = {
            "type": "payment_failed",
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "description": payment.description,
            "error": error_message,
            "timestamp": datetime.utcnow()
        }
        
        results = []
        
        # Send email
        if customer_email:
            email_result = await self._send_email(
                to=customer_email,
                subject=f"Payment Failed - {payment.amount} {payment.currency}",
                template="payment_failed",
                data=notification
            )
            results.append({"channel": "email", "result": email_result})
        
        # Send SMS for high-value payments
        if customer_phone and payment.amount >= Decimal("10000"):
            sms_result = await self._send_sms(
                to=customer_phone,
                message=f"High-value payment of {payment.amount} {payment.currency} failed. Please contact support."
            )
            results.append({"channel": "sms", "result": sms_result})
        
        # Send push notification
        push_result = await self._send_push(
            customer_id=payment.from_customer_id,
            title="Payment Failed",
            body=f"{payment.amount} {payment.currency} payment failed: {error_message}",
            data=notification
        )
        results.append({"channel": "push", "result": push_result})
        
        return {
            "success": True,
            "notifications_sent": len([r for r in results if r["result"]["success"]]),
            "results": results
        }
    
    async def notify_scheduled_payment_upcoming(
        self,
        schedule_id: str,
        amount: Decimal,
        currency: str,
        description: str,
        scheduled_date: datetime,
        days_until: int,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Notify customer of upcoming scheduled payment.
        
        Args:
            schedule_id: Schedule ID
            amount: Payment amount
            currency: Currency
            description: Description
            scheduled_date: Scheduled date
            days_until: Days until payment
            customer_email: Customer email
            
        Returns:
            Notification result
        """
        notification = {
            "type": "scheduled_payment_upcoming",
            "schedule_id": schedule_id,
            "amount": amount,
            "currency": currency,
            "description": description,
            "scheduled_date": scheduled_date,
            "days_until": days_until,
            "timestamp": datetime.utcnow()
        }
        
        results = []
        
        # Send email
        if customer_email:
            email_result = await self._send_email(
                to=customer_email,
                subject=f"Upcoming Payment - {amount} {currency} in {days_until} days",
                template="scheduled_payment_upcoming",
                data=notification
            )
            results.append({"channel": "email", "result": email_result})
        
        return {
            "success": True,
            "notifications_sent": len([r for r in results if r["result"]["success"]]),
            "results": results
        }
    
    async def _send_email(
        self,
        to: str,
        subject: str,
        template: str,
        data: Dict[str, Any],
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send email notification."""
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        return {
            "success": True,
            "channel": "email",
            "to": to,
            "sent_at": datetime.utcnow()
        }
    
    async def _send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """Send SMS notification."""
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        return {
            "success": True,
            "channel": "sms",
            "to": to,
            "sent_at": datetime.utcnow()
        }
    
    async def _send_push(
        self,
        customer_id: str,
        title: str,
        body: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send push notification."""
        # TODO: Integrate with push notification service (Firebase, etc.)
        return {
            "success": True,
            "channel": "push",
            "customer_id": customer_id,
            "sent_at": datetime.utcnow()
        }
