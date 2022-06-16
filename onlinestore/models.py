from os import access
from tkinter import CASCADE
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField


# Create your models here.
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    zip = models.IntegerField()

    def __str__(self):
        return self.name
CATEGORY_CHOICES = (
    ('S','Shirt'),
    ('SP','Sport wear'),
    ('O','Outwear'),
)

LABEL_CHOICES = (
    ('P','primary'),
    ('S','secondary'),
    ('D','danger'),
)

class Item(models.Model):
    item_title = models.CharField(max_length=120)
    price = models.FloatField()
    discount = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2,default='S')
    label = models.CharField(choices=LABEL_CHOICES,max_length=2,default='D')
    description = models.TextField(default="This is the dummy description of this product item")
    slug = models.SlugField(default='item_title')
    image = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.item_title

    def getAbsoluteUrl(self):
        return reverse( "onlinestore:products", kwargs={ 'slug' : self.slug})

    def getAddtoCartUrl(self):
        return reverse( "onlinestore:addtoCart", kwargs={ 'slug' : self.slug})

    def getRemovefromCartUrl(self):
        return reverse( "onlinestore:removefromCart", kwargs={ 'slug' : self.slug})

class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)     
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.item_title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # CASCADE -> delte child rows after parent's record deletion
    # customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=25)
    items = models.ManyToManyField(OrderItem)
    numbers = models.PositiveIntegerField(default=1)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    placed_date = models.DateTimeField()
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL,blank=True,null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL,blank=True,null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL,blank=True, null=True)
    being_delievered = models.BooleanField(default=False)
    recieved = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
         return self.user.username
    
    def get_total(self):
        total=0
        for order_item in self.items.all():
            total = total + order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

class BillingAddress(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    countries = CountryField(multiple=True)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    stripe_change_id = models.CharField(max_length=55)
    user = models.ForeignKey(User,on_delete=models.SET_NULL,blank=True,null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField(default=1.0)
    
    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"