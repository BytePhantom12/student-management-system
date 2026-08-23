from django.conf import settings
from django.db import models
class AuditLog(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="audit_logs")
    action=models.CharField(max_length=80,db_index=True); object_type=models.CharField(max_length=80); object_id=models.CharField(max_length=80,blank=True)
    metadata=models.JSONField(default=dict,blank=True); timestamp=models.DateTimeField(auto_now_add=True,db_index=True)
    class Meta: ordering=["-timestamp"]

