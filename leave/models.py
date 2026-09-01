from django.db import models
from django.conf import settings
from django.utils import timezone

class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_days_per_year = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    total_days = models.PositiveIntegerField()
    used_days = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.year}): {self.remaining_days} remaining"

    @property
    def remaining_days(self):
        return max(0, self.total_days - self.used_days)

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    applied_on = models.DateTimeField(default=timezone.now)
    decision_note = models.TextField(blank=True)
    is_deducted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.start_date} to {self.end_date}): {self.status}"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
