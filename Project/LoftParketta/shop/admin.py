from django.contrib import admin
from .models import Brand, Category, Product, News, ShippingAddress, Order, OrderItem, Document

# Az OrderItem-ek inline megjelenítése az Order admin felületén
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Ne jelenjen meg extra üres sor
    readonly_fields = ('product', 'quantity', 'unit_price', 'total_price')

# Az Order admin felületének testreszabása
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'shipping_address', 'order_date')
    list_filter = ('status', 'order_date', 'payment_method')
    search_fields = ('user__username', 'guest_user_id', 'shipping_address__recipient_name')
    readonly_fields = ('order_date', 'total_amount', 'payment_method', 'shipping_address_display')  # 'status' már nem readonly
    inlines = [OrderItemInline]  # Az OrderItem-ek megjelenítése

    # A szállítási cím részleteinek megjelenítése az Order részletekben
    def shipping_address_display(self, obj):
        if obj.shipping_address:
            return (f"Név: {obj.shipping_address.recipient_name}\n"
                    f"Cím: {obj.shipping_address.address_line1}, {obj.shipping_address.city}, "
                    f"{obj.shipping_address.postal_code}, {obj.shipping_address.country}\n"
                    f"Telefon: {obj.shipping_address.phone_number}")
        return "Nincs szállítási cím megadva"

    shipping_address_display.short_description = 'Shipping Address'

# A többi modell regisztrálása az admin felületre
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "is_active")
    list_filter = ("is_active", "is_discounted", "category", "brand")
    search_fields = ("name", "description")
    ordering = ("name",)

    fieldsets = (
        ("Készlet", {
            "fields": ("stock", "is_active")
        }),
        ("Általános információk", {
            "fields": ("name", "description", "sort_description", "category", "brand")
        }),
        ("Árazás", {
            "fields": ("price", "is_discounted", "discount_rate")
        }),
        ("Média", {
            "fields": ("image", "link")
        }),
    )


admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(News)
admin.site.register(ShippingAddress)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Document)
