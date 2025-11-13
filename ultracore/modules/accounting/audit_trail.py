"""
Audit Trail
Complete audit trail for all accounting activities
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class AuditTrail:
    """
    Complete audit trail for accounting
    Tracks all changes, who made them, and when
    """
    
    def __init__(self):
        self.audit_log = []
        self.log_counter = 0
    
    def log_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        user: str,
        details: Dict[str, Any],
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log audit event
        """
        
        self.log_counter += 1
        
        audit_entry = {
            "audit_id": f"AUDIT-{self.log_counter:08d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "user": user,
            "details": details,
            "before_state": before_state,
            "after_state": after_state
        }
        
        self.audit_log.append(audit_entry)
        
        return audit_entry
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """Get complete history for entity"""
        
        return [
            entry for entry in self.audit_log
            if entry["entity_type"] == entity_type
            and entry["entity_id"] == entity_id
        ]
    
    def get_user_activity(
        self,
        user: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get all activity by user"""
        
        activity = [
            entry for entry in self.audit_log
            if entry["user"] == user
        ]
        
        if start_date:
            activity = [
                e for e in activity
                if datetime.fromisoformat(e["timestamp"]) >= start_date
            ]
        
        if end_date:
            activity = [
                e for e in activity
                if datetime.fromisoformat(e["timestamp"]) <= end_date
            ]
        
        return activity
    
    def get_audit_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate audit report for period"""
        
        period_entries = [
            entry for entry in self.audit_log
            if start_date <= datetime.fromisoformat(entry["timestamp"]) <= end_date
        ]
        
        # Group by event type
        by_event_type = {}
        for entry in period_entries:
            event_type = entry["event_type"]
            if event_type not in by_event_type:
                by_event_type[event_type] = []
            by_event_type[event_type].append(entry)
        
        # Group by user
        by_user = {}
        for entry in period_entries:
            user = entry["user"]
            if user not in by_user:
                by_user[user] = []
            by_user[user].append(entry)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_events": len(period_entries),
            "by_event_type": {
                event_type: len(entries)
                for event_type, entries in by_event_type.items()
            },
            "by_user": {
                user: len(entries)
                for user, entries in by_user.items()
            },
            "entries": period_entries
        }

# Global instance
audit_trail = AuditTrail()
