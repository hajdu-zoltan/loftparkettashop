from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import AnonymousUser
from decimal import Decimal
from django.http import HttpResponseNotAllowed
from django.views import View
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import CartItem
from shop.models import Order, OrderItem, ShippingAddress
from shop.models import Product
from shop.forms import QuoteRequestForm, PaymentForm

from .barion import create_payment, get_payment_status
from .szamlazzhu_module import SzamlazzInfo, SzamlazzItem, SzamlazzhuModule

import logging
import uuid
import os
import requests
import yaml
logger = logging.getLogger(__name__)
cart_count = 0



def view_cart(request):
    vat_rate = Decimal('0.27')  # ÁFA kulcs
    vat_amount = Decimal('0')
    total_out_vat = Decimal('0')
    total_price = Decimal('0')
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
        if total_price > 0:
            vat_amount = total_price * vat_rate
            total_out_vat = total_price - vat_amount
        else:
            vat_amount = Decimal('0')
            total_out_vat = Decimal('0')

    else:
        # Bejelentkezett felhasználó esetén
        cart_items = CartItem.objects.filter(user=request.user)
        total_price = Decimal('0')

        for item in cart_items:
            product = item.product
            product_price = Decimal(product.price)
            discounted_price = product_price * (1 - (product.discount_rate / 100))
            total_price += discounted_price * item.quantity

        vat_amount = total_price * vat_rate
        total_out_vat = total_price - vat_amount
        cart_count = cart_items.count()

        # Pass discounted prices to the template
        cart_items = [
            {
                'id': item.id,
                'product': item.product,
                'discounted_price': Decimal(item.product.price) * (1 - (item.product.discount_rate / 100)),
                'quantity': item.quantity,
                'total_price': Decimal(item.product.price) * (1 - (item.product.discount_rate / 100)) * item.quantity
            }
            for item in cart_items
        ]

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count,
        'vat_amount': vat_amount,
        'vat_rate': vat_rate,
        'total_out_vat': total_out_vat
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(product=product, user=request.user)
        cart_item.quantity += 1
        cart_item.save()
        cart_count = CartItem.objects.filter(user=request.user).count()
    else:
        # Névtelen felhasználó esetén, kosár tárolása a session-ben
        cart = request.session.get('cart', {})
        if not isinstance(cart, dict):  # Ellenőrizzük, hogy a kosár dictionary
            cart = {}
        if str(product_id) in cart:
            cart[str(product_id)] += 1
        else:
            cart[str(product_id)] = 1
        request.session['cart'] = cart
        cart_count = sum(cart.values())

    response_data = {
        'status': 'success',
        'cart_count': cart_count,
    }
    return JsonResponse(response_data)

def remove_from_cart(request, item_id):
    """
    Termék eltávolítása a kosárból (mennyiség csökkentése vagy teljes törlés).
    """
    if request.user.is_authenticated:
        # Bejelentkezett felhasználó esetén
        try:
            # Megkeressük a kosárban lévő terméket a felhasználóhoz rendelve
            cart_item = CartItem.objects.get(product_id=item_id, user=request.user)

            if cart_item.quantity > 1:
                # Ha a mennyiség nagyobb, mint 1, csökkentjük
                cart_item.quantity -= 1
                cart_item.save()
                logger.info(f"Decreased quantity for product {item_id} in user {request.user}'s cart.")
            else:
                # Ha a mennyiség 1 vagy kevesebb, töröljük a terméket a kosárból
                cart_item.delete()
                logger.info(f"Removed product {item_id} from user {request.user}'s cart.")
        except CartItem.DoesNotExist:
            logger.warning(f"CartItem with product id {item_id} does not exist for user {request.user}.")
    else:
        # Névtelen felhasználó esetén, kosár tárolása a session-ben
        cart = request.session.get('cart', {})

        if str(item_id) in cart:
            # Ha a mennyiség nagyobb, mint 1, csökkentjük
            if cart[str(item_id)] > 1:
                cart[str(item_id)] -= 1
                logger.info(f"Decreased quantity for product {item_id} in session cart.")
            else:
                # Ha a mennyiség 1 vagy kevesebb, töröljük a terméket a kosárból
                del cart[str(item_id)]
                logger.info(f"Removed product {item_id} from session cart.")

            # Frissítjük a session-t
            request.session['cart'] = cart
        else:
            logger.warning(f"Product with id {item_id} not found in session cart.")

    # Visszairányítjuk a kosár nézetéhez
    return redirect('shopping_cart:view_cart')

