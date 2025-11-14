"""
Kafka Configuration.

Configuration for Kafka producers and consumers.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class KafkaConfig:
    """Kafka configuration."""
    
    # Bootstrap servers
    bootstrap_servers: str = "localhost:9092"
    
    # Security
    security_protocol: str = "PLAINTEXT"  # PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
    sasl_mechanism: Optional[str] = None  # PLAIN, SCRAM-SHA-256, SCRAM-SHA-512
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    
    # SSL
    ssl_ca_location: Optional[str] = None
    ssl_cert_location: Optional[str] = None
    ssl_key_location: Optional[str] = None
    
    # Producer settings
    producer_acks: str = "all"  # 0, 1, all
    producer_compression_type: str = "snappy"  # none, gzip, snappy, lz4, zstd
    producer_max_in_flight_requests: int = 5
    producer_retries: int = 10
    producer_retry_backoff_ms: int = 100
    producer_linger_ms: int = 10
    producer_batch_size: int = 16384
    
    # Consumer settings
    consumer_group_id: str = "ultracore-event-consumers"
    consumer_auto_offset_reset: str = "earliest"  # earliest, latest, none
    consumer_enable_auto_commit: bool = False
    consumer_max_poll_records: int = 500
    consumer_session_timeout_ms: int = 30000
    consumer_heartbeat_interval_ms: int = 10000
    
    # Topic settings
    event_store_topic: str = "ultracore-events"
    dead_letter_topic: str = "ultracore-events-dlq"
    snapshot_topic: str = "ultracore-snapshots"
    
    # Partitions and replication
    default_partitions: int = 10
    default_replication_factor: int = 3
    
    # Schema registry (optional)
    schema_registry_url: Optional[str] = None
    
    def get_producer_config(self) -> Dict[str, any]:
        """Get producer configuration dictionary."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "security.protocol": self.security_protocol,
            "acks": self.producer_acks,
            "compression.type": self.producer_compression_type,
            "max.in.flight.requests.per.connection": self.producer_max_in_flight_requests,
            "retries": self.producer_retries,
            "retry.backoff.ms": self.producer_retry_backoff_ms,
            "linger.ms": self.producer_linger_ms,
            "batch.size": self.producer_batch_size,
        }
        
        # Add SASL config if needed
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
            config["sasl.username"] = self.sasl_username
            config["sasl.password"] = self.sasl_password
        
        # Add SSL config if needed
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_cert_location:
            config["ssl.certificate.location"] = self.ssl_cert_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location
        
        return config
    
    def get_consumer_config(self, group_id: Optional[str] = None) -> Dict[str, any]:
        """Get consumer configuration dictionary."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "security.protocol": self.security_protocol,
            "group.id": group_id or self.consumer_group_id,
            "auto.offset.reset": self.consumer_auto_offset_reset,
            "enable.auto.commit": self.consumer_enable_auto_commit,
            "max.poll.records": self.consumer_max_poll_records,
            "session.timeout.ms": self.consumer_session_timeout_ms,
            "heartbeat.interval.ms": self.consumer_heartbeat_interval_ms,
        }
        
        # Add SASL config if needed
        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism
            config["sasl.username"] = self.sasl_username
            config["sasl.password"] = self.sasl_password
        
        # Add SSL config if needed
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_cert_location:
            config["ssl.certificate.location"] = self.ssl_cert_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location
        
        return config


# Default configuration
default_config = KafkaConfig()
