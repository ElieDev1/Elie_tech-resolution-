from django.contrib import admin
from .models import *

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1 

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    inlines = [ProductImageInline] 

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address')
    search_fields = ('user__username',) 
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'quantity', 'total_price', 'payment_approved', 'ordered_at')
    search_fields = ('customer__user__username', 'product__name')
    list_filter = ('payment_approved', 'ordered_at')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'timestamp')
    search_fields = ('sender__username', 'recipient__username')
    list_filter = ('timestamp',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'content', 'timestamp')
    search_fields = ('user__username', 'product__name', 'content')
    list_filter = ('timestamp',)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role')
    list_filter = ('role',)

# Register your models here
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(comment, CommentAdmin)
