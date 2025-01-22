import json
import requests
from django.urls import reverse
import logging

base_url = "https://api.barion.com"
POS_KEY = "57b233ce-3ba1-4305-9117-1149002ec392"
PIXEL = "BP-s4UecBuBU8-4A"
START_PAYMENT = base_url + "/v2/Payment/Start"


def create_payment(request, user, items, order):
    headers = {
        'Content-Type': 'application/json',
    }
    items, total = process_items(items)
    payload = {
        "POSKey": POS_KEY,
        "PaymentType": "Immediate",
        "GuestCheckOut": True,
        "FundingSources": ["All"],
        "PaymentRequestId": str(order.code),
        "PayerHint": order.billing_email,
        "Locale": "hu-HU",
        "Transactions": [
            {
                "POSTransactionId": str(order.code),
                "Payee": "loftparketta@gmail.com",
                "Total": total,
                "Currency": "HUF",
                "Comment": "Test transaction",
                "Items": items
            }
        ],
        "RedirectUrl": request.build_absolute_uri(reverse('barion_after')),
        "CallbackUrl": request.build_absolute_uri(reverse('barion_ipn')),
        "OrderNumber": str(order.tax_number),
        # "BillingAddress": {
        #     "Country": billing_address.country.code,
        #     "City": billing_address.city,
        #     "Zip": billing_address.postal_code,
        #     "Street": billing_address.address_line_1,
        #     "Street2": billing_address.address_line_2,
        #     "Street3": "",
        #     "FullName": user.first_name if user.first_name else '',
        # }
    }
    data = json.dumps(payload)
    response = requests.post(START_PAYMENT, headers=headers, data=data)
    print(f"barion_response")
    logging.info(f"response: {response}")
    if response.status_code == 200:
        print("Payment created successfully!")
        print("Response JSON:", response.json())
        json_response = response.json()
        return json_response["GatewayUrl"], json_response["PaymentId"]
    else:
        print("Failed to create payment.")
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
        return None


def get_payment_status(payment_id):
    headers = {
        'Content-Type': 'application/json',
        "x-pos-key": POS_KEY
    }

    params = {
        # "POSKey": POS_KEY,
        # "PaymentId": payment_id
    }

    url = base_url + f"/v4/payment/{payment_id}/paymentstate"
    response = requests.get(url, headers=headers, params=params)
    print("barion_response")
    if response.status_code == 200:
        print("IPN Payment status retrieved successfully!")
        print("IPN Response JSON:", response.json())
        return response.json()
        # json_response = response.json()

    else:
        print("Failed to retrieve payment status.")
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
        return None


def process_items(items):
    barion_items = []
    price_sum = 0
    for item in items:
        product = item['product']  # A 'Product' objektum
        new_item = {
            "Name": product.name,  # Pont operátor az attribútum eléréséhez
            "Description": product.description,
            "Quantity": item['quantity'],
            "Unit": "db",
            "Unit price": int(product.price * product.discount_rate) if product.is_discounted else int(product.price),
            "ItemTotal": int(
                (product.price * product.discount_rate) * item['quantity']) if product.is_discounted else int(
                product.price * item['quantity']),
        }
        barion_items.append(new_item)
        price_sum += int(new_item['ItemTotal'])
    return barion_items, price_sum