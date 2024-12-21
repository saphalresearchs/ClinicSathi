from rest_framework.permissions import BasePermission

class IsRegistered(BasePermission):
    """
    Allow access only to users who are registered as a patient or doctor.
    """
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role in ['doctor', 'patient']:
            return True
        return False
