from django.urls import path
from .views import *

app_name = 'onlinestore'

urlpatterns = [
    path('',HomeView.as_view(),name='home'),
    path('checkout/',checkoutView.as_view(),name='checkout'),
    path('orderSummary/',orderSummaryView.as_view(),name='orderSummary'),
    path('products/<slug>/',ItemDetailView.as_view(),name='products'), 
    path('add-coupon/<slug>/',AddCouponView.as_view(),name='add-coupon'), 
    path('addtoCart/<slug>/',addtoCart,name='addtoCart'), 
    path('payment/<payment_option>/',PaymentView.as_view(),name='payment'), 
    path('removefromCart/<slug>/',removefromCart,name='removefromCart'),  
    path('removeSingleItemfromCart/<slug>/',removeSingleItemfromCart,name='removeSingleItemfromCart'),
    path('request-refund/',RequestRefundView.as_view(),name="request-refund"),
]