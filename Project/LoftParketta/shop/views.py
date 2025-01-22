from django.shortcuts import render, get_object_or_404
from .models import News, Category, Product
from django.core.paginator import Paginator, EmptyPage
from decimal import Decimal
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
import json
from django.contrib.auth.decorators import login_required
#from cart.cart import Cart
from shopping_cart.models import CartItem
from django.contrib.auth.models import AnonymousUser

from django.contrib.auth.models import User
# from .forms import FormWithCaptcha
from django.contrib import messages
from datetime import datetime
from django.core.mail import EmailMessage
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail, BadHeaderError
from django.core.mail import EmailMultiAlternatives

from django.contrib.auth.models import User

cart_count = 0
def home(request):
    news_items = News.objects.all()
    category_items = Category.objects.all()
    product_items = Product.objects.filter(is_discounted=True)
    top_product_items = Product.objects.filter(is_discounted=True).order_by('id')[:10]
    for product in product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))

    for product in top_product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))

    for news in news_items:
        if news.product and news.product.is_discounted:
            news.product.discounted_price = news.product.price * (1 - (news.product.discount_rate / 100))

    # Paginator
    paginator = Paginator(product_items, 12)  # 8 kártya egy oldalon
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    actual_page = 'home'
    cart_count = get_cart_count(request)
    return render(request, 'home.html', {
        'news_items': news_items,
        'category_items': category_items,
        'page_obj': page_obj,
        'actual_page': actual_page,
        'cart_count': cart_count,
        'top_product_items': top_product_items
    })

def product_list(request):
    page_number = request.GET.get('page', 1)
    product_items = Product.objects.filter(is_discounted=True).order_by('id')
    paginator = Paginator(product_items, 16)

    try:
        products = paginator.page(page_number)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    actual_page = 'products'
    cart_count = CartItem.objects.filter(user=request.user).count()
    products_data = {
        'products': [
            {
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'discount_rate': float(product.discount_rate),
                'discounted_price': float(product.price * (1 - (product.discount_rate / 100))),
                'image_url': product.image.url if product.image else '',
                'sort_description': product.sort_description,
                'is_discounted': product.is_discounted,
            }
            for product in products
        ],
        'has_next': products.has_next(),
        'has_previous': products.has_previous(),
        'total_pages': paginator.num_pages,
        'cart_count': cart_count,
        'actual_page': actual_page
    }

    return JsonResponse(products_data)


def product_list_all(request, category_id=None):
    page_number = request.GET.get('page', 1)
    categories = request.GET.getlist('category') if category_id is None else [category_id]
    stars_filter = request.GET.getlist('stars')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    order_by = request.GET.get('order_by', 'name')  # Alapértelmezett rendezés: név
    order_dir = request.GET.get('order_dir', 'asc')  # Alapértelmezett rendezési irány: növekvő

    # Lekérjük az összes terméket
    product_items = Product.objects.all()

    # Szűrés kategóriák szerint
    if categories:
        try:
            categories = [int(c) for c in categories if c.isdigit()]
            product_items = product_items.filter(category__id__in=categories)
        except ValueError:
            pass

    # Szűrés csillagok szerint
    if stars_filter:
        try:
            stars_values = [int(star) for star in stars_filter if star.isdigit()]
            if stars_values:
                product_items = product_items.filter(rating__in=stars_values)
        except ValueError:
            pass

    # Szűrés árak szerint
    if price_min:
        try:
            price_min = float(price_min)
            product_items = product_items.filter(price__gte=price_min)
        except ValueError:
            pass

    if price_max:
        try:
            price_max = float(price_max)
            product_items = product_items.filter(price__lte=price_max)
        except ValueError:
            pass

    # Rendezés
    if order_by == 'price':
        product_items = product_items.order_by(f"{'-' if order_dir == 'desc' else ''}price")
    elif order_by == 'name':
        product_items = product_items.order_by(f"{'-' if order_dir == 'desc' else ''}name")
    else:
        product_items = product_items.order_by('id')  # Biztosítjuk, hogy mindig legyen rendezés

    # Pagináció
    paginator = Paginator(product_items, 16)  # 16 termék oldalanként

    try:
        products = paginator.page(page_number)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    for product in product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))
    # Termékadatok előkészítése JSON válaszhoz
    actual_page = 'products'
    cart_count = CartItem.objects.filter(user=request.user).count()
    products_data = {
        'products': product_items,
        'has_next': products.has_next(),
        'has_previous': products.has_previous(),
        'total_pages': paginator.num_pages,
        'cart_count': cart_count,
        'actual_page': actual_page
    }

    return JsonResponse(products_data)




