from rest_framework.permissions import BasePermission


class IsUser(BasePermission):
    """
    Permission class to check if user is a regular customer.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'USER'
        )


class IsCourier(BasePermission):
    """
    Permission class to check if user is a courier.
    Can also check object-level permissions for courier-owned resources.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'COURIER'
        )
    
    def has_object_permission(self, request, view, obj):
        """Check if courier owns the object"""
        # Check if object has a courier attribute
        if hasattr(obj, 'courier'):
            return obj.courier == request.user
        # If no courier attribute, allow (for viewsets that filter queryset)
        return True


class IsUserOrCourier(BasePermission):
    """
    Permission class to allow both user types.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type in ['USER', 'COURIER']
        )
