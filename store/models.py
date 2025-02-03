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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_approved = models.BooleanField(default=False)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.user.username}"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)
    is_read = models.BooleanField(default=False)    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"

class comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.product}"    
    


from django.db import models

class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('CEO', 'CEO & Founder'),
        ('CTO', 'Chief Technology Officer'),
        ('CMO', 'Chief Marketing Officer'),
        ('DEV', 'Software Developer'),
        ('DESIGNER', 'UI/UX Designer'),
        ('SUPPORT', 'Customer Support'),
    ]

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEV')
    image = models.ImageField(upload_to='team_images/')

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"


