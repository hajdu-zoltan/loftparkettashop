from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

def send_order_status_email(order):
    if order.guest_user_id:
        url = reverse('order_status_guest', args=[order.id, order.guest_user_id])
    else:
        url = reverse('order_status', args=[order.id])

    full_url = f"{settings.SITE_URL}{url}"  # Pl. settings.SITE_URL = "https://www.example.com"

    message = f"Kedves vásárlónk!\n\nA rendelésed állapotát itt tudod megtekinteni: {full_url}\n\nKöszönjük a vásárlást!"
    send_mail(
        'Rendelés állapota',
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email if order.user else order.shipping_address.email],
        fail_silently=False,
    )
