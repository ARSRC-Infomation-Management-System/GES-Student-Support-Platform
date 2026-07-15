from app.exceptions.base import DomainException

class StorageException(DomainException):
    def __init__(self, message: str):
        super().__init__(code="STORAGE_ERROR", message=message, status_code=400)
