"""
Performance testing helpers.

Provides benchmarking, load testing, and chaos engineering utilities.
"""

import time
import asyncio
import random
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, median, stdev


@dataclass
class PerformanceMetrics:
    """Performance test metrics."""
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_seconds: float
    min_latency_ms: float
    max_latency_ms: float
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_duration_seconds": self.total_duration_seconds,
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "mean_latency_ms": self.mean_latency_ms,
            "median_latency_ms": self.median_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "requests_per_second": self.requests_per_second,
            "error_count": len(self.errors)
        }


class PerformanceBenchmark:
    """
    Performance benchmark runner.
    
    Measures latency, throughput, and resource usage.
    """
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
    
    async def benchmark(
        self,
        operation_name: str,
        operation: Callable,
        num_requests: int = 1000,
        concurrency: int = 10
    ) -> PerformanceMetrics:
        """
        Benchmark an operation.
        
        Args:
            operation_name: Name of operation
            operation: Async function to benchmark
            num_requests: Total number of requests
            concurrency: Number of concurrent requests
        
        Returns:
            Performance metrics
        """
        latencies = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        # Run requests in batches
        for batch_start in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - batch_start)
            
            # Create tasks
            tasks = []
            for _ in range(batch_size):
                tasks.append(self._execute_request(operation))
            
            # Execute batch
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    errors.append(str(result))
                else:
                    successful += 1
                    latencies.append(result)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate metrics
        if latencies:
            sorted_latencies = sorted(latencies)
            p95_index = int(len(sorted_latencies) * 0.95)
            p99_index = int(len(sorted_latencies) * 0.99)
            
            metrics = PerformanceMetrics(
                operation=operation_name,
                total_requests=num_requests,
                successful_requests=successful,
                failed_requests=failed,
                total_duration_seconds=total_duration,
                min_latency_ms=min(latencies),
                max_latency_ms=max(latencies),
                mean_latency_ms=mean(latencies),
                median_latency_ms=median(latencies),
                p95_latency_ms=sorted_latencies[p95_index],
                p99_latency_ms=sorted_latencies[p99_index],
                requests_per_second=num_requests / total_duration,
                errors=errors[:10]  # Keep first 10 errors
            )
        else:
            metrics = PerformanceMetrics(
                operation=operation_name,
                total_requests=num_requests,
                successful_requests=0,
                failed_requests=num_requests,
                total_duration_seconds=total_duration,
                min_latency_ms=0,
                max_latency_ms=0,
                mean_latency_ms=0,
                median_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                requests_per_second=0,
                errors=errors[:10]
            )
        
        self.results.append(metrics)
        return metrics
    
    async def _execute_request(self, operation: Callable) -> float:
        """Execute single request and measure latency."""
        start = time.time()
        await operation()
        end = time.time()
        return (end - start) * 1000  # Convert to milliseconds


