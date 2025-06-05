from django.db.models.signals import pre_save
from django.dispatch import receiver
from shop.models import Order, OrderItem, ShippingAddress
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

@receiver(pre_save, sender=Order)
def send_status_change_email(sender, instance, **kwargs):
    if not instance.pk:
        # Új rendelés, nincs státuszváltozás

        return

    else:
        cart_items = OrderItem.objects.filter(order=instance)
        message_to_user = render_to_string('order_status_email.html', {
            'username': instance.user.username if instance.user else 'Vendég',  # Ha vendég a felhasználó
            'order': instance,
            'cart_items': cart_items,  # Kosár tartalmának átadása
            'status_url': instance.status_url  # URL átadása az email sablonnak
        })
        email_to_user = EmailMessage(
            'Rendelés állapota frissítve',
            message_to_user,
            to=[instance.billing_email],  # Címzett email cím
        )
        email_to_user.content_subtype = 'html'  # HTML formátum
        email_to_user.send()
