from django.db.models.signals import post_save
from django.dispatch import receiver
from attendance.models import Attendance
from hifz.models import HifzProgress
from students.models import Student,StudentNote
from teachers.models import Teacher
@receiver(post_save,sender=Student)
@receiver(post_save,sender=Teacher)
@receiver(post_save,sender=HifzProgress)
@receiver(post_save,sender=Attendance)
@receiver(post_save,sender=StudentNote)
def log_change(sender,instance,created,**kwargs):
    from .models import AuditLog
    user=getattr(instance,"recorded_by",None) or getattr(instance,"author",None)
    AuditLog.objects.create(user=user,action=f"{sender.__name__.lower()}_{'created' if created else 'updated'}",object_type=sender.__name__,object_id=str(instance.pk))