def delete_from_cart(request, item_id):
    """
    Termék teljes eltávolítása a kosárból.
    """
    if request.user.is_authenticated:
        # Bejelentkezett felhasználó esetén
        try:
            # Kosár elem megkeresése és törlése
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            logger.info(f"Product with id {item_id} deleted from cart for user {request.user}.")
        except CartItem.DoesNotExist:
            logger.error(f"CartItem with id {item_id} does not exist for user {request.user}.")
    else:
        # Névtelen felhasználó esetén, kosár tárolása a session-ben
        cart = request.session.get('cart', {})
        if str(item_id) in cart:
            # Termék teljes eltávolítása a kosárból
            del cart[str(item_id)]
            request.session['cart'] = cart
            logger.info(f"Product with id {item_id} deleted from session cart.")
        else:
            logger.error(f"Product with id {item_id} not found in session cart.")

    # Visszairányítás a kosár nézetéhez
    return redirect('shopping_cart:view_cart')

def add_quantity(request, item_id):
    """
    Termék mennyiségének növelése a kosárban.
    """
    logger.info(f"Adding quantity for item_id: {item_id}")
    if request.method == 'POST':
        try:
            # A POST kéréssel érkezett mennyiség lekérdezése (alapértelmezett 1)
            add_quantity = int(request.POST.get('quantity', 1))
            logger.info(f"Quantity to add: {add_quantity}")

            if add_quantity <= 0:
                raise ValueError("The quantity to add must be a positive integer.")

            if request.user.is_authenticated:
                # Authentikált felhasználók esetén
                cart_item, created = CartItem.objects.get_or_create(
                    product_id=item_id,
                    user=request.user,
                    defaults={'quantity': 0}
                )
                cart_item.quantity += add_quantity
                cart_item.save()
                logger.info(f"Updated quantity for item_id: {item_id} to {cart_item.quantity}")
                cart_count = CartItem.objects.filter(user=request.user).count()

            else:
                # Névtelen felhasználók kosarának frissítése a session-ben
                cart = request.session.get('cart', {})
                current_quantity = cart.get(str(item_id), 0)
                cart[str(item_id)] = current_quantity + add_quantity
                request.session['cart'] = cart
                cart_count = sum(cart.values())
                logger.info(f"Updated session cart for item_id: {item_id}, quantity: {cart[str(item_id)]}")

            response_data = {
                'status': 'success',
                'cart_count': cart_count,
            }
            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Error adding quantity for item_id {item_id}: {e}")
            response_data = {
                'status': 'error',
                'message': str(e),
            }
            return JsonResponse(response_data, status=400)

    else:
        logger.warning("Invalid request method. Only POST is allowed.")
        return HttpResponseNotAllowed(['POST'])
