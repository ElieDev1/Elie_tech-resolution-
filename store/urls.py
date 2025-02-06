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
     # Password reset URL
    path('reset_password/', views.auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('reset_password_sent/', views.auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', views.auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('products/', views.product_list, name='product_list'),
    path('chekout/', views.checkout, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
   



    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('orders/', views.order_list, name='order_list'),
    path('like_product/<int:product_id>/', views.toggle_like, name='like_product'),
    path('add_comment/<int:pk>/', views.add_comment, name='add_comment'),
    path('cart/', views.cart_view, name='cart_view'),  # Cart view page
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add product to cart
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'), # Remove product from cart
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),



    path('messages/', views.message_page, name='messages'),
    path('chat_with_customer/<int:customer_id>/', views.chat_with_customer, name='chat_with_customer'),
    path('send_message/', views.send_message, name='send_message'),
    path('about/', views.about_view, name='about'),





    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('sold-products/', views.sold_products_list, name='sold_products_list'),
    path('all-customers/', views.all_customers, name='all_customers'),
    path('customer-contributions/', views.customer_contributions, name='customer_contributions'),
    
    # Product Management
    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/add/', views.add_product, name='admin_add_product'),
    path('admin-panel/products/edit/<int:pk>/', views.edit_product, name='admin_edit_product'),
    path('admin-panel/products/delete/<int:pk>/', views.delete_product, name='admin_delete_product'),
    path("admin-panel/product/<int:product_id>/", views.admin_product_detail, name="admin_product_detail"),
    
    # Order Management
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin_order/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('order/<int:order_id>/payment/', views.payment_method, name='payment_method'),
    path('admin-panel/orders/approve/<int:order_id>/', views.approve_payment, name='approve_payment'),
    path('confirm-delivery/<int:order_id>/', views.confirm_delivery, name='confirm_delivery'),
    

    
    # User Management
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/user_view/<int:user_id>/', views.admin_view_user, name='admin_view_user'),
    path('admin-panel/users/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin-panel/users/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    
    # Message Management
    path('admin-panel/messages/', views.admin_messages, name='admin_messages'),
    path('admin-panel/messages/view/<int:message_id>/', views.admin_view_message, name='admin_view_message'),
    path('admin-panel/messages/delete/<int:message_id>/', views.admin_delete_message, name='admin_delete_message'),
    
    # Team Management
    path('admin-panel/team/', views.admin_team, name='admin_team'),
    path('admin-panel/team/add/', views.add_team, name='admin_add_team'),
    path('admin-panel/team/edit/<int:pk>/', views.edit_team, name='admin_edit_team'),
    path('admin-panel/team/delete/<int:pk>/', views.delete_team, name='admin_delete_team'),


    path('admin-panel/search/', views.admin_search, name='admin_search'),

    path('admin-panel/comments/', views.admin_comment_list, name='admin_comment_list'),
    path('admin-panel/comments/view/<int:comment_id>/', views.admin_view_comment, name='admin_view_comment'),
    path('admin-panel/comments/edit/<int:comment_id>/', views.admin_edit_comment, name='admin_edit_comment'),
    path('admin-panel/comments/delete/<int:comment_id>/', views.admin_delete_comment, name='admin_delete_comment'),
    path('admin-panel/all-products/', views.all_products, name='all_products'),
     # Advertisement URLs
    path('advertisements/', views.advertisement_list, name='advertisement_list'),
    path('advertisements/create/', views.create_advertisement, name='create_advertisement'),
    path('advertisements/edit/<int:pk>/', views.edit_advertisement, name='edit_advertisement'),
    path('advertisements/delete/<int:pk>/', views.delete_advertisement, name='delete_advertisement'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/edit/<int:pk>/', views.edit_notification, name='edit_notification'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    
   


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
