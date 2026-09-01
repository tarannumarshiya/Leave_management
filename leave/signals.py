from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import datetime

from .models import LeaveRequest, LeaveBalance, LeaveType
from attendance.models import Attendance

@receiver(pre_save, sender=LeaveRequest)
def capture_old_status(sender, instance, **kwargs):
    """
    Capture the status before save to check if it changes in post_save.
    """
    if instance.pk:
        try:
            old_instance = LeaveRequest.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except LeaveRequest.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=LeaveRequest)
def handle_leave_approval(sender, instance, created, **kwargs):
    """
    Deducts leave balance and auto-creates Attendance records marked as 'leave'
    for the dates in the LeaveRequest upon approval. Also sends console emails.
    """
    # 1. Handle Notifications
    if created:
        # Notify manager about new application
        manager_email = instance.employee.manager.email if (instance.employee.manager and instance.employee.manager.email) else settings.DEFAULT_FROM_EMAIL
        subject = f"New Leave Request: {instance.employee.get_full_name() or instance.employee.username}"
        message = (
            f"Employee: {instance.employee.get_full_name() or instance.employee.username}\n"
            f"Leave Type: {instance.leave_type.name}\n"
            f"Dates: {instance.start_date} to {instance.end_date} ({instance.duration_days} days)\n"
            f"Reason: {instance.reason}\n"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager_email],
            fail_silently=True
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        if instance.status in ['approved', 'rejected'] and instance.status != old_status:
            # Notify employee of manager decision
            employee_email = instance.employee.email or settings.DEFAULT_FROM_EMAIL
            subject = f"Leave Request {instance.get_status_display()}"
            message = (
                f"Dear {instance.employee.get_full_name() or instance.employee.username},\n\n"
                f"Your request for {instance.leave_type.name} ({instance.start_date} to {instance.end_date}) "
                f"has been {instance.status.upper()}.\n"
                f"Decision Note: {instance.decision_note or 'None provided'}\n\n"
                f"Regards,\nLeaveFlow Management System"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee_email],
                fail_silently=True
            )

    # 2. Handle Approval Business Logic (Balance Deduction & Attendance Records)
    if instance.status == 'approved' and not instance.is_deducted:
        # Update LeaveBalance
        year = instance.start_date.year
        balance, created_bal = LeaveBalance.objects.get_or_create(
            employee=instance.employee,
            leave_type=instance.leave_type,
            year=year,
            defaults={'total_days': instance.leave_type.max_days_per_year, 'used_days': 0}
        )
        balance.used_days += instance.duration_days
        balance.save()

        # Create Attendance Records
        curr_date = instance.start_date
        while curr_date <= instance.end_date:
            att, created_att = Attendance.objects.get_or_create(
                employee=instance.employee,
                date=curr_date,
                defaults={
                    'status': 'leave',
                    'check_in_time': None,
                    'check_out_time': None,
                    'working_hours': 0.0
                }
            )
            
            if not created_att and att.status != 'leave':
                att.status = 'leave'
                att.check_in_time = None
                att.check_out_time = None
                att.working_hours = 0.0
                att.save()
                
            curr_date += datetime.timedelta(days=1)

        # Mark is_deducted = True on LeaveRequest
        LeaveRequest.objects.filter(pk=instance.pk).update(is_deducted=True)