def update_quantity(request, item_id):
    logger.info(f"Received request to update quantity for item_id: {item_id}")
    if request.method == 'POST':
        try:
            # Új mennyiség lekérése
            new_quantity = int(request.POST.get('quantity', 1))
            logger.info(f"New quantity received: {new_quantity}")

            # Meglévő mennyiség lekérése
            if request.user.is_authenticated:
                # Authentikált felhasználók esetén a kosár lekérdezése
                cart_item = CartItem.objects.filter(user=request.user, product_id=item_id).first()
                current_quantity = cart_item.quantity if cart_item else 0
                logger.info(f"Current quantity in cart: {current_quantity}")

                if new_quantity > current_quantity:
                    # Ha az új mennyiség nagyobb, akkor hozzáadjuk a különbséget
                    for _ in range(new_quantity - current_quantity):
                        add_to_cart(request, item_id)
                elif new_quantity < current_quantity:
                    # Ha az új mennyiség kisebb, akkor eltávolítjuk a különbséget
                    for _ in range(current_quantity - new_quantity):
                        remove_from_cart(request, item_id)  # Tegyük fel, hogy van egy remove_from_cart függvényed
            else:
                # Névtelen felhasználók esetén a session-ből szedjük le a kosarat
                cart = request.session.get('cart', {})
                if not isinstance(cart, dict):
                    cart = {}

                current_quantity = cart.get(str(item_id), 0)
                logger.info(f"Current quantity in session cart: {current_quantity}")

                if new_quantity > current_quantity:
                    # Ha az új mennyiség nagyobb, hozzáadjuk a különbséget
                    cart[str(item_id)] = current_quantity + (new_quantity - current_quantity)
                elif new_quantity < current_quantity:
                    # Ha az új mennyiség kisebb, csökkentjük a különbséget
                    cart[str(item_id)] = max(0, current_quantity - (current_quantity - new_quantity))

                request.session['cart'] = cart

            return redirect('shopping_cart:view_cart')

        except Exception as e:
            logger.error(f"Error updating quantity: {e}")
            return HttpResponse("Internal Server Error", status=500)

    else:
        return HttpResponseNotAllowed(['POST'])


