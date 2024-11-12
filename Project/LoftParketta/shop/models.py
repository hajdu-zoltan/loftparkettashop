from django.db import models
from users.models import CustomUser
from django.utils import timezone
import uuid

class Brand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='brand_images/', null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    sort_description = models.TextField(null=True, blank=True)
    is_discounted = models.BooleanField(default=False)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    popularity = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_products = models.ManyToManyField('self', symmetrical=True, blank=True)

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ShippingAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_name = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    STATUS_CHOICES = [
        ('recorded', 'Rögzített'),
        ('processing', 'Feldolgozás alatt'),
        ('shipping', 'Szállítás alatt'),
        ('ready_for_pickup', 'Átvehető'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Bankkártya'),
        ('bank_transfer', 'Banki átutalás'),
        ('cash_on_delivery', 'Utánvétes'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    guest_user_id = models.CharField(max_length=36, null=True, blank=True)  # Vendégfelhasználó azonosító
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recorded')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    payed = models.BooleanField(default=False)
    barion_id = models.CharField(max_length=255, blank=True, null=True)
    BARION_STATUSES = [
        ("Prepared", "Prepared"),
        ("Started", "Started"),
        ("InProgress", "InProgress"),
        ("Canceled", "Canceled"),
        ("Expired", "Expired"),
        ("Succeeded", "Succeeded")
    ]
    barion_status = models.CharField(
        max_length=20,
        choices=BARION_STATUSES,
        null=True,
        default=None,
    )
    # Céges rendelés adatok
    is_company = models.BooleanField(default=False)  # Céges rendelés
    company_name = models.CharField(max_length=255, null=True, blank=True)  # Cég neve, ha céges rendelés
    tax_number = models.CharField(max_length=50, null=True, blank=True)  # Cég adószáma, ha céges rendelés

    # Számlázási adatok
    billing_first_name = models.CharField(max_length=100, default="N/A")  # Alapértelmezett érték
    billing_last_name = models.CharField(max_length=100, default="N/A")  # Alapértelmezett érték
    billing_email = models.EmailField(null=True, blank=True)  # Átmenetileg nullable
    billing_phone = models.CharField(max_length=15, default="N/A")  # Alapértelmezett érték
    billing_postal_code = models.CharField(max_length=10, default="N/A")  # Alapértelmezett érték
    billing_address = models.CharField(max_length=255, default="N/A")  # Alapértelmezett érték
    billing_city = models.CharField(max_length=100, default="N/A")  # Alapértelmezett érték
    billing_country = models.CharField(max_length=100, default="N/A")  # Alapértelmezett érték

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_order_items(self):
        return OrderItem.objects.filter(order=self)

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()} - Total: {self.total_amount} HUF - Payment: {self.get_payment_method_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"


class Document(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
