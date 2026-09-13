from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_IMAGE_DIR = PROJECT_ROOT / "uploads" / "profile-images"

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
MAX_IMAGE_SIZE = (512, 512)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_profile_image(
    upload_file: UploadFile,
    customer_id: str,
) -> str:
    if upload_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            "Only JPG, PNG, and WebP profile images are allowed."
        )

    contents = await upload_file.read()

    if not contents:
        raise ValueError("Profile image is empty.")

    if len(contents) > MAX_UPLOAD_SIZE:
        raise ValueError(
            "Profile image must be 5 MB or smaller."
        )

    try:
        from io import BytesIO

        image = Image.open(BytesIO(contents))
        image = ImageOps.exif_transpose(image)
        image.verify()

        image = Image.open(BytesIO(contents))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception as exc:
        raise ValueError(
            "The uploaded file is not a valid image."
        ) from exc

    image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

    PROFILE_IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{customer_id}_{uuid4().hex}.webp"
    destination = PROFILE_IMAGE_DIR / filename

    image.save(
        destination,
        format="WEBP",
        quality=85,
        optimize=True,
    )

    return f"/uploads/profile-images/{filename}"
