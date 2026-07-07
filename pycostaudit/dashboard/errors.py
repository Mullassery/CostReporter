"""
Custom exception classes and error handling for PyCostAudit API.
"""

from fastapi import HTTPException
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PyCostAuditException(Exception):
    """Base exception for PyCostAudit"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.message
        )


class ValidationError(PyCostAuditException):
    """Request validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(PyCostAuditException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(PyCostAuditException):
    """User not authorized for resource"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class NotFoundError(PyCostAuditException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(PyCostAuditException):
    """Resource conflict (e.g., duplicate)"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class InternalServerError(PyCostAuditException):
    """Internal server error"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


class InsufficientDataError(ValidationError):
    """Not enough data to perform operation"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)


class InvalidAlgorithmError(ValidationError):
    """Invalid algorithm specified"""
    def __init__(self, algorithm: str, valid_algorithms: list):
        message = f"Invalid algorithm '{algorithm}'. Must be one of: {', '.join(valid_algorithms)}"
        super().__init__(message, {"algorithm": algorithm, "valid": valid_algorithms})


class InvalidFrameworkError(ValidationError):
    """Invalid compliance framework"""
    def __init__(self, framework: str, valid_frameworks: list):
        message = f"Invalid framework '{framework}'. Must be one of: {', '.join(valid_frameworks)}"
        super().__init__(message, {"framework": framework, "valid": valid_frameworks})


def handle_exception(exception: Exception, operation: str) -> HTTPException:
    """Convert any exception to HTTP response"""
    if isinstance(exception, PyCostAuditException):
        logger.warning(f"Handled {operation}: {exception.message}", extra={"status": exception.status_code})
        return exception.to_http_exception()

    elif isinstance(exception, ValueError):
        logger.warning(f"Validation error in {operation}: {str(exception)}")
        return ValidationError(str(exception)).to_http_exception()

    elif isinstance(exception, KeyError):
        logger.warning(f"Missing key in {operation}: {str(exception)}")
        return ValidationError(f"Missing required parameter: {str(exception)}").to_http_exception()

    else:
        logger.error(f"Unexpected error in {operation}: {str(exception)}", exc_info=True)
        return InternalServerError(f"An unexpected error occurred: {type(exception).__name__}").to_http_exception()
