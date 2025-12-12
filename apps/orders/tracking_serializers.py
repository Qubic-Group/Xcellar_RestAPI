from rest_framework import serializers
from apps.orders.models import Order, TrackingHistory
from datetime import datetime


def get_status_display_message(status):
    status_messages = {
        'PENDING': 'Your parcel has been received and is being processed',
        'AVAILABLE': 'Your parcel has been prepared and is ready for pickup',
        'ASSIGNED': 'A courier has been assigned to your parcel',
        'ACCEPTED': 'Our delivery courier has picked up your parcel',
        'PICKED_UP': 'Our delivery courier has picked up your parcel',
        'IN_TRANSIT': 'The package is now in transit. You will receive the parcel shortly',
        'DELIVERED': 'You parcel was delivered successfully by the delivery man',
        'CANCELLED': 'This order has been cancelled',
    }
    return status_messages.get(status, 'Status update')


def get_status_icon(status):
    status_icons = {
        'PENDING': 'checkmark',
        'AVAILABLE': 'checkmark',
        'ASSIGNED': 'checkmark',
        'ACCEPTED': 'checkmark',
        'PICKED_UP': 'checkmark',
        'IN_TRANSIT': 'truck',
        'DELIVERED': 'checkmark',
        'CANCELLED': 'close',
    }
    return status_icons.get(status, 'checkmark')


class TrackingTimelineSerializer(serializers.Serializer):
    date = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    icon = serializers.CharField()
    message = serializers.CharField()
    location = serializers.CharField(allow_null=True, required=False)


class PublicTrackingSerializer(serializers.Serializer):
    tracking_number = serializers.CharField()
    pickup_address = serializers.CharField()
    dropoff_address = serializers.CharField()
    recipient_name = serializers.CharField()
    estimated_delivery = serializers.CharField(allow_null=True)
    current_status = serializers.CharField()
    current_status_display = serializers.CharField()
    timeline = TrackingTimelineSerializer(many=True)


def get_status_display_text(status):
    status_displays = {
        'PENDING': 'Parcel Received',
        'AVAILABLE': 'Parcel Preparation',
        'ASSIGNED': 'Pickup Confirmation',
        'ACCEPTED': 'Pickup Confirmation',
        'PICKED_UP': 'Pickup Confirmation',
        'IN_TRANSIT': 'In-Transit',
        'DELIVERED': 'Successfully Delivered',
        'CANCELLED': 'Cancelled',
    }
    return status_displays.get(status, status.replace('_', ' ').title())


def serialize_tracking_data(order):
    timeline_data = []
    
    tracking_history = order.tracking_history.all().order_by('-created_at')
    
    for history_item in tracking_history:
        status_display = get_status_display_text(history_item.status)
        message = history_item.notes if history_item.notes else get_status_display_message(history_item.status)
        
        timeline_data.append({
            'date': history_item.created_at.strftime('%d %b %Y') if history_item.created_at else '',
            'status': history_item.status,
            'status_display': status_display,
            'icon': get_status_icon(history_item.status),
            'message': message,
            'location': history_item.location if history_item.location else None,
        })
    
    estimated_delivery_str = None
    if order.estimated_delivery_time:
        estimated_delivery_str = order.estimated_delivery_time.strftime('%d %b %Y')
    
    return {
        'tracking_number': order.tracking_number,
        'pickup_address': order.pickup_address,
        'dropoff_address': order.dropoff_address,
        'recipient_name': order.recipient_name,
        'estimated_delivery': estimated_delivery_str,
        'current_status': order.status,
        'current_status_display': order.get_status_display(),
        'timeline': timeline_data,
    }

