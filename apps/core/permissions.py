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
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'COURIER'
        )


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

