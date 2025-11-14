"""Fee Event Publisher"""
class FeeEventPublisher:
    def __init__(self):
        self.kafka_producer = None
    
    def publish_fee_structure_event(self, event):
        self._publish("fees.structures", event)
    
    def publish_fee_charge_event(self, event):
        self._publish("fees.charges", event)
    
    def publish_subscription_event(self, event):
        self._publish("fees.subscriptions", event)
    
    def publish_promotion_event(self, event):
        self._publish("fees.promotions", event)
    
    def _publish(self, topic, event):
        pass

_publisher = None
def get_fee_event_publisher():
    global _publisher
    if not _publisher:
        _publisher = FeeEventPublisher()
    return _publisher
