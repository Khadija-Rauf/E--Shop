from django import views
from django.forms import CharField
from django.shortcuts import get_object_or_404, render,redirect
from .models import *
from django.views.generic import ListView,DetailView,View
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.conf import settings
import stripe
import string
import random

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase+string.digits,k=25))

class HomeView(ListView):
    model = Item
    paginate_by = 15
    template_name = "homePage.html"

class orderSummaryView(LoginRequiredMixin, View):
   def get(self, *args, **kwargs):
    try:
        order = Order.objects.get(user=self.request.user,ordered = False)
        context ={ 'object' : order }
        return render(self.request,"orderSummary.html",context)
    except ObjectDoesNotExist:
        messages.warning(self.request,"You don't have an active order.")
        return redirect("/")

class ItemDetailView(DetailView):
    model = Item
    template_name = "ProductPage.html"

class checkoutView(View):
    def get(self,*args,**kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = checkoutForm()
            context = {
                'form' : form,
                'couponfprm':CouponForm(),
                'order': order,
                'DISPLAY_COUPOM_FORM':True
            }
            return render(self.request,"checkoutPage.html",context)    
        except ObjectDoesNotExist:
            messages.info(self.request,"You don't have an active order.")
            return redirect("core:checkout")
    
    def post(self,*args,**kwargs):
        form = checkoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user,ordered = False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                home_address = form.cleaned_data.get('home_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    home_address = home_address,
                    country = country,
                    zip = zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                messages.success(self.request,"Invalid payment option selected.")

                if payment_option =='S':
                    return redirect('onlinestore:payment',payment_option='stripe')
                elif payment_option =='P':
                    return redirect('onlinestore:payment',payment_option='paypal')
                else:
                    messages.warning(self.request,"Invalid payment option selected")
                    return redirect('onlinestore:checkout')
        except ObjectDoesNotExist:
            messages.warning (self.request,"You don't have an active order.")
            return redirect("onlinestore:orderSummary")
        return redirect("onlinestore:payment",payment_option='stripe')

class PaymentView(View):
    def get(self,*args,**kwargs):
        order = Order.objects.get(user=self.request.user,ordered=False)
        # if order.billing_address:
        context = {
            'order' : order,
            'DISPLAY_COUPON_FORM':False
        }
        return render(self.request,"payment.html",context)
        # else:
        #    messages.warning(self.request,"You have not added a billing address.")
        #    return redirect("onlinestore:checkout")

    def post(self,*args,**kwargs):
        order = Order.objects.get(user=self.request.user,ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total()*100)
        try:
            charge = stripe.Charge.create(
                amount = amount,
                currency = "usd",
                source = token,
            )
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = amount
            payment.save()

            order_items = order.items.all()
            order.items.update(ordered = True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment=payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request,"Your order was successful!")
            return redirect("/")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
            messages.warning(self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")

        except Exception as e:
                # send an email to ourselves
            messages.warning(self.request, "A serious error occurred. We have been notifed.")
            return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")



def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request,"productPage.html",context)

@login_required
def addtoCart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item ,created= OrderItem.objects.get_or_create(item = item,user=request.user,ordered = False)
    order_q = Order.objects.filter(user=request.user, ordered=False)
    if order_q.exists():
        order = order_q[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item.quantity =  order_item.quantity + 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("onlinestore:orderSummary")
        else:
            messages.info(request, "This item was added into your cart.")
            order.items.add(order_item)
            return redirect("onlinestore:orderSummary")
    else:
        placed_date = timezone.now()
        order = Order.objects.create(user=request.user ,placed_date = placed_date)
        order.items.add(order_item)
        messages.info(request, "This item was added into your cart.")
        return redirect("onlinestore:orderSummary")
@login_required
def removefromCart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item = OrderItem.objects.get_or_create(item = item,user=request.user,ordered = False)
    order_q = Order.objects.filter(user=request.user, ordered=False)
    if order_q.exists():
        order = order_q[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(item = item,user=request.user,ordered = False)[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed into your cart.")       
        else:
            messages.info(request, "This item was not into your cart.")
            return redirect("onlinestore:orderSummary")
    else:
        messages.info(request, "You don't have an active order.")
        return redirect("onlinestore:products", slug=slug)
    return redirect("onlinestore:products", slug=slug)

@login_required
def removeSingleItemfromCart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item = OrderItem.objects.get_or_create(item = item,user=request.user,ordered = False)
    order_q = Order.objects.filter(user=request.user, ordered=False)
    if order_q.exists():
        order = order_q[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(item = item,user=request.user,ordered = False)[0]
            if order_item.quantity > 1:
                order_item.quantity =  order_item.quantity - 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")  
            return redirect("onlinestore:orderSummary")
        else:
            messages.info(request, "This item was not into your cart.")
            return redirect("onlinestore:products", slug=slug)
    else:
        messages.info(request, "You don't have an active order.")
        return redirect("onlinestore:products", slug=slug)
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code = code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon doesn't exist")
        return redirect("core:checkout")

class AddCouponView(View):
    def post(self,*args,**kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data('code')
                order = Order.objcts.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request,code)
                order.save()
                messages.info(self.request,"Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request,"You don't have an active order.")
                return redirect("core:checkout")

class RequestRefundView(View):
    def get(self,*args,**kwargs):
        form=RefundForm()
        context = {
            'form':form
        }
        return render(self.request,"request-refund.html",context)
    def post(self,*args,**kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data('message')
            email = forms.cleaned_data('email')

            try:
                order=order,object.get(ref_code=ref_code)
                order.refund_requested=True
                order.save()
                refund=Refund()
                refund.order=order
                refund.reason=message
                refund.email = email
                refund.save()

                messages.info(self.request,"Your request is recieved.")
                return redirect("onlinestore:request-refund")

            except ObjectDoesNotExist:
                message.info(self.request,"This order doesn't exist.")
                return redirect("onlinestore:request-refund")