def product_list_all_category_select(request, category_id=None):
    page_number = request.GET.get('page', 1)
    categories = [category_id] if category_id else request.GET.getlist('category')
    stars_filter = request.GET.getlist('stars')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    order_by = request.GET.get('order_by', 'name')
    order_dir = request.GET.get('order_dir', 'asc')

    # Alap lekérdezés
    product_items = Product.objects.all()

    # Kategóriák szűrése
    if categories:
        try:
            categories = [int(c) for c in categories if c]
            product_items = product_items.filter(category__id__in=categories)
        except ValueError:
            pass

    # Csillagok szűrése
    if stars_filter:
        try:
            stars_values = [int(star) for star in stars_filter if star.isdigit()]
            if stars_values:
                product_items = product_items.filter(rating__in=stars_values)
        except ValueError:
            pass

    # Ár szűrése
    if price_min:
        try:
            price_min = float(price_min)
            product_items = product_items.filter(price__gte=price_min)
        except ValueError:
            pass

    if price_max:
        try:
            price_max = float(price_max)
            product_items = product_items.filter(price__lte=price_max)
        except ValueError:
            pass

    # Rendezés
    order_field = {
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
        'name_desc': '-name'
    }.get(order_by, 'name')

    product_items = product_items.order_by(order_field)

    # Pagináció
    for product in product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))
    paginator = Paginator(product_items, 16)  # 16 termék oldalanként
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    actual_page = 'products'
    cart_count = get_cart_count(request)
    context = {
        'page_obj': page_obj,              # A paginált termékek
        'product_items': product_items,    # Az összes szűrt termék
        'category_items': Category.objects.all(),
        'selected_category_id': category_id,
        'cart_count': cart_count,
        'actual_page': actual_page
    }

    return render(request, 'products.html', context, )





