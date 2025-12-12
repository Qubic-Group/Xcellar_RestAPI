from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from apps.core.response import success_response, error_response
from apps.core.permissions import IsUser
from drf_spectacular.utils import extend_schema
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid
from PIL import Image
import logging

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def validate_image_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ', '.join(ALLOWED_IMAGE_EXTENSIONS)
        return False, f'Invalid image format. Allowed formats: {allowed}'
    
    if file.size > MAX_IMAGE_SIZE_BYTES:
        return False, f'Image size exceeds {MAX_IMAGE_SIZE_MB}MB limit'
    
    try:
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
        return True, None
    except Exception:
        return False, 'Invalid image file'


@extend_schema(
    tags=['Orders'],
    summary='Upload Parcel Image',
    description='Upload an image for a parcel/package. Returns the image URL to be used in parcel_images field when creating an order.',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'image': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Image file (JPG, PNG, GIF, WEBP, max 5MB)'
                }
            }
        }
    },
    responses={
        201: {
            'description': 'Image uploaded successfully',
            'examples': {
                'application/json': {
                    'image_url': 'http://localhost:8000/media/orders/parcels/abc123.jpg'
                }
            }
        },
        400: {'description': 'Validation error - invalid image'},
        401: {'description': 'Authentication required'},
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
@parser_classes([MultiPartParser, FormParser])
def upload_parcel_image(request):
    if 'image' not in request.FILES:
        return error_response('Image file is required', status_code=status.HTTP_400_BAD_REQUEST)
    
    image_file = request.FILES['image']
    
    is_valid, error_message = validate_image_file(image_file)
    if not is_valid:
        return error_response(error_message, status_code=status.HTTP_400_BAD_REQUEST)
    
    file_extension = os.path.splitext(image_file.name)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    upload_path = f"orders/parcels/{unique_filename}"
    
    try:
        saved_path = default_storage.save(upload_path, image_file)
        image_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        
        return success_response(
            data={'image_url': image_url},
            message='Image uploaded successfully',
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error(f"Error uploading image: {e}", exc_info=True)
        return error_response('Failed to upload image. Please try again.', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

