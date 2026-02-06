from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginHistory

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request)
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    last_login = LoginHistory.objects.filter(
        user=user, logout_time__isnull=True
    ).last()

    if last_login:
        last_login.logout_time = last_login.logout_time = last_login.logout_time or last_login.login_time
        last_login.save()