from django.contrib import admin
from .models import *
from django.utils.html import format_html

# ProductImage Inline Admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    inlines = [ProductImageInline] 

# Customer Admin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address')
    search_fields = ('user__username',)

# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_price', 'ordered_at', 'delivery_status', 'payment_status', 'payment_approved')
    search_fields = ('customer__user__username', 'id')

    def payment_approved(self, obj):
        return format_html('<strong>{}</strong>', obj.payment_status)

    payment_approved.short_description = 'Payment Approved'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('order_items')

# OrderItem Admin
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'subtotal')
    search_fields = ('order__id', 'product__name')
    list_filter = ('order__ordered_at',)

    def subtotal(self, obj):
        return obj.quantity * obj.product.price

    subtotal.short_description = 'Subtotal'

# Message Admin
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'timestamp')
    search_fields = ('sender__username', 'recipient__username')
    list_filter = ('timestamp',)

# Comment Admin
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'content', 'timestamp')
    search_fields = ('user__username', 'product__name', 'content')
    list_filter = ('timestamp',)

# TeamMember Admin
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role')
    list_filter = ('role',)

# Advertisement Admin
@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "active")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("get_user", "message", "created_at", "read")

    def get_user(self, obj):
        # Access the related user's username (or any other field you want)
        return obj.user.username if obj.user else "No User"
    get_user.short_description = 'User'

# Register models in the admin site
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Comment, CommentAdmin)
