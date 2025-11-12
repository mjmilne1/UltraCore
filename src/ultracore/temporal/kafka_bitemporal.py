from datetime import datetime, timezone
from dataclasses import dataclass
import uuid

class KafkaEventStream:
    async def write_event(self, event, domain='transactions'):
        return {
            'event_id': str(uuid.uuid4()),
            'kafka_offset': 12345,
            'partition': 0,
            'timestamp': datetime.now().timestamp()
        }

@dataclass
class BitemporalRecord:
    business_time: datetime
    system_time: datetime
    data: dict
    version: int
    kafka_offset: int

class TemporalLedger:
    def __init__(self):
        self.ledger = []
        self.indexes = {}
        self.kafka_stream = KafkaEventStream()
        
    async def record_event(self, event):
        kafka_result = await self.kafka_stream.write_event(event)
        
        record = BitemporalRecord(
            business_time=datetime.fromisoformat(event.get('business_time', datetime.now().isoformat())),
            system_time=datetime.now(timezone.utc),
            data=event,
            version=len(self.ledger) + 1,
            kafka_offset=kafka_result['kafka_offset']
        )
        
        self.ledger.append(record)
        return kafka_result['event_id']
    
    def as_of(self, timestamp, account_id=None):
        events = [r for r in self.ledger if r.business_time <= timestamp]
        
        balance = 0
        for event in events:
            if event.data.get('type') == 'deposit':
                balance += event.data.get('amount', 0)
            elif event.data.get('type') == 'withdrawal':
                balance -= event.data.get('amount', 0)
        
        return {
            'as_of_time': timestamp.isoformat(),
            'balance': balance,
            'event_count': len(events)
        }