def products(request):
    # Szűrési paraméterek lekérése
    selected_category_id = request.GET.get('category')
    stars = request.GET.get('stars')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    order_by = request.GET.get('order_by', 'name')
    order_dir = request.GET.get('order_dir', 'asc')
    cart_count = 0
    # Alapértelmezett lekérdezés
    product_items = Product.objects.all()

    # Kategória szerinti szűrés
    if selected_category_id:
        try:
            selected_category_id = int(selected_category_id)
            product_items = product_items.filter(category__id=selected_category_id)
        except ValueError:
            pass

    # Csillag szerinti szűrés
    if stars:
        product_items = product_items.filter(stars=stars)

    # Ár szerinti szűrés
    if price_min:
        product_items = product_items.filter(price__gte=price_min)
    if price_max:
        product_items = product_items.filter(price__lte=price_max)

    # Rendezés
    if order_by == 'price_asc':
        order_by_field = 'price'
    elif order_by == 'price_desc':
        order_by_field = '-price'
    elif order_by == 'name_asc':
        order_by_field = 'name'
    elif order_by == 'name_asc':
        order_by_field = '-name'
    elif order_by =='discounted':
        order_by_field = 'id'
        product_items = product_items.filter(is_discounted=True)
    else:
        order_by_field = 'id'
    product_items = product_items.order_by(order_by_field)
    for product in product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))
    # Pagináció
    paginator = Paginator(product_items, 16)  # 16 termék oldalanként
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    actual_page = 'products'
    cart_count = get_cart_count(request)
    context = {
        'page_obj': page_obj,
        'category_items': Category.objects.all(),
        'selected_category_id': selected_category_id,
        'selected_stars': stars,
        'price_min': price_min,
        'price_max': price_max,
        'selected_order_by': order_by,
        'selected_order_dir': order_dir,
        'cart_count': cart_count,
        'actual_page': actual_page
    }

    return render(request, 'products.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_price = Decimal(product.price)
    product.discounted_price = product_price * (1 - (product.discount_rate / 100))
    related_products = product.related_products.all()

    discounted_price = product_price * (1 - (product.discount_rate / 100))
    quantity = request.GET.get('quantity', 1)
    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1  # Alapértelmezett mennyiség, ha nem érvényes szám

    # Összesített ár
    total_price = discounted_price * quantity

    for _product in related_products:
        _product.discounted_price = product_price * (1 - (_product.discount_rate / 100))
    # Pagináció
    paginator = Paginator(related_products, 4)  # 4 termék oldalanként
    page_number = request.GET.get('page')

    # Ellenőrizzük, hogy a page_number egész szám-e
    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1  # Ha nem egész szám vagy None, akkor az első oldalra irányítunk

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Ha a page_number nem egész szám, akkor az első oldal jelenjen meg
        page_obj = paginator.page(1)
    except EmptyPage:
        # Ha túl nagy az oldalszám, akkor az utolsó oldalt jelenítsük meg
        page_obj = paginator.page(paginator.num_pages)

    cart_count = get_cart_count(request)
    context = {
        'product': product,
        'quantity': quantity,
        'total_price': total_price,
        'related_products': page_obj,
        'cart_count': cart_count
    }
    return render(request, 'product_detail.html', context)

from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Product, Category

def search(request):
    query = request.GET.get('q')
    selected_category_id = request.GET.get('category_id')

    # Szűrési feltételek
    filters = {}
    if query:
        filters['name__icontains'] = query
    if selected_category_id:
        filters['category_id'] = selected_category_id

    # Termékek lekérdezése a szűrők alapján
    product_items = Product.objects.filter(**filters)

    # Számítsuk ki a kedvezményes árat a találatoknál
    for product in product_items:
        product.discounted_price = product.price * (1 - (product.discount_rate / 100))

    # Pagináció a keresési találatokhoz
    paginator = Paginator(product_items, 16)  # 16 termék oldalanként
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Kontextus létrehozása a sablonhoz
    context = {
        'page_obj': page_obj,
        'category_items': Category.objects.all(),
        'selected_category_id': selected_category_id,
        'selected_stars': None,
        'price_min': None,
        'price_max': None,
        'selected_order_by': 'name',
        'selected_order_dir': 'asc',
        'cart_count': cart_count,
        'actual_page': 'products',
        'query': query,  # Ezt is átadjuk a keresési kifejezés megjelenítéséhez
    }

    return render(request, 'products.html', context)


def cookie_policy(request):
    return render(request, 'cookie_policy.html')

def aszf(request):
    return render(request, 'aszf.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def get_cart_count(request):
    cart_count = 0
    if isinstance(request.user, AnonymousUser):
        # Névtelen felhasználó esetén: kosár tárolása a session-ben
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):  # Biztosítjuk, hogy a kosár dictionary típusú legyen
            cart = {}
            request.session['cart'] = cart

        cart_items = []
        total_price = Decimal('0')

        for product_id, quantity in cart.items():
            # Ellenőrizzük, hogy a mennyiség egész szám legyen
            if not isinstance(quantity, int):
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    quantity = 0  # Hibás érték esetén kihagyjuk
                    continue

            # Töltjük a termékinformációkat
            try:
                product = get_object_or_404(Product, id=product_id)
                product_price = Decimal(product.price)
                discounted_price = product_price * (1 - (product.discount_rate / 100))
                cart_items.append({
                    'product': product,
                    'discounted_price': discounted_price,
                    'quantity': quantity,
                    'total_price': discounted_price * quantity
                })
                total_price += discounted_price * quantity
            except Product.DoesNotExist:
                continue  # Ha a termék nem található, kihagyjuk

            cart_count = len(cart_items)
    else:
        cart_count = CartItem.objects.filter(user=request.user).count()
    return cart_count