class QuoteRequestView(View):
    def get(self, request):
        form = QuoteRequestForm()
        cart_items = []

        if isinstance(request.user, AnonymousUser):
            # Névtelen felhasználó esetén: kosár tárolása a session-ben
            cart = request.session.get('cart', {})
            if not isinstance(cart, dict):
                cart = {}
            for product_id, quantity in cart.items():
                product = get_object_or_404(Product, id=product_id)
                product_price = Decimal(product.price)
                discounted_price = product_price * (1 - (product.discount_rate / 100))
                cart_items.append({
                    'product': product,
                    'discounted_price': discounted_price,
                    'quantity': quantity,
                    'total_price': discounted_price * quantity
                })
        else:
            # Bejelentkezett felhasználó esetén
            cart_items_queryset = CartItem.objects.filter(user=request.user)
            for item in cart_items_queryset:
                product = item.product
                product_price = Decimal(product.price)
                discounted_price = product_price * (1 - (product.discount_rate / 100))
                cart_items.append({
                    'product': product,
                    'discounted_price': discounted_price,
                    'quantity': item.quantity,
                    'total_price': discounted_price * item.quantity
                })

        return render(request, 'quote_request.html', {'form': form, 'cart_items': cart_items})

    def post(self, request):
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            # Kosár termékeinek összegyűjtése
            cart_items = []
            if isinstance(request.user, AnonymousUser):
                cart = request.session.get('cart', {})
                for product_id, quantity in cart.items():
                    product = get_object_or_404(Product, id=product_id)
                    discounted_price = product.price * (1 - (product.discount_rate / 100))
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'discounted_price': discounted_price,
                        'total_price': discounted_price * quantity,
                    })
            else:
                cart_items_queryset = CartItem.objects.filter(user=request.user)
                for item in cart_items_queryset:
                    product = item.product
                    discounted_price = product.price * (1 - (product.discount_rate / 100))
                    cart_items.append({
                        'product': product,
                        'quantity': item.quantity,
                        'discounted_price': discounted_price,
                        'total_price': discounted_price * item.quantity,
                    })


            # Email küldés az ügyfélnek (HTML sablon)
            message_to_customer = render_to_string("customer_email.html", {
                'username': form.cleaned_data['name'],
                'cart_items': cart_items  # Kosár elemek hozzáadása az ügyfél emailhez is
            })

            email_to_customer = EmailMessage(
                'Árajánlat Kérés',
                message_to_customer,
                to=[form.cleaned_data['email']]
            )
            email_to_customer.content_subtype = 'html'  # Az email típusa HTML legyen
            email_to_customer.send()

            # Email küldés a cégnek (HTML sablon)
            message_to_company = render_to_string("company_email.html", {
                'username': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'message': form.cleaned_data['message'],
                'shipping_address': form.cleaned_data['shipping_address'],
                'shipping_country': form.cleaned_data['shipping_country'],
                'shipping_postal_code': form.cleaned_data['shipping_postal_code'],
                'shipping_city': form.cleaned_data['shipping_city'],
                'cart_items': cart_items  # Kosár termékeinek átadása a cég emailhez
            })

            email_to_company = EmailMessage(
                'Új árajánlat kérés érkezett',
                message_to_company,
                to=['hajduzoltan2019@gmail.com'],  # A cég email címe
            )
            email_to_company.content_subtype = 'html'  # Az email típusa HTML legyen
            email_to_company.send()

            messages.success(request, 'Árajánlat kérés sikeresen elküldve!')
            return render(request, 'quote_request.html')

        else:
            # Ha a form nem érvényes, újra rendereld a template-et a hibákkal
            cart_items = []  # Itt újra be kell állítani a cart_items-t, hogy a GET és POST esetek hasonlóan működjenek

            if isinstance(request.user, AnonymousUser):
                cart = request.session.get('cart', {})
                if not isinstance(cart, dict):
                    cart = {}
                for product_id, quantity in cart.items():
                    product = get_object_or_404(Product, id=product_id)
                    product_price = Decimal(product.price)
                    discounted_price = product_price * (1 - (product.discount_rate / 100))
                    cart_items.append({
                        'product': product,
                        'discounted_price': discounted_price,
                        'quantity': quantity,
                        'total_price': discounted_price * quantity
                    })
            else:
                cart_items_queryset = CartItem.objects.filter(user=request.user)
                for item in cart_items_queryset:
                    product = item.product
                    product_price = Decimal(product.price)
                    discounted_price = product_price * (1 - (product.discount_rate / 100))
                    cart_items.append({
                        'product': product,
                        'discounted_price': discounted_price,
                        'quantity': item.quantity,
                        'total_price': discounted_price * item.quantity
                    })

            return render(request, 'quote_request.html', {'form': form, 'cart_items': cart_items})



def payment_view(request):
    shipping_address =""
    cart_items = []
    User = get_user_model()  # User modell betöltése
    total_price = Decimal('0')
    cart_count = 0
    vat_amount = Decimal('0')
    total_out_vat = Decimal('0')
    cart_count = 0
    total_price = Decimal('0')

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():

            shipping_cost = 0
            # Szállítási adatok kinyerése
            shipping_first_name = form.cleaned_data['shipping_first_name']
            shipping_last_name = form.cleaned_data['shipping_last_name']
            shipping_postal_code = form.cleaned_data['shipping_postal_code']
            shipping_method = form.cleaned_data['shipping_method']
            shipping_address = form.cleaned_data['shipping_address']
            if (int(shipping_postal_code) >= 6700 or int(shipping_postal_code) <= 6791) or shipping_method == "store_pickup":

                if shipping_method == "store_pickup":
                    shipping_address = "LoftParketta(Szeged, Kossuth Lajos sgrt. 49-51, 6724)"
                elif shipping_method == "home_delivery":
                    shipping_cost = 10000

                shipping_city = form.cleaned_data['shipping_city']
                shipping_country = form.cleaned_data['shipping_country']

                is_company = form.cleaned_data['is_company']
                company_name = form.cleaned_data['company_name']
                tax_number = form.cleaned_data['tax_number']

                # Számlázási adatok kinyerése
                billing_first_name = form.cleaned_data['billing_first_name']
                billing_last_name = form.cleaned_data['billing_last_name']
                billing_email = form.cleaned_data['billing_email']
                billing_phone = form.cleaned_data['billing_phone']
                billing_postal_code = form.cleaned_data['billing_postal_code']
                billing_address = form.cleaned_data['billing_address']
                billing_city = form.cleaned_data['billing_city']
                billing_country = form.cleaned_data['billing_country']

                payment_method = form.cleaned_data['payment_method']
                # Kosár adatok kinyerése
                cart = request.session.get('cart', {})
                total_price = Decimal('0')
                cart_items = []

                if isinstance(request.user, AnonymousUser):
                    for product_id, quantity in cart.items():
                        product = get_object_or_404(Product, id=product_id)
                        product_price = Decimal(product.price)
                        discounted_price = product_price * (1 - (product.discount_rate / 100))
                        total_price += discounted_price * quantity
                        cart_items.append({
                            'product': product,
                            'quantity': quantity,
                            'discounted_price': discounted_price,
                            'total_price': discounted_price * quantity
                        })
                else:
                    cart_items = CartItem.objects.filter(user=request.user)
                    total_price = Decimal('0')
                    for item in cart_items:
                        product = item.product
                        product_price = Decimal(product.price)
                        discounted_price = product_price * (1 - (product.discount_rate / 100))
                        total_price += discounted_price * item.quantity

                # Új rendelés létrehozása
                user = request.user if request.user.is_authenticated else None
                guest_user_id = str(uuid.uuid4()) if not user else None  # Vendégfelhasználó azonosító generálása

                # Szállítási cím létrehozása
                shipping_address_instance = ShippingAddress.objects.create(
                    user=user,  # Felhasználó, ha be van jelentkezve
                    recipient_name=f"{shipping_first_name} {shipping_last_name}",
                    address_line1=shipping_address,
                    city=shipping_city,
                    state='',  # Ha van állam mező, állítsd be
                    postal_code=shipping_postal_code,
                    country=shipping_country,
                    phone_number=billing_phone  # A telefonszám a számlázásból
                )

                # Új rendelés létrehozása
                order = Order.objects.create(
                    user=user,
                    guest_user_id=guest_user_id,  # Vendégfelhasználó azonosító
                    total_amount=total_price+shipping_cost,
                    shipping_address=shipping_address_instance,
                    shipping_method=shipping_method,
                    payment_method=payment_method,
                    billing_email=billing_email,
                    billing_phone=billing_phone,
                    billing_first_name=billing_first_name,
                    billing_last_name=billing_last_name,
                    billing_postal_code=billing_postal_code,
                    billing_address=billing_address,
                    billing_city=billing_city,
                    billing_country=billing_country,
                    is_company=is_company,
                    company_name=company_name,
                    tax_number=tax_number,

                )

                if payment_method == 'credit_card':
                    gateway_url, payment_id = create_payment(request, user, cart_items, order)
                    if not (gateway_url and payment_id):
                        ...  # todo return with error
                    # todo delete cart from sesion

                    order.barion_id = payment_id
                    order.save()
                    if gateway_url:
                        return redirect(gateway_url)

                    # Barion fizetési adatok előkészítése
                    barion_data = {
                        "POSKey": settings.BARION_POS_KEY,
                        "PaymentType": "Immediate",
                        "GuestCheckOut": True,
                        "FundingSources": ["All"],
                        "PaymentRequestId": str(order.id),  # Egyedi rendelés ID
                        "Locale": "hu-HU",
                        "Transactions": [
                            {
                                "POSTransactionId": str(order.id),
                                "Payee": settings.BARION_PUBLIC_ID,
                                "Total": str(total_price),
                                "Items": [
                                    {
                                        "Name": item['product'].name,
                                        "Description": item['product'].description,
                                        "Quantity": item['quantity'],
                                        "Unit": "piece",
                                        "UnitPrice": str(item['discounted_price']),
                                        "ItemTotal": str(item['total_price']),
                                        "SKU": item['product'].sku,
                                    }
                                    for item in cart_items
                                ]
                            }
                        ],
                        "RedirectUrl": request.build_absolute_uri(reverse('payment_success')),
                        "CallbackUrl": settings.BARION_CALLBACK_URL
                    }

                    # Barion kérés küldése
                    response = requests.post(
                        settings.BARION_API_URL,
                        json=barion_data
                    )
                    if response.status_code == 200:
                        barion_response = response.json()
                        if barion_response.get("Status") == "Prepared":
                            payment_url = barion_response["GatewayUrl"]
                            return JsonResponse({"redirect_url": payment_url})
                        else:
                            return JsonResponse({"error": "Barion payment preparation failed."})
                    else:
                        return JsonResponse({"error": "Error communicating with Barion."})

                # Kosár elemeinek rögzítése
                for item in cart_items:
                    if isinstance(item, dict):  # Névtelen felhasználó esetén a kosár elemek dictionary formában vannak
                        product = item['product']
                        quantity = item['quantity']
                        discounted_price = item['discounted_price']
                        total_price = item['total_price']
                    else:  # Bejelentkezett felhasználó esetén a kosár elemek CartItem objektumok
                        product = item.product
                        quantity = item.quantity
                        discounted_price = Decimal(product.price) * (1 - (product.discount_rate / 100))
                        total_price = discounted_price * quantity

                    order_item = OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=discounted_price,
                        total_price=total_price,
                    )
                    order_item.save()  # Mentés az adatbázisba

                # Kosár ürítése
                if request.user.is_authenticated:
                    # Bejelentkezett felhasználó esetén
                    try:
                        CartItem.objects.filter(user=request.user).delete()
                    except Exception as e:
                        logger.error(f"Error while clearing cart for user {request.user}: {e}")
                else:
                    # Névtelen felhasználó esetén, kosár tárolása a session-ben
                    request.session['cart'] = {}  # Teljesen töröljük a kosár tartalmát

                # Email küldés
                if order.guest_user_id:
                    status_url = f"{settings.SITE_URL}{reverse('shopping_cart:order_status_guest', args=[order.id, order.guest_user_id])}"
                else:
                    status_url = f"{settings.SITE_URL}{reverse('shopping_cart:order_status', args=[order.id])}"

                cart_items = OrderItem.objects.filter(order=order)

                # Email sablon renderelése a változókkal
                message_to_user = render_to_string('order_status_email.html', {
                    'username': order.user.username if order.user else 'Vendég',  # Ha vendég a felhasználó
                    'order': order,
                    'cart_items': cart_items,  # Kosár tartalmának átadása
                    'status_url': status_url  # URL átadása az email sablonnak
                })

                # Email küldés beállítása
                email_to_user = EmailMessage(
                    'Rendelés állapota frissítve',
                    message_to_user,
                    to=[billing_email],  # Címzett email cím
                )
                email_to_user.content_subtype = 'html'  # HTML formátum
                email_to_user.send()

                #create_invoice(order)

                # Átirányítás a sikeres rendelés oldalára
                return render(request, 'success.html', {
                    'email': billing_email,
                    'payment_method': payment_method
                })

    else:
        form = PaymentForm()
        vat_rate = Decimal('0.27')


        if isinstance(request.user, AnonymousUser):
            # Névtelen felhasználó esetén: kosár tárolása a session-ben
            cart = request.session.get('cart', {})
            if not isinstance(cart, dict):  # Biztosítjuk, hogy a kosár dictionary típusú legyen
                cart = {}
                request.session['cart'] = cart

            cart_items = []
            total_price = Decimal('0')
            for product_id, quantity in cart.items():
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

            cart_count = len(cart_items)
            if total_price > 0:
                vat_amount = total_price * vat_rate
                total_out_vat = total_price - vat_amount
            else:
                vat_amount = Decimal('0')
                total_out_vat = Decimal('0')

        else:
            # Bejelentkezett felhasználó esetén
            cart_items = CartItem.objects.filter(user=request.user)
            total_price = Decimal('0')
            for item in cart_items:
                product = item.product
                product_price = Decimal(product.price)
                discounted_price = product_price * (1 - (product.discount_rate / 100))
                total_price += discounted_price * item.quantity

            cart_count = len(cart_items)
            if total_price > 0:
                vat_amount = total_price * vat_rate
                total_out_vat = total_price - vat_amount
            else:
                vat_amount = Decimal('0')
                total_out_vat = Decimal('0')

    return render(request, 'payment.html', {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count,
        'vat_amount': vat_amount,
        'total_out_vat': total_out_vat,
    })


