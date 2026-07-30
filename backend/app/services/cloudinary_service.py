import uuid
import io
from typing import Tuple, Optional
from PIL import Image, UnidentifiedImageError
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
import app.core.cloudinary  # Ensures Cloudinary SDK is configured once


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class CloudinaryService:
    @staticmethod
    def _is_configured() -> bool:
        return bool(
            settings.CLOUDINARY_CLOUD_NAME
            and settings.CLOUDINARY_API_KEY
            and settings.CLOUDINARY_API_SECRET
        )

    @classmethod
    def validate_image_file(cls, file: UploadFile, file_bytes: bytes) -> None:
        # 1. Size check
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file size exceeds maximum limit of 10 MB.",
            )

        # 2. Content-Type Header check
        content_type = (file.content_type or "").lower()
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported image format. Allowed formats: JPG, JPEG, PNG, WEBP.",
            )

        # 3. Pillow Content Verification
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image binary content format: '{image.format}'. Allowed formats: JPG, PNG, WEBP.",
                )
        except UnidentifiedImageError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file or corrupted binary content.",
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to validate image content: {str(e)}",
            )

    @classmethod
    def upload_image(cls, file: UploadFile, folder: str = "events") -> Tuple[str, str]:
        """Validates and uploads an image file to Cloudinary.
        
        Returns:
            Tuple[secure_url, public_id]
        """
        if not cls._is_configured():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloudinary storage service is not configured.",
            )

        file.file.seek(0)
        file_bytes = file.file.read()
        file.file.seek(0)

        cls.validate_image_file(file, file_bytes)

        unique_id = str(uuid.uuid4())
        public_id = f"{folder}/event_{unique_id}"

        try:
            response = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            secure_url = response.get("secure_url")
            returned_public_id = response.get("public_id", public_id)
            if not secure_url:
                raise Exception("Cloudinary upload did not return a secure URL.")
            return secure_url, returned_public_id
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload image to Cloudinary: {str(e)}",
            )

    @classmethod
    def delete_image(cls, public_id: Optional[str]) -> bool:
        """Deletes an image asset from Cloudinary using its public_id."""
        if not public_id or not cls._is_configured():
            return False
        try:
            res = cloudinary.uploader.destroy(public_id)
            return res.get("result") == "ok"
        except Exception:
            return False
