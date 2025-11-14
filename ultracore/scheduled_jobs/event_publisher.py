"""Scheduled Jobs Event Publisher"""
class ScheduledJobsEventPublisher:
    def __init__(self):
        self.kafka_producer = None
    
    def publish_schedule_event(self, event):
        self._publish("jobs.schedules", event)
    
    def publish_job_event(self, event):
        self._publish("jobs.executions", event)
    
    def _publish(self, topic, event):
        pass

_publisher = None
def get_jobs_event_publisher():
    global _publisher
    if not _publisher:
        _publisher = ScheduledJobsEventPublisher()
    return _publisher
