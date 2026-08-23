from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from students.models import Student
from .quran import SURAH_CHOICES
class HifzProgress(models.Model):
    class Status(models.TextChoices): NOT_STARTED="not_started","Not Started"; IN_PROGRESS="in_progress","In Progress"; COMPLETED="completed","Completed"; REVISION="revision","Revision"
    class Revision(models.TextChoices): NOT_DUE="not_due","Not due"; DUE="due","Due"; CURRENT="current","Current"; COMPLETE="complete","Complete"
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="hifz_progress")
    surah=models.PositiveSmallIntegerField(choices=SURAH_CHOICES,validators=[MinValueValidator(1),MaxValueValidator(114)])
    juz=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(30)])
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.NOT_STARTED)
    progress_percentage=models.PositiveSmallIntegerField(default=0,validators=[MaxValueValidator(100)])
    date_started=models.DateField(null=True,blank=True); date_completed=models.DateField(null=True,blank=True)
    revision_status=models.CharField(max_length=20,choices=Revision.choices,default=Revision.NOT_DUE)
    teacher_notes=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["student","surah"],name="unique_student_surah")]
        ordering=["-updated_at"]
    def clean(self):
        from django.core.exceptions import ValidationError
        errors={}
        if self.date_completed and (not self.date_started or self.date_completed < self.date_started): errors["date_completed"]="Completion must be on or after start."
        if self.status==self.Status.COMPLETED and self.progress_percentage != 100: errors["progress_percentage"]="Completed progress must be 100%."
        if errors: raise ValidationError(errors)
    def save(self,*args,**kwargs): self.full_clean(); return super().save(*args,**kwargs)

