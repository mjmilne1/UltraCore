"""Data Import/Export Event Publisher"""
class DataImportExportEventPublisher:
    def __init__(self):
        self.kafka_producer = None
    
    def publish_import_event(self, event):
        self._publish("data.imports", event)
    
    def publish_export_event(self, event):
        self._publish("data.exports", event)
    
    def publish_mapping_event(self, event):
        self._publish("data.mappings", event)
    
    def _publish(self, topic, event):
        pass

_publisher = None
def get_data_event_publisher():
    global _publisher
    if not _publisher:
        _publisher = DataImportExportEventPublisher()
    return _publisher