class StartPaymentView(View):
    def get(self, request):
        payment_request = {
            "POSKey": settings.BARION_POS_KEY,
            "PaymentType": "Immediate",
            "GuestCheckout": True,
            "FundingSources": ["All"],
            "Locale": "hu-HU",
            "Currency": "HUF",
            "Transactions": [
                {
                    "POSTransactionId": "TRANS-12345",
                    "Payee": "info@yourdomain.com",
                    "Total": 1000,  # Az összeg forintban
                    "Items": [
                        {
                            "Name": "Teszt termék",
                            "Description": "Ez egy teszt termék",
                            "Quantity": 1,
                            "Unit": "db",
                            "UnitPrice": 1000,
                            "ItemTotal": 1000
                        }
                    ]
                }
            ],
            "CallbackUrl": settings.BARION_CALLBACK_URL,
            "RedirectUrl": "https://yourdomain.com/payment/success/"  # Az URL, ahová sikeres fizetés után tér vissza
        }

        response = requests.post(settings.BARION_API_URL, json=payment_request)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("PaymentId"):
            return redirect(response_data["GatewayUrl"])
        else:
            return JsonResponse({"error": "Payment initiation failed"}, status=400)

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        # Ellenőrizd és dolgozd fel a visszatérő adatokat
        data = request.json()
        # Frissítsd a rendelés állapotát az adatbázisban a kapott PaymentId alapján

    return JsonResponse({"status": "ok"})

