from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('product-list/', views.product_list, name='product_list'),
    path('product-list-all/', views.product_list_all, name='product_list_all'),
    path('products/category/<int:category_id>/', views.product_list_all_category_select, name='products_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('aszf/', views.aszf, name='aszf'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)