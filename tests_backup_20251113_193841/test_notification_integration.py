"""
Notification System Integration Tests
Comprehensive tests for notification system with UltraCore architecture
"""

import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ultracore.notifications.events import (
    NotificationType,
    AlertPriority,
    DeliveryChannel,
    DeliveryStatus,
    PriceAlertCreated,
    NotificationCreated
)
from ultracore.notifications.event_publisher import NotificationEventPublisher
from ultracore.notifications.aggregates import (
    PriceAlertAggregate,
    NotificationAggregate,
    NotificationPreferenceAggregate
)
from ultracore.agentic_ai.agents.notifications import get_notification_agent
from ultracore.ml.notifications import get_engagement_model, get_preference_learning_model
from ultracore.mcp.notification_tools import get_notification_tools
from ultracore.datamesh.notification_mesh import get_notification_data_product


class TestNotificationEventSourcing(unittest.TestCase):
    """Test event sourcing for notifications"""
    
    def setUp(self):
        self.event_publisher = NotificationEventPublisher()
        self.tenant_id = "test_tenant"
        self.client_id = "test_client"
    
    def test_price_alert_creation(self):
        """Test price alert creation via events"""
        alert = PriceAlertAggregate(
            tenant_id=self.tenant_id,
            alert_id="test_alert_1",
            client_id=self.client_id
        )
        
        alert.create(
            symbol="AAPL",
            target_price=150.00,
            alert_type="above"
        )
        
        self.assertEqual(alert.symbol, "AAPL")
        self.assertEqual(alert.target_price, 150.00)
        self.assertTrue(alert.active)
        self.assertEqual(len(alert.uncommitted_events), 1)
    
    def test_price_alert_trigger(self):
        """Test price alert triggering"""
        alert = PriceAlertAggregate(
            tenant_id=self.tenant_id,
            alert_id="test_alert_2",
            client_id=self.client_id
        )
        
        alert.create(symbol="TSLA", target_price=200.00, alert_type="above")
        alert.trigger(current_price=205.00)
        
        self.assertFalse(alert.active)
        self.assertIsNotNone(alert.triggered_at)
        self.assertEqual(alert.triggered_price, 205.00)
    
    def test_notification_creation(self):
        """Test notification creation via events"""
        notification = NotificationAggregate(
            tenant_id=self.tenant_id,
            notification_id="test_notif_1",
            client_id=self.client_id
        )
        
        notification.create(
            notification_type=NotificationType.PRICE_ALERT,
            title="Price Alert",
            message="AAPL reached target price",
            priority=AlertPriority.MEDIUM,
            channels=[DeliveryChannel.EMAIL, DeliveryChannel.PUSH]
        )
        
        self.assertEqual(notification.notification_type, NotificationType.PRICE_ALERT)
        self.assertEqual(notification.priority, AlertPriority.MEDIUM)
        self.assertEqual(len(notification.channels), 2)
    
    def test_notification_delivery(self):
        """Test notification delivery tracking"""
        notification = NotificationAggregate(
            tenant_id=self.tenant_id,
            notification_id="test_notif_2",
            client_id=self.client_id
        )
        
        notification.create(
            notification_type=NotificationType.TRANSACTION_CONFIRMATION,
            title="Transaction Confirmed",
            message="Your transaction has been confirmed",
            priority=AlertPriority.HIGH,
            channels=[DeliveryChannel.EMAIL]
        )
        
        notification.mark_sent(DeliveryChannel.EMAIL)
        notification.mark_delivered(DeliveryChannel.EMAIL)
        
        self.assertEqual(
            notification.delivery_status[DeliveryChannel.EMAIL],
            DeliveryStatus.DELIVERED
        )


