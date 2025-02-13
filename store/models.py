from django.db import models
from django.contrib.auth.models import User



class Product(models.Model):
    CATEGORY_CHOICES = [
        ('accessories', 'Accessories & Gadgets'),
        ("smartphones", "Smartphones & Accessories"),
        ("laptops", "Laptops & Computers"),
        ("tv_entertainment", "TVs & Home Entertainment"),
        ("audio", "Audio & Headphones"),
        ("gaming", "Gaming & Accessories"),
        ("cameras", "Cameras & Photography"),
        ("wearables", "Wearables & Smartwatches"),
        ("home_appliances", "Home Appliances"),
        ("networking", "Networking & Internet"),
        ("power", "Power & Batteries"),
        ("drones", "Drones & RC Gadgets"),
        ("diy", "DIY Electronics & Components"),
        ("office", "Office & Stationery Tech"),
        ("car_electronics", "Car Electronics"),
        ("security", "Security & Surveillance"),
        ("software", "Software & Apps"),
        ("other", "Other Electronics"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0.0)
    expected_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="liked_products", blank=True)
    comments = models.ManyToManyField(User, through="Comment", related_name="commented_products", blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="accessories")  # Category Field

    def __str__(self):
        return self.name


    # Get the main image for the product
    def main_image(self):
        main_image = self.product_images.filter(main_image=True).first()
        if main_image:
            return main_image.image.url
        return self.product_images.first().image.url  # fallback to first image if no main image

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="product_images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    main_image = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/profile.png', blank=True)

    def __str__(self):
        return self.user.username

class Order(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered_at = models.DateTimeField(auto_now_add=True)
    
    # Delivery status
    delivery_status = models.CharField(max_length=100, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')], default='Pending')

    # Payment-related fields
    payment_message = models.TextField(blank=True, null=True)
    payment_image = models.ImageField(upload_to='payment_images/', blank=True, null=True)
    payment_status = models.CharField(
        choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed')],
        default='Pending', max_length=10
    )

    def __str__(self):
        return f"Order for {self.customer.user.username} placed on {self.ordered_at}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} items"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)
    is_read = models.BooleanField(default=False)    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"



class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Allow anonymous users
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'UnknownUser'} on {self.product}"

    


from django.db import models

class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('CEO', 'CEO & Founder'),
        ('CTO', 'Chief Technology Officer'),
        ('CMO', 'Chief Marketing Officer'),
        ('DEV', 'Software Developer'),
        ('DESIGNER', 'UI/UX Designer'),
        ('SUPPORT', 'Customer Support'),
        ('agent', 'Agent'),
        ('MARKETING', 'Marketing Specialist'),
        ('HR', 'Human Resource Manager'),
        ('FINANCE', 'Finance Manager'),
        ('OTHER', 'Other'),
        

    ]

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEV')
    image = models.ImageField(upload_to='team_images/')

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"


from django.utils import timezone

class Advertisement(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='advertisements/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)  # Link to the product or promo page
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def is_active(self):
        return self.active and self.start_date <= timezone.now() <= self.end_date


class Notification(models.Model):
    user = models.ManyToManyField(User, related_name="notifications", blank=True)  # Allows selection of multiple users
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    for_all = models.BooleanField(default=False)  # True if the notification is for all users

    def __str__(self):
        return self.message[:50]

