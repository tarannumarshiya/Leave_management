from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half-day', 'Half Day'),
        ('leave', 'On Leave'),
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField(default=timezone.localdate)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        if self.check_in_time and self.check_out_time:
            if self.check_out_time <= self.check_in_time:
                raise ValidationError("Check-out time must be after check-in time.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.check_in_time and self.check_out_time:
            # Combine date and time to calculate duration
            dt_in = datetime.datetime.combine(self.date, self.check_in_time)
            dt_out = datetime.datetime.combine(self.date, self.check_out_time)
            if dt_out > dt_in:
                diff = dt_out - dt_in
                self.working_hours = round(diff.total_seconds() / 3600.0, 2)
            else:
                self.working_hours = 0.0
        else:
            self.working_hours = 0.0
        super().save(*args, **kwargs)
