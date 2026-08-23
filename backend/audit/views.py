from rest_framework.mixins import ListModelMixin,RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from common import IsAdmin
from .models import AuditLog
from .serializers import AuditSerializer
class AuditViewSet(ListModelMixin,RetrieveModelMixin,GenericViewSet):
    permission_classes=[IsAdmin]; serializer_class=AuditSerializer; queryset=AuditLog.objects.select_related("user"); filterset_fields=("action","object_type","user")

