class AppError(Exception):
    """Base exception class for all application errors"""
    status_code = 500
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response"""
        result = dict(self.payload or {})
        result['error'] = self.message
        return result


class DatabaseError(AppError):
    """Exception for database-related errors"""
    def __init__(self, message="Database error occurred", status_code=500, payload=None):
        super().__init__(message, status_code, payload)


class ResourceNotFoundError(AppError):
    """Exception for when a requested resource is not found"""
    def __init__(self, resource_type="Resource", resource_id=None, status_code=404, payload=None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, status_code, payload)


class ValidationError(AppError):
    """Exception for input validation errors"""
    def __init__(self, message="Invalid input", status_code=400, errors=None, payload=None):
        if errors:
            if payload is None:
                payload = {}
            payload['validation_errors'] = errors
        super().__init__(message, status_code, payload)


class AuthenticationError(AppError):
    """Exception for authentication failures"""
    def __init__(self, message="Authentication required", status_code=401, payload=None):
        super().__init__(message, status_code, payload)


class AuthorizationError(AppError):
    """Exception for authorization failures"""
    def __init__(self, message="Not authorized", status_code=403, payload=None):
        super().__init__(message, status_code, payload)


class RateLimitError(AppError):
    """Exception for rate limiting"""
    def __init__(self, message="Rate limit exceeded", status_code=429, payload=None):
        super().__init__(message, status_code, payload)