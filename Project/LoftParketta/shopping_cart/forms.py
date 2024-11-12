from django import forms

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
    full_name = forms.CharField(max_length=100, required=True, label="Teljes név")
    email = forms.EmailField(required=True, label="Email cím")
    phone = forms.CharField(max_length=15, required=True, label="Telefonszám")
    address = forms.CharField(max_length=255, required=True, label="Cím")
    city = forms.CharField(max_length=100, required=True, label="Város")

    # Szállítási lehetőségek
    shipping_method = forms.ChoiceField(
        choices=[
            ('free_shipping', 'Ingyenes szállítás Szegeden belül'),
            ('home_delivery', 'Házhoz szállítás'),
            ('store_pickup', 'Boltban történő átvétel')
        ],
        required=True,
        label="Szállítási mód"
    )

    payment_method = forms.ChoiceField(
        choices=[
            ('cash_on_delivery', 'Utánvétel'),
            ('bank_transfer', 'Banki utalás'),
            ('credit_card', 'Bankkártyás fizetés')
        ],
        required=True,
        label="Fizetési mód"
    )