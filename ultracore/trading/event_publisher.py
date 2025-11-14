"""Trading Event Publisher"""
class TradingEventPublisher:
    def __init__(self):
        self.kafka_producer = None
    
    def publish_order_event(self, event):
        self._publish("trading.orders", event)
    
    def publish_trade_event(self, event):
        self._publish("trading.trades", event)
    
    def publish_position_event(self, event):
        self._publish("trading.positions", event)
    
    def _publish(self, topic, event):
        pass

_publisher = None
def get_trading_event_publisher():
    global _publisher
    if not _publisher:
        _publisher = TradingEventPublisher()
    return _publisher
