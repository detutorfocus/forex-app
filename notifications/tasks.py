from celery import shared_task
from django.core.mail import send_mail

@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def send_email_task(self, subject, message, from_email, recipient_list):
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        raise self.retry(exc=e)
