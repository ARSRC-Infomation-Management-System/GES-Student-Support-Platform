import io
from PIL import Image

def strip_exif_metadata(file_bytes: bytes, filename: str) -> bytes:
    """
    Strips EXIF and other device-identifying metadata from uploaded images.
    Currently acts as an MVP sanitization limit (only processing JPEG/PNG/WEBP).
    """
    lower_filename = filename.lower()
    if not lower_filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        # MVP Limit: Keep non-image files intact without attempting sanitization
        return file_bytes
    try:
        image = Image.open(io.BytesIO(file_bytes))
        clean_buffer = io.BytesIO()
        fmt = image.format if image.format else "JPEG"
        
        # Build clean image by copying raw pixel values (removes EXIF and profiles)
        data = list(image.getdata())
        clean_image = Image.new(image.mode, image.size)
        clean_image.putdata(data)
        
        clean_image.save(clean_buffer, format=fmt)
        return clean_buffer.getvalue()
    except Exception:
        # Fallback to original bytes to prevent upload crashes on parsing errors
        return file_bytes
