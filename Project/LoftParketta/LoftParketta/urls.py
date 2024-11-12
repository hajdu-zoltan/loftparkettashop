# myshop/urls.py
from django.urls import path, include
from django.contrib import admin
from shop.views import home
from two_factor.urls import urlpatterns as tf_urls
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from shopping_cart import  views as shopping_cart_views

urlpatterns = [
    path('', home, name='home'),


    path('shop/', include('shop.urls', namespace='shop')),  # URL-ek a 'shop' alkalmazáshoz
    path('cart/', include('shopping_cart.urls', namespace='cart')),  # URL-ek a 'shopping_cart' alkalmazáshoz
    path('admin/', admin.site.urls),
    # path('accounts/', include('allauth.urls')),
    path('captcha/', include('captcha.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='Password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="Password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='Password_reset_complete.html'), name='password_reset_complete'),
    path("/barionafter", shopping_cart_views.barion_after, name="barion_after"),
    path("payment_status/<str:payment_id>/", shopping_cart_views.payment_status, name="payment_status"),
    path("/barionipn", shopping_cart_views.barion_ipn, name="barion_ipn"),
    path("/checkvat", shopping_cart_views.check_vat, name="check_vat"),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)