from django.urls import path
from . import views

app_name = 'shopping_cart'

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('add_quantity/<int:item_id>/', views.add_quantity, name='add_quantity'),
    path('delete/<int:item_id>/', views.delete_from_cart, name='delete_from_cart'),
    path('quote-request/', views.QuoteRequestView.as_view(), name='quote_request'),
    path('payment/', views.payment_view, name='payment'),
    path('success/', views.success_view, name='success_page'),
    path('order-status/<uuid:code>/', views.order_status, name='order_status_uuid'),
    path('order-status/<uuid:code>/<str:guest_user_id>/', views.order_status, name='order_status_guest'),

    path('payment/start/', views.StartPaymentView.as_view(), name='start_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path("barionafter", views.barion_after, name="barion_after"),
    path("payment_status/<str:payment_id>/", views.payment_status, name="payment_status"),

    path("barionipn", views.barion_ipn, name="barion_ipn"),
    path("checkvat", views.check_vat, name="check_vat"),

]