class TestNotificationAgent(unittest.TestCase):
    """Test AI agent for notifications"""
    
    def setUp(self):
        self.agent = get_notification_agent()
        self.tenant_id = "test_tenant"
        self.client_id = "test_client"
    
    def test_price_alert_trigger_decision(self):
        """Test AI decision for price alert triggering"""
        result = self.agent.should_trigger_price_alert(
            symbol="AAPL",
            current_price=155.00,
            target_price=150.00,
            alert_type="above",
            historical_prices=[148.0, 149.0, 151.0, 153.0, 154.0],
            market_conditions={"high_volatility": False}
        )
        
        self.assertTrue(result["should_trigger"])
        self.assertIn("confidence", result)
    
    def test_portfolio_alert_trigger_decision(self):
        """Test AI decision for portfolio alert triggering"""
        result = self.agent.should_trigger_portfolio_alert(
            portfolio_id="portfolio_1",
            alert_type="rebalancing_needed",
            current_value=0.0,
            threshold_value=5.0,
            portfolio_data={"drift_percent": 7.5}
        )
        
        self.assertTrue(result["should_trigger"])
        self.assertIn("details", result)
    
    def test_priority_calculation(self):
        """Test AI priority calculation"""
        priority = self.agent.calculate_notification_priority(
            notification_type=NotificationType.PORTFOLIO_ALERT,
            client_data={"risk_profile": "high", "portfolio_value": 2000000},
            notification_data={},
            user_preferences={"engagement_score": 0.8}
        )
        
        self.assertIn(priority, [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH, AlertPriority.URGENT])
    
    def test_delivery_time_optimization(self):
        """Test AI delivery time optimization"""
        delivery_time = self.agent.optimize_delivery_time(
            client_id=self.client_id,
            notification_type=NotificationType.PORTFOLIO_SUMMARY,
            priority=AlertPriority.LOW,
            user_preferences={"quiet_hours_start": "22:00", "quiet_hours_end": "08:00"},
            historical_engagement=[]
        )
        
        self.assertIsInstance(delivery_time, datetime)
    
    def test_channel_selection(self):
        """Test AI channel selection"""
        channels = self.agent.select_delivery_channels(
            client_id=self.client_id,
            notification_type=NotificationType.PRICE_ALERT,
            priority=AlertPriority.URGENT,
            user_preferences={"channels": [DeliveryChannel.EMAIL]}
        )
        
        self.assertIsInstance(channels, list)
        self.assertGreater(len(channels), 0)
    
    def test_notification_suppression(self):
        """Test notification fatigue management"""
        recent_notifications = [
            {"created_at": datetime.utcnow() - timedelta(hours=i), "notification_type": NotificationType.PRICE_ALERT}
            for i in range(15)
        ]
        
        result = self.agent.should_suppress_notification(
            client_id=self.client_id,
            notification_type=NotificationType.PRICE_ALERT,
            priority=AlertPriority.LOW,
            recent_notifications=recent_notifications
        )
        
        self.assertIn("should_suppress", result)


class TestNotificationML(unittest.TestCase):
    """Test ML models for notifications"""
    
    def setUp(self):
        self.engagement_model = get_engagement_model()
        self.preference_model = get_preference_learning_model()
    
    def test_engagement_prediction(self):
        """Test engagement probability prediction"""
        prediction = self.engagement_model.predict_engagement(
            notification_data={
                "notification_type": NotificationType.PRICE_ALERT,
                "priority": AlertPriority.MEDIUM
            },
            user_data={
                "portfolio_value": 500000,
                "risk_profile": "medium"
            },
            historical_data=[]
        )
        
        self.assertIn("engagement_probability", prediction)
        self.assertGreaterEqual(prediction["engagement_probability"], 0.0)
        self.assertLessEqual(prediction["engagement_probability"], 1.0)
    
    def test_time_preference_learning(self):
        """Test learning user time preferences"""
        historical_data = [
            {"read_at": datetime(2024, 1, 1, 9, 0)},
            {"read_at": datetime(2024, 1, 2, 9, 15)},
            {"read_at": datetime(2024, 1, 3, 12, 30)},
            {"read_at": datetime(2024, 1, 4, 17, 0)},
        ]
        
        preferences = self.preference_model.learn_time_preferences(historical_data)
        
        self.assertIn("preferred_hours", preferences)
        self.assertIn("quiet_hours_start", preferences)
        self.assertIn("confidence", preferences)
    
    def test_channel_preference_learning(self):
        """Test learning user channel preferences"""
        historical_data = [
            {"channel": DeliveryChannel.EMAIL, "read_at": datetime.utcnow()},
            {"channel": DeliveryChannel.EMAIL, "read_at": datetime.utcnow()},
            {"channel": DeliveryChannel.PUSH, "read_at": None},
            {"channel": DeliveryChannel.SMS, "read_at": datetime.utcnow()},
        ]
        
        preferences = self.preference_model.learn_channel_preferences(historical_data)
        
        self.assertIn("preferred_channels", preferences)
        self.assertIn("channel_engagement_rates", preferences)
    
    def test_comprehensive_recommendations(self):
        """Test comprehensive preference recommendations"""
        historical_data = [
            {
                "notification_type": NotificationType.PRICE_ALERT,
                "channel": DeliveryChannel.EMAIL,
                "read_at": datetime(2024, 1, 1, 9, 0),
                "created_at": datetime(2024, 1, 1, 8, 55)
            }
            for _ in range(50)
        ]
        
        recommendations = self.preference_model.recommend_preferences(
            user_id=self.client_id,
            historical_data=historical_data
        )
        
        self.assertIn("recommended_settings", recommendations)
        self.assertIn("confidence", recommendations)
        self.assertGreater(recommendations["confidence"], 0.0)


