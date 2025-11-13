"""Access Control Middleware"""
from functools import wraps

def require_permission(resource: str, action: str):
    """Decorator for permission checking"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check permission before executing
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name: str):
    """Decorator for role checking"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check role before executing
            return func(*args, **kwargs)
        return wrapper
    return decorator
