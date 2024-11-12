from django import forms
#from captcha.fields import ReCaptchaField
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from shop.models import Order

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2", "first_name", "last_name")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user

class QuoteRequestForm(forms.Form):
    request_type = forms.ChoiceField(choices=[('cart', 'Kosárban lévő termékekről kérek árajánlatot'),
                                               ('custom', 'Egyedi termékről kérek árajánlatot')],
                                      required=True)
    custom_product_name = forms.CharField(required=False, max_length=100)
    custom_product_description = forms.CharField(required=False, widget=forms.Textarea)
    custom_product_quantity = forms.IntegerField(min_value=1, required=False)
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=15)
    message = forms.CharField(required=False, widget=forms.Textarea)

    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get("request_type")

        if request_type == 'custom':
            custom_product_name = cleaned_data.get('custom_product_name')
            custom_product_quantity = cleaned_data.get('custom_product_quantity')

            if not custom_product_name:
                self.add_error('custom_product_name', 'A termék neve kötelező, ha egyedi terméket kérsz.')
            if custom_product_quantity is None:
                self.add_error('custom_product_quantity', 'A mennyiség kötelező, ha egyedi terméket kérsz.')

        return cleaned_data


class PaymentForm(forms.Form):
    # Szállítási adatok
    shipping_first_name = forms.CharField(max_length=100, required=True, label="Keresztnév")
    shipping_last_name = forms.CharField(max_length=100, required=True, label="Vezetéknév")
    shipping_postal_code = forms.CharField(max_length=10, required=True, label="Irányítószám")
    shipping_address = forms.CharField(max_length=255, required=True, label="Cím")
    shipping_city = forms.CharField(max_length=100, required=True, label="Város")
    shipping_country = forms.CharField(max_length=100, required=True, label="Ország")
    shipping_method = forms.ChoiceField(
        choices=[
            ('free_shipping', 'Ingyenes szállítás Szegeden belül'),
            ('home_delivery', 'Házhoz szállítás'),
            ('store_pickup', 'Boltban történő átvétel')
        ],
        required=True,
        label="Szállítási mód"
    )

    # Számlázási adatok
    billing_first_name = forms.CharField(max_length=100, required=True, label="Keresztnév")
    billing_last_name = forms.CharField(max_length=100, required=True, label="Vezetéknév")
    billing_email = forms.EmailField(required=True, label="Email")
    billing_phone = forms.CharField(max_length=15, required=True, label="Telefonszám")
    billing_postal_code = forms.CharField(max_length=10, required=True, label="Irányítószám")
    billing_address = forms.CharField(max_length=255, required=True, label="Cím")
    billing_city = forms.CharField(max_length=100, required=True, label="Város")
    billing_country = forms.CharField(max_length=100, required=True, label="Ország")

    # Cég vásárlás jelölése
    is_company = forms.BooleanField(required=False, label="Cégként vásárolok")
    company_name = forms.CharField(max_length=255, required=False, label="Cégnév")
    tax_number = forms.CharField(max_length=20, required=False, label="Adószám")

    # Fizetési mód
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        label='Fizetési mód',
        widget=forms.RadioSelect
    )