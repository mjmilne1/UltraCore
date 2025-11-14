"""Event Compression"""
import gzip
import json
import logging

logger = logging.getLogger(__name__)

class EventCompressor:
    """Compress event payloads."""
    
    @staticmethod
    def compress(event_data: dict) -> bytes:
        """Compress event data."""
        json_str = json.dumps(event_data)
        compressed = gzip.compress(json_str.encode())
        ratio = len(compressed) / len(json_str)
        logger.debug(f"Compressed event (ratio: {ratio:.2f})")
        return compressed
    
    @staticmethod
    def decompress(compressed_data: bytes) -> dict:
        """Decompress event data."""
        decompressed = gzip.decompress(compressed_data)
        return json.loads(decompressed.decode())
