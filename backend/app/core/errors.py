from fastapi import HTTPException, status


class DomainError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict | None = None):
        detail = {"code": code, "message": message}
        if details:
            detail["details"] = details
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__("NOT_FOUND", message, status.HTTP_404_NOT_FOUND, details)


class ForbiddenError(DomainError):
    def __init__(self, message: str = "You are not authorized to perform this action", details: dict | None = None):
        super().__init__("FORBIDDEN", message, status.HTTP_403_FORBIDDEN, details)


class ConflictError(DomainError):
    def __init__(self, message: str = "Resource state conflict", details: dict | None = None):
        super().__init__("CONFLICT", message, status.HTTP_409_CONFLICT, details)


class ServiceError(DomainError):
    def __init__(self, message: str = "A dependent service is unavailable", details: dict | None = None):
        super().__init__("SERVICE_UNAVAILABLE", message, status.HTTP_503_SERVICE_UNAVAILABLE, details)


class ValidationError(DomainError):
    def __init__(self, message: str = "Invalid input data", details: dict | None = None):
        super().__init__("VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)