class TestNotificationMCP(unittest.TestCase):
    """Test MCP tools for notifications"""
    
    def setUp(self):
        self.tools = get_notification_tools()
        self.tenant_id = "test_tenant"
        self.client_id = "test_client"
    
    def test_create_price_alert_tool(self):
        """Test price alert creation via MCP tool"""
        result = self.tools.create_price_alert(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            symbol="AAPL",
            target_price=150.00,
            alert_type="above"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("alert_id", result)
    
    def test_send_notification_tool(self):
        """Test notification sending via MCP tool"""
        result = self.tools.send_notification(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            notification_type="price_alert",
            title="Test Notification",
            message="This is a test",
            priority="medium"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("notification_id", result)
    
    def test_send_transaction_confirmation_tool(self):
        """Test transaction confirmation via MCP tool"""
        result = self.tools.send_transaction_confirmation(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            transaction_id="txn_123",
            transaction_type="buy",
            amount=1000.00,
            currency="AUD",
            symbol="AAPL",
            quantity=10.0
        )
        
        self.assertTrue(result["success"])
    
    def test_update_preferences_tool(self):
        """Test preference update via MCP tool"""
        result = self.tools.update_notification_preferences(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            notification_type="price_alert",
            enabled=True,
            channels=["EMAIL", "PUSH"],
            frequency="immediate"
        )
        
        self.assertTrue(result["success"])
    
    def test_get_recommendations_tool(self):
        """Test getting AI recommendations via MCP tool"""
        historical_data = [
            {
                "notification_type": NotificationType.PRICE_ALERT,
                "read_at": datetime.utcnow(),
                "created_at": datetime.utcnow() - timedelta(minutes=5)
            }
            for _ in range(20)
        ]
        
        result = self.tools.get_recommended_preferences(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            historical_data=historical_data
        )
        
        self.assertTrue(result["success"])
        self.assertIn("recommendations", result)


class TestNotificationDataMesh(unittest.TestCase):
    """Test data mesh for notifications"""
    
    def setUp(self):
        self.data_product = get_notification_data_product()
        self.tenant_id = "test_tenant"
        self.client_id = "test_client"
    
    def test_data_product_metadata(self):
        """Test data product metadata"""
        self.assertEqual(self.data_product.domain, "notifications")
        self.assertEqual(self.data_product.availability_sla, 99.9)
        self.assertTrue(self.data_product.privacy_act_compliant)
        self.assertTrue(self.data_product.asic_compliant)
    
    def test_get_notifications_api(self):
        """Test get notifications API"""
        notifications = self.data_product.get_notifications(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            limit=10
        )
        
        self.assertIsInstance(notifications, list)
    
    def test_get_price_alerts_api(self):
        """Test get price alerts API"""
        alerts = self.data_product.get_price_alerts(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            active_only=True
        )
        
        self.assertIsInstance(alerts, list)
    
    def test_consent_check_api(self):
        """Test consent check API (Privacy Act compliance)"""
        has_consent = self.data_product.has_consent(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            notification_type=NotificationType.PRICE_ALERT,
            channel=DeliveryChannel.EMAIL
        )
        
        self.assertIsInstance(has_consent, bool)
    
    def test_data_quality_metrics(self):
        """Test data quality metrics"""
        metrics = self.data_product.get_data_quality_metrics()
        
        self.assertIn("availability", metrics)
        self.assertIn("latency_p99_ms", metrics)
        self.assertIn("sla_compliance", metrics)


class TestNotificationCompliance(unittest.TestCase):
    """Test Australian compliance for notifications"""
    
    def setUp(self):
        self.data_product = get_notification_data_product()
        self.tenant_id = "test_tenant"
    
    def test_privacy_act_compliance(self):
        """Test Privacy Act 1988 compliance"""
        # Verify consent is required
        self.assertTrue(self.data_product.privacy_act_compliant)
        
        # Verify consent check exists
        consent = self.data_product.get_consent(
            tenant_id=self.tenant_id,
            client_id="test_client"
        )
        self.assertIsInstance(consent, (dict, type(None)))
    
    def test_asic_compliance(self):
        """Test ASIC compliance"""
        # Verify ASIC compliance flag
        self.assertTrue(self.data_product.asic_compliant)
        
        # Verify 7-year retention
        self.assertEqual(self.data_product.data_retention_days, 2555)  # ~7 years
    
    def test_audit_log_retention(self):
        """Test audit log retention (7 years)"""
        audit_log = self.data_product.get_audit_log(
            tenant_id=self.tenant_id,
            limit=100
        )
        
        self.assertIsInstance(audit_log, list)
    
    def test_compliance_reporting(self):
        """Test compliance report generation"""
        report = self.data_product.generate_compliance_report(
            tenant_id=self.tenant_id,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        self.assertIn("consent_compliance_rate", report)
        self.assertIn("privacy_violations", report)


def run_all_tests():
    """Run all notification system tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationEventSourcing))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationML))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationMCP))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationDataMesh))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationCompliance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_all_tests()
