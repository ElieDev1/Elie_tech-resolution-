from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('products/', views.product_list, name='product_list'),
    path('chekout/', views.checkout, name='checkout'),
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.order_list, name='order_list'),
    path('like_product/<int:product_id>/', views.toggle_like, name='like_product'),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('cart/', views.cart_view, name='cart_view'),  # Cart view page
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add product to cart
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'), # Remove product from cart
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('pay_order/<int:order_id>/', views.pay_order, name='pay_order'), 


    path('messages/', views.message_page, name='messages'),
    path('chat_with_customer/<int:customer_id>/', views.chat_with_customer, name='chat_with_customer'),
    path('send_message/', views.send_message, name='send_message'),
    path('about/', views.about_view, name='about'),




]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
