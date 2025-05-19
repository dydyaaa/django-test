from rest_framework import permissions
from .models import Ad, ExchangeProposal

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if isinstance(obj, Ad):
            return obj.user == request.user
        if isinstance(obj, ExchangeProposal):
            if request.method == 'PATCH':
                return obj.ad_receiver.user == request.user
            if request.method == 'DELETE':
                return obj.ad_sender.user == request.user
        return False
