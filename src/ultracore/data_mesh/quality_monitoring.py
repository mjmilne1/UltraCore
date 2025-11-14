"""
Data Quality Monitoring System.

Monitors and reports on data quality across all data products.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from enum import Enum

from .products.base import DataProduct, DataQualityMetrics, DataQualityLevel


class QualityAlertSeverity(str, Enum):
    """Quality alert severity levels."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action required within 24h
    MEDIUM = "medium"  # Action required within week
    LOW = "low"  # Monitor


class QualityAlert:
    """Data quality alert."""
    
    def __init__(
        self,
        product_id: str,
        metric_name: str,
        severity: QualityAlertSeverity,
        message: str,
        current_value: Decimal,
        threshold_value: Decimal
    ):
        self.alert_id = f"{product_id}_{metric_name}_{datetime.utcnow().timestamp()}"
        self.product_id = product_id
        self.metric_name = metric_name
        self.severity = severity
        self.message = message
        self.current_value = current_value
        self.threshold_value = threshold_value
        self.created_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None
        self.resolved_by: Optional[str] = None


class QualityThresholds:
    """Quality thresholds for monitoring."""
    
    # Completeness thresholds
    COMPLETENESS_CRITICAL = Decimal("80")
    COMPLETENESS_HIGH = Decimal("90")
    COMPLETENESS_MEDIUM = Decimal("95")
    
    # Accuracy thresholds
    ACCURACY_CRITICAL = Decimal("85")
    ACCURACY_HIGH = Decimal("92")
    ACCURACY_MEDIUM = Decimal("97")
    
    # Timeliness thresholds (minutes)
    TIMELINESS_CRITICAL = 60
    TIMELINESS_HIGH = 30
    TIMELINESS_MEDIUM = 15
    
    # Overall quality thresholds
    OVERALL_CRITICAL = Decimal("80")
    OVERALL_HIGH = Decimal("90")
    OVERALL_MEDIUM = Decimal("95")


