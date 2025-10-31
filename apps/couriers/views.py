from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiExample
import logging

from apps.core.permissions import IsCourier
from .models import Vehicle, DriverLicense
from .serializers import VehicleSerializer, DriverLicenseSerializer

logger = logging.getLogger(__name__)


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courier vehicles.
    Only couriers can access their own vehicles.
    Supports file uploads for documents (registration, insurance, road worthiness).
    """
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsCourier]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['license_plate_number', 'manufacturer', 'model']
    ordering_fields = ['created_at', 'year_of_manufacturing', 'manufacturer']
    ordering = ['-created_at']
    
    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Return only vehicles belonging to the authenticated courier"""
        queryset = Vehicle.objects.filter(
            courier=self.request.user,
            courier__user_type='COURIER'
        )
        
        # Manual filtering via query parameters
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        ownership_condition = self.request.query_params.get('ownership_condition', None)
        if ownership_condition:
            queryset = queryset.filter(ownership_condition=ownership_condition)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    def perform_create(self, serializer):
        """Automatically assign vehicle to authenticated courier"""
        vehicle = serializer.save(courier=self.request.user)
        logger.info(f"Vehicle created: {vehicle.license_plate_number} for courier {self.request.user.email}")
    
    def perform_update(self, serializer):
        """Log vehicle updates"""
        vehicle = serializer.save()
        logger.info(f"Vehicle updated: {vehicle.license_plate_number} by courier {self.request.user.email}")
    
    def perform_destroy(self, instance):
        """Soft delete vehicle by setting is_active=False"""
        instance.is_active = False
        instance.save()
        logger.info(f"Vehicle deactivated: {instance.license_plate_number} by courier {self.request.user.email}")
    
    @extend_schema(
        tags=['Couriers'],
        summary='List Vehicles',
        description='List all vehicles belonging to the authenticated courier. Supports filtering and search.',
        responses={
            200: VehicleSerializer(many=True),
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Only couriers allowed'},
        },
    )
    def list(self, request, *args, **kwargs):
        """List all vehicles for authenticated courier"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Create Vehicle',
        description='Create a new vehicle for the authenticated courier.',
        request=VehicleSerializer,
        responses={
            201: VehicleSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Only couriers allowed'},
        },
        examples=[
            OpenApiExample(
                'Create Vehicle Request',
                value={
                    'vehicle_type': 'MOTORCYCLE',
                    'ownership_condition': 'OWNED',
                    'manufacturer': 'Honda',
                    'model': 'CBR 600',
                    'year_of_manufacturing': 2020,
                    'license_plate_number': 'ABC-1234',
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """Create a new vehicle"""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Get Vehicle',
        description='Retrieve a specific vehicle by ID. Only accessible by the vehicle owner.',
        responses={
            200: VehicleSerializer,
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific vehicle"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Partial Update Vehicle',
        description='Partially update a vehicle. Only accessible by the vehicle owner. Supports document uploads (registration, insurance, road worthiness).',
        request=VehicleSerializer,
        responses={
            200: VehicleSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a vehicle"""
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Update Vehicle',
        description='Update a vehicle. Only accessible by the vehicle owner. Supports document uploads (registration, insurance, road worthiness).',
        request=VehicleSerializer,
        responses={
            200: VehicleSerializer,
            400: {'description': 'Validation error'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    def update(self, request, *args, **kwargs):
        """Update a vehicle"""
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Delete Vehicle',
        description='Delete (deactivate) a vehicle. Only accessible by the vehicle owner.',
        responses={
            204: {'description': 'Vehicle deleted successfully'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete (soft delete) a vehicle"""
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Activate Vehicle',
        description='Activate a vehicle. Only accessible by the vehicle owner.',
        responses={
            200: VehicleSerializer,
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a vehicle"""
        vehicle = self.get_object()
        vehicle.is_active = True
        vehicle.save()
        serializer = self.get_serializer(vehicle)
        logger.info(f"Vehicle activated: {vehicle.license_plate_number}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Couriers'],
        summary='Deactivate Vehicle',
        description='Deactivate a vehicle. Only accessible by the vehicle owner.',
        responses={
            200: VehicleSerializer,
            401: {'description': 'Authentication required'},
            403: {'description': 'Forbidden - Vehicle does not belong to you'},
            404: {'description': 'Vehicle not found'},
        },
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a vehicle"""
        vehicle = self.get_object()
        vehicle.is_active = False
        vehicle.save()
        serializer = self.get_serializer(vehicle)
        logger.info(f"Vehicle deactivated: {vehicle.license_plate_number}")
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Couriers'],
    summary='Get Driver License',
    description='Retrieve driver license information for the authenticated courier. Returns empty response if license not created yet.',
    responses={
        200: {
            'description': 'Driver license data or empty response',
            'examples': {
                'application/json': {
                    'id': 1,
                    'license_number': 'DL123456',
                    'issue_date': '2020-01-15',
                    'expiry_date': '2025-01-15',
                    'issuing_authority': 'DMV',
                    'front_page_url': 'http://localhost:8000/media/licenses/documents/front/license_1.jpg',
                    'back_page_url': 'http://localhost:8000/media/licenses/documents/back/license_1.jpg',
                    'is_expired': False,
                }
            }
        },
        401: {'description': 'Authentication required'},
        403: {'description': 'Forbidden - Only couriers allowed'},
    },
    examples=[
        OpenApiExample(
            'Driver License Response',
            value={
                'id': 1,
                'license_number': 'DL123456',
                'issue_date': '2020-01-15',
                'expiry_date': '2025-01-15',
                'issuing_authority': 'DMV',
                'front_page_url': 'http://localhost:8000/media/licenses/documents/front/license_1.jpg',
                'back_page_url': 'http://localhost:8000/media/licenses/documents/back/license_1.jpg',
                'is_expired': False,
            },
            response_only=True,
        ),
    ],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCourier])
@ratelimit(key='user', rate='100/h', method='GET')
def driver_license(request):
    """
    Get driver license for authenticated courier.
    GET /api/v1/couriers/license/
    """
    try:
        courier_profile = request.user.courier_profile
        license_obj = courier_profile.driver_license
        serializer = DriverLicenseSerializer(license_obj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except AttributeError:
        # License not created yet (OneToOne relationship doesn't exist)
        # Django raises RelatedObjectDoesNotExist which is a subclass of AttributeError
        return Response(
            {
                'message': 'Driver license not registered yet. Use PUT/PATCH to create.',
                'license': None
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        # Fallback exception handling
        logger.error(f"Error retrieving driver license for courier {request.user.email}: {e}")
        return Response(
            {
                'message': 'Driver license not registered yet. Use PUT/PATCH to create.',
                'license': None
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Couriers'],
    summary='Create/Update Driver License',
    description='Create or update driver license information for the authenticated courier. Supports file uploads. Auto-creates license if it doesn\'t exist.',
    request=DriverLicenseSerializer,
    responses={
        200: {
            'description': 'Driver license created/updated successfully',
            'examples': {
                'application/json': {
                    'message': 'Driver license updated successfully',
                    'license': {
                        'id': 1,
                        'license_number': 'DL123456',
                        'issue_date': '2020-01-15',
                        'expiry_date': '2025-01-15',
                        'issuing_authority': 'DMV',
                    }
                }
            }
        },
        400: {'description': 'Validation error'},
        401: {'description': 'Authentication required'},
        403: {'description': 'Forbidden - Only couriers allowed'},
    },
    examples=[
        OpenApiExample(
            'Update Driver License Request',
            value={
                'license_number': 'DL123456',
                'issue_date': '2020-01-15',
                'expiry_date': '2025-01-15',
                'issuing_authority': 'DMV',
                'front_page': '<file>',
                'back_page': '<file>',
            },
            request_only=True,
        ),
    ],
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsCourier])
@ratelimit(key='user', rate='10/h', method=['PUT', 'PATCH'])
def update_driver_license(request):
    """
    Create or update driver license for authenticated courier.
    PUT/PATCH /api/v1/couriers/license/update/
    """
    from django.db import transaction
    
    courier_profile = request.user.courier_profile
    is_create = False
    license_obj = None
    
    try:
        license_obj = courier_profile.driver_license
        serializer = DriverLicenseSerializer(
            license_obj,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
    except AttributeError:
        # License doesn't exist, create new one (OneToOne relationship doesn't exist)
        # Django raises RelatedObjectDoesNotExist which is a subclass of AttributeError
        is_create = True
        serializer = DriverLicenseSerializer(
            data=request.data,
            context={'request': request}
        )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Handle file deletions if replacing (save old file references before saving)
            old_front_page = None
            old_back_page = None
            
            if not is_create and license_obj:
                old_front_page = license_obj.front_page
                old_back_page = license_obj.back_page
            
            # Save license, automatically assign to courier_profile
            license_obj = serializer.save(courier_profile=courier_profile)
            
            # Delete old files if new ones were uploaded (after saving new files)
            if 'front_page' in serializer.validated_data and old_front_page:
                old_front_page.delete(save=False)
            if 'back_page' in serializer.validated_data and old_back_page:
                old_back_page.delete(save=False)
            
        logger.info(f"Driver license {'created' if is_create else 'updated'} for courier {request.user.email}")
        
        response_serializer = DriverLicenseSerializer(license_obj, context={'request': request})
        return Response(
            {
                'message': f'Driver license {"created" if is_create else "updated"} successfully',
                'license': response_serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Failed to update driver license for courier {request.user.email}: {e}")
        return Response(
            {'error': 'Failed to update driver license. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