class LoadTester:
    """
    Load testing utility.
    
    Simulates realistic load patterns.
    """
    
    def __init__(self):
        self.active_users = 0
        self.total_requests = 0
    
    async def ramp_up_test(
        self,
        operation: Callable,
        start_users: int = 1,
        max_users: int = 100,
        ramp_duration_seconds: int = 60,
        test_duration_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Ramp-up load test.
        
        Gradually increases load from start_users to max_users.
        """
        results = []
        
        # Ramp-up phase
        ramp_step = (max_users - start_users) / (ramp_duration_seconds / 10)
        current_users = start_users
        
        for _ in range(ramp_duration_seconds // 10):
            current_users = min(max_users, current_users + ramp_step)
            
            # Execute requests
            tasks = [operation() for _ in range(int(current_users))]
            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            results.append({
                "users": int(current_users),
                "duration": duration,
                "requests_per_second": len(tasks) / duration if duration > 0 else 0
            })
            
            await asyncio.sleep(10)
        
        # Sustained load phase
        for _ in range(test_duration_seconds // 10):
            tasks = [operation() for _ in range(max_users)]
            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            results.append({
                "users": max_users,
                "duration": duration,
                "requests_per_second": len(tasks) / duration if duration > 0 else 0
            })
            
            await asyncio.sleep(10)
        
        return {
            "test_type": "ramp_up",
            "max_users": max_users,
            "total_samples": len(results),
            "avg_requests_per_second": mean([r["requests_per_second"] for r in results]),
            "results": results
        }
    
    async def spike_test(
        self,
        operation: Callable,
        baseline_users: int = 10,
        spike_users: int = 1000,
        spike_duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Spike test.
        
        Sudden increase in load to test system resilience.
        """
        results = []
        
        # Baseline
        tasks = [operation() for _ in range(baseline_users)]
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        baseline_duration = time.time() - start_time
        
        results.append({
            "phase": "baseline",
            "users": baseline_users,
            "duration": baseline_duration,
            "requests_per_second": baseline_users / baseline_duration if baseline_duration > 0 else 0
        })
        
        # Spike
        tasks = [operation() for _ in range(spike_users)]
        start_time = time.time()
        spike_results = await asyncio.gather(*tasks, return_exceptions=True)
        spike_duration = time.time() - start_time
        
        spike_errors = sum(1 for r in spike_results if isinstance(r, Exception))
        
        results.append({
            "phase": "spike",
            "users": spike_users,
            "duration": spike_duration,
            "requests_per_second": spike_users / spike_duration if spike_duration > 0 else 0,
            "errors": spike_errors,
            "error_rate": spike_errors / spike_users if spike_users > 0 else 0
        })
        
        # Recovery
        await asyncio.sleep(spike_duration_seconds)
        
        tasks = [operation() for _ in range(baseline_users)]
        start_time = time.time()
        await asyncio.gather(*tasks, return_exceptions=True)
        recovery_duration = time.time() - start_time
        
        results.append({
            "phase": "recovery",
            "users": baseline_users,
            "duration": recovery_duration,
            "requests_per_second": baseline_users / recovery_duration if recovery_duration > 0 else 0
        })
        
        return {
            "test_type": "spike",
            "spike_users": spike_users,
            "results": results
        }


class ChaosEngineer:
    """
    Chaos engineering utility.
    
    Injects failures to test system resilience.
    """
    
    def __init__(self):
        self.failures_injected = []
    
    async def inject_latency(
        self,
        operation: Callable,
        latency_ms: int = 1000,
        failure_rate: float = 0.1
    ) -> Any:
        """
        Inject latency into operation.
        
        Args:
            operation: Operation to wrap
            latency_ms: Latency to inject (milliseconds)
            failure_rate: Probability of injecting latency (0-1)
        
        Returns:
            Operation result
        """
        if random.random() < failure_rate:
            self.failures_injected.append({
                "type": "latency",
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(latency_ms / 1000)
        
        return await operation()
    
    async def inject_error(
        self,
        operation: Callable,
        error_rate: float = 0.1,
        error_message: str = "Chaos-injected error"
    ) -> Any:
        """
        Inject errors into operation.
        
        Args:
            operation: Operation to wrap
            error_rate: Probability of injecting error (0-1)
            error_message: Error message
        
        Returns:
            Operation result or raises exception
        """
        if random.random() < error_rate:
            self.failures_injected.append({
                "type": "error",
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            raise Exception(error_message)
        
        return await operation()
    
    async def inject_timeout(
        self,
        operation: Callable,
        timeout_seconds: float = 5.0,
        failure_rate: float = 0.1
    ) -> Any:
        """
        Inject timeouts into operation.
        
        Args:
            operation: Operation to wrap
            timeout_seconds: Timeout duration
            failure_rate: Probability of injecting timeout (0-1)
        
        Returns:
            Operation result or raises TimeoutError
        """
        if random.random() < failure_rate:
            self.failures_injected.append({
                "type": "timeout",
                "timeout_seconds": timeout_seconds,
                "timestamp": datetime.utcnow().isoformat()
            })
            raise asyncio.TimeoutError("Chaos-injected timeout")
        
        return await operation()
    
    def get_failure_report(self) -> Dict[str, Any]:
        """Get report of injected failures."""
        return {
            "total_failures": len(self.failures_injected),
            "failure_types": {
                "latency": sum(1 for f in self.failures_injected if f["type"] == "latency"),
                "error": sum(1 for f in self.failures_injected if f["type"] == "error"),
                "timeout": sum(1 for f in self.failures_injected if f["type"] == "timeout")
            },
            "failures": self.failures_injected
        }


class MemoryLeakDetector:
    """Detect memory leaks in long-running operations."""
    
    def __init__(self):
        self.memory_samples = []
    
    async def monitor_operation(
        self,
        operation: Callable,
        iterations: int = 100,
        sample_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Monitor operation for memory leaks.
        
        Args:
            operation: Operation to monitor
            iterations: Number of iterations
            sample_interval: Sample memory every N iterations
        
        Returns:
            Memory leak report
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            for i in range(iterations):
                await operation()
                
                if i % sample_interval == 0:
                    memory_info = process.memory_info()
                    self.memory_samples.append({
                        "iteration": i,
                        "rss_mb": memory_info.rss / 1024 / 1024,
                        "vms_mb": memory_info.vms / 1024 / 1024
                    })
            
            # Analyze trend
            if len(self.memory_samples) >= 2:
                first_sample = self.memory_samples[0]["rss_mb"]
                last_sample = self.memory_samples[-1]["rss_mb"]
                memory_growth_mb = last_sample - first_sample
                growth_rate_mb_per_iteration = memory_growth_mb / iterations
                
                # Detect leak (>1MB growth per 100 iterations)
                has_leak = growth_rate_mb_per_iteration > 0.01
                
                return {
                    "has_memory_leak": has_leak,
                    "memory_growth_mb": memory_growth_mb,
                    "growth_rate_mb_per_iteration": growth_rate_mb_per_iteration,
                    "samples": self.memory_samples
                }
            else:
                return {
                    "has_memory_leak": False,
                    "message": "Insufficient samples"
                }
        
        except ImportError:
            return {
                "has_memory_leak": False,
                "message": "psutil not available"
            }