class DataQualityMonitor:
    """
    Data quality monitoring system.
    
    Monitors data quality across all data products and generates alerts.
    """
    
    def __init__(self):
        self.active_alerts: List[QualityAlert] = []
        self.resolved_alerts: List[QualityAlert] = []
        self.quality_history: Dict[str, List[DataQualityMetrics]] = {}
    
    async def monitor_product(self, product: DataProduct) -> List[QualityAlert]:
        """
        Monitor a data product's quality.
        
        Args:
            product: Data product to monitor
            
        Returns:
            List of new quality alerts
        """
        # Measure quality
        metrics = await product.measure_quality()
        
        # Store in history
        product_id = product.metadata.product_id
        if product_id not in self.quality_history:
            self.quality_history[product_id] = []
        self.quality_history[product_id].append(metrics)
        
        # Check thresholds and generate alerts
        alerts = []
        
        # Check completeness
        if metrics.completeness_score < QualityThresholds.COMPLETENESS_CRITICAL:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="completeness",
                severity=QualityAlertSeverity.CRITICAL,
                message=f"Completeness score critically low: {metrics.completeness_score}%",
                current_value=metrics.completeness_score,
                threshold_value=QualityThresholds.COMPLETENESS_CRITICAL
            ))
        elif metrics.completeness_score < QualityThresholds.COMPLETENESS_HIGH:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="completeness",
                severity=QualityAlertSeverity.HIGH,
                message=f"Completeness score below threshold: {metrics.completeness_score}%",
                current_value=metrics.completeness_score,
                threshold_value=QualityThresholds.COMPLETENESS_HIGH
            ))
        
        # Check accuracy
        if metrics.accuracy_score < QualityThresholds.ACCURACY_CRITICAL:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="accuracy",
                severity=QualityAlertSeverity.CRITICAL,
                message=f"Accuracy score critically low: {metrics.accuracy_score}%",
                current_value=metrics.accuracy_score,
                threshold_value=QualityThresholds.ACCURACY_CRITICAL
            ))
        elif metrics.accuracy_score < QualityThresholds.ACCURACY_HIGH:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="accuracy",
                severity=QualityAlertSeverity.HIGH,
                message=f"Accuracy score below threshold: {metrics.accuracy_score}%",
                current_value=metrics.accuracy_score,
                threshold_value=QualityThresholds.ACCURACY_HIGH
            ))
        
        # Check overall quality
        if metrics.overall_quality_score < QualityThresholds.OVERALL_CRITICAL:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="overall_quality",
                severity=QualityAlertSeverity.CRITICAL,
                message=f"Overall quality critically low: {metrics.overall_quality_score}%",
                current_value=metrics.overall_quality_score,
                threshold_value=QualityThresholds.OVERALL_CRITICAL
            ))
        elif metrics.overall_quality_score < QualityThresholds.OVERALL_HIGH:
            alerts.append(QualityAlert(
                product_id=product_id,
                metric_name="overall_quality",
                severity=QualityAlertSeverity.HIGH,
                message=f"Overall quality below threshold: {metrics.overall_quality_score}%",
                current_value=metrics.overall_quality_score,
                threshold_value=QualityThresholds.OVERALL_HIGH
            ))
        
        # Add to active alerts
        self.active_alerts.extend(alerts)
        
        return alerts
    
    async def get_quality_report(
        self,
        product_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get quality report for products.
        
        Args:
            product_id: Optional product ID to filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Quality report dictionary
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        report = {
            "report_generated_at": datetime.utcnow(),
            "period_start": start_date,
            "period_end": end_date,
            "products": []
        }
        
        # Filter products
        products_to_report = [product_id] if product_id else self.quality_history.keys()
        
        for pid in products_to_report:
            if pid not in self.quality_history:
                continue
            
            # Filter metrics by date
            metrics_in_period = [
                m for m in self.quality_history[pid]
                if start_date <= m.measured_at <= end_date
            ]
            
            if not metrics_in_period:
                continue
            
            # Calculate averages
            avg_completeness = sum(m.completeness_score for m in metrics_in_period) / len(metrics_in_period)
            avg_accuracy = sum(m.accuracy_score for m in metrics_in_period) / len(metrics_in_period)
            avg_consistency = sum(m.consistency_score for m in metrics_in_period) / len(metrics_in_period)
            avg_timeliness = sum(m.timeliness_score for m in metrics_in_period) / len(metrics_in_period)
            avg_uniqueness = sum(m.uniqueness_score for m in metrics_in_period) / len(metrics_in_period)
            avg_overall = sum(m.overall_quality_score for m in metrics_in_period) / len(metrics_in_period)
            
            # Get active alerts for product
            product_alerts = [a for a in self.active_alerts if a.product_id == pid]
            
            report["products"].append({
                "product_id": pid,
                "measurements_count": len(metrics_in_period),
                "average_scores": {
                    "completeness": float(avg_completeness),
                    "accuracy": float(avg_accuracy),
                    "consistency": float(avg_consistency),
                    "timeliness": float(avg_timeliness),
                    "uniqueness": float(avg_uniqueness),
                    "overall": float(avg_overall)
                },
                "active_alerts_count": len(product_alerts),
                "critical_alerts_count": len([a for a in product_alerts if a.severity == QualityAlertSeverity.CRITICAL]),
                "latest_measurement": metrics_in_period[-1].measured_at
            })
        
        return report
    
    def get_active_alerts(
        self,
        product_id: Optional[str] = None,
        severity: Optional[QualityAlertSeverity] = None
    ) -> List[QualityAlert]:
        """Get active quality alerts."""
        alerts = self.active_alerts
        
        if product_id:
            alerts = [a for a in alerts if a.product_id == product_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve a quality alert."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                self.active_alerts.remove(alert)
                self.resolved_alerts.append(alert)
                return True
        return False
    
    def get_quality_trend(
        self,
        product_id: str,
        metric_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get quality trend for a specific metric.
        
        Args:
            product_id: Product ID
            metric_name: Metric name (completeness, accuracy, etc.)
            days: Number of days to look back
            
        Returns:
            List of data points with date and value
        """
        if product_id not in self.quality_history:
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        metrics = [
            m for m in self.quality_history[product_id]
            if m.measured_at >= cutoff_date
        ]
        
        trend = []
        for m in metrics:
            value = getattr(m, f"{metric_name}_score", None)
            if value is not None:
                trend.append({
                    "date": m.measured_at,
                    "value": float(value)
                })
        
        return trend


# Global quality monitor instance
quality_monitor = DataQualityMonitor()
