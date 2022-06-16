from email import message
from email.policy import default
from tkinter import Widget
from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S','Stipe'),
    ('P','PayPal')
)

class checkoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '1234 Main St'}))
    home_address = forms.CharField(required=False,widget=forms.TextInput(attrs={'placeholder': 'Apartment or suite'}))
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={'class': 'custom-select d-bock w-100'}))
    zip = forms.CharField(widget=forms.TextInput(attrs={'class': 'for-control'}))
    same_billing_address = forms.BooleanField(widget=forms.CheckboxInput())
    save_info = forms.BooleanField(widget=forms.CheckboxInput())
    payment_option = forms.ChoiceField(widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)

class CouponForm(forms.Form):
    code =  forms.CharField(widget=forms.TextInput(attrs={
        'class':'forms-control',
        'placeholder':'Promo code',
        'aria-label':'Recipient\'s username',
        'aria-describedly': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()