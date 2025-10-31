from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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