def payment_success(request):
    return JsonResponse({"message": "Payment successful!"})

def success_view(request):
    return render(request, 'success.html')


def order_status(request, order_id, guest_user_id=None):
    # A rendelés lekérdezése az ID és a guest_user_id alapján (ha vendégfelhasználó)
    if guest_user_id:
        order = get_object_or_404(Order, id=order_id, guest_user_id=guest_user_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order
    }
    return render(request, 'order_status.html', context)

def order_status_guest_view(request, order_id, guest_user_id):
    order = get_object_or_404(Order, id=order_id, guest_user_id=guest_user_id)
    return render(request, 'order_status.html', {'order': order})

@csrf_exempt
def barion_after(request):
    if request.method == 'GET':
        payment_id = request.GET.get('paymentId', None)
        customer_cart = CustomerCart.objects.get(barion_id=payment_id)
        status = '' if not customer_cart.barion_status else customer_cart.barion_status
        return render(request, 'booking/after_payment.html', {"status": _(status), "appointment_code": str(customer_cart.code), "barion_id": payment_id})

def payment_status(request, payment_id):
    customer_cart = Order.objects.filter(barion_id=payment_id).first()
    if not customer_cart:
        return JsonResponse({'error': "Can't found transaction"}, status=405)
    return JsonResponse({"status": _(customer_cart.barion_status)})

