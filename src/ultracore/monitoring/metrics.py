"""Unified Metrics Collection"""
from typing import Dict, Any
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect metrics across all frameworks."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}
        logger.info("MetricsCollector initialized")
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict = None):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self.counters[key] += value
    
    def record_histogram(self, name: str, value: float, labels: Dict = None):
        """Record a histogram value."""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict = None):
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def _make_key(self, name: str, labels: Dict = None) -> str:
        """Make metric key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self.counters),
            "histograms": {k: self._histogram_stats(v) for k, v in self.histograms.items()},
            "gauges": dict(self.gauges)
        }
    
    def _histogram_stats(self, values: list) -> Dict:
        """Calculate histogram statistics."""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "sum": sum(values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[len(values) // 2],
            "p95": sorted_values[int(len(values) * 0.95)],
            "p99": sorted_values[int(len(values) * 0.99)]
        }

# Global metrics instance
_metrics_instance = None

def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
