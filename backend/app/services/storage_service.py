import os
import uuid
from fastapi import UploadFile
from app.core.config import settings
from app.utils.metadata import strip_exif_metadata
from app.exceptions.storage import StorageException

class StorageService:
    @staticmethod
    async def save_file(upload_file: UploadFile) -> dict:
        try:
            file_content = await upload_file.read()
            
            # File validation (e.g. max size limit 10MB)
            max_size_bytes = 10 * 1024 * 1024
            if len(file_content) > max_size_bytes:
                raise StorageException("File exceeds maximum limit of 10MB.")
            
            # Metadata removal for privacy (EXIF stripping)
            clean_content = strip_exif_metadata(file_content, upload_file.filename)
            
            # Generate unique disk filename
            file_uuid = uuid.uuid4().hex
            file_ext = os.path.splitext(upload_file.filename)[1]
            save_filename = f"{file_uuid}{file_ext}"
            save_path = os.path.join(settings.UPLOAD_DIR, save_filename)
            
            # Write to storage provider
            with open(save_path, "wb") as f:
                f.write(clean_content)
                
            return {
                "filename": upload_file.filename,
                "file_path": save_path,
                "file_size": len(clean_content),
                "content_type": upload_file.content_type
            }
        except Exception as e:
            if isinstance(e, StorageException):
                raise e
            raise StorageException(f"File upload failed: {str(e)}")