@csrf_exempt
def barion_ipn(request):
    if request.method == 'GET':
        payment_id = request.GET.get('paymentId', None)
        if not payment_id:
            return JsonResponse({'error': 'Payment ID not provided'}, status=400)

        response = get_payment_status(payment_id)
        if response:
            try:
                customer_cart = CustomerCart.objects.get(barion_id=payment_id)
                status = response.get('Status')
                if status in dict(CustomerCart.BARION_STATUSES).keys():
                    billing = BillingAddress.objects.filter(customer_cart=customer_cart).first()
                    if customer_cart.barion_status != 'success' and status == 'Succeeded' and billing:
                        create_invoice(customer_cart)
                    customer_cart.barion_status = status
                    customer_cart.save()
                return JsonResponse({'status': 'success', 'message': 'Appointment status updated'})
            except Appointment.DoesNotExist:
                return JsonResponse({'error': 'Appointment not found'}, status=404)
            except KeyError:
                return JsonResponse({'error': 'Invalid status in payment response'}, status=500)
            except Exception as e:
                print(f"Barion ipn exception {e}")
                return JsonResponse({'error': 'Error while processing data'}, status=500)
        else:
            return JsonResponse({'error': 'Failed to retrieve payment status'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def check_vat(request):
    if request.method == 'POST':
        config = get_invoice_cnf()
        try:
            valid = False
            request_data = json.loads(request.body)
            tax_num = request_data.get('tax_num').split('-')[0]
            residency = request_data.get('residency')
            response_data = {"valid": False}
            if residency.lower() == 'eu':
                response_data = VIESModule.get_tax_number_data(tax_num)
            if residency.lower() == 'hu':
                nav_api = NAVOnlineSzamlaAPI(config['nav_api']['user'], config['nav_api']['password'], config['nav_api']['xml_key'], config['nav_api']['user_tax_number'])
                api_response = nav_api.get_tax_number_data(tax_num)
                if not api_response.get("valid", False):
                    api_response = VIESModule.get_tax_number_data(tax_num)
                else:
                    api_response["country_code"] = "HU"
                response_data = api_response
            return JsonResponse(response_data)
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def create_invoice(order):
    logger = logging.getLogger('django')
    user = order.user
    szamlazz_info = SzamlazzInfo()
    szamlazz_info.buyer_name = order.billing_last_name + " " + order.billing_first_name
    szamlazz_info.buyer_post_code = order.billing_postal_code
    szamlazz_info.buyer_city = order.billing_city
    szamlazz_info.buyer_address = order.billing_address
    szamlazz_info.comment = ""
    szamlazz_info.buyer_tax_number = order.tax_number
    szamlazz_info.buyer_email = order.billing_email
    if order.payment_method == 'redit_card':
        szamlazz_info.payment_type = "Bankkártyás vásárlás"
    elif order.payment_method == 'bank_transfer':
        szamlazz_info.payment_type = "Átutalás"
    szamlazz_info.order_number = order.code
    print("Szamlazz info", szamlazz_info)
    tax = 27 / 100
    cart_items = OrderItem.objects.filter(order=order).all()
    for item in cart_items:
        netto_price = round((int(item.total_price) / (1 + tax)), 2)
        tax_content = round(int(item.total_price) - netto_price, 2)
        brutto_price = int(item.total_price)
        szamlazz_item = SzamlazzItem(item.product.name, 1, netto_price, netto_price, tax_content, brutto_price, vat_key=int(tax * 100))
        szamlazz_info.items.append(szamlazz_item)

    # Elküldi a számlakészítési igényt
    szamlazz_result = SzamlazzhuModule(get_invoice_cnf()["szamlazz_agent"]).create_invoice(szamlazz_info)
    print(f"Számlázz válasz adatok: {szamlazz_result}")

    if szamlazz_result[0] is True:
        logger.info(f'Invoice created {szamlazz_result}')
        order.invoice_num = szamlazz_result[1]
        order.invoice_url = szamlazz_result[2]
        order.save()
        return True
    logger.error("Erorr while creating invoice")
    return False


def get_invoice_cnf(filename='invoice_config.yaml'):
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)