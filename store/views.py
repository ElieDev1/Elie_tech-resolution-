from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from .models import *
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q, Count,Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta
from django.utils import timezone
from .forms import *
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings



def home(request):
    # Products with like counts (for the main grid)
    products_with_likes = Product.objects.annotate(likes_count=Count('likes')).order_by('-likes_count')

    # 40 random products (for the carousel)
    all_products = Product.objects.order_by('?')[:20]

    # Categories with product counts
    categories = Product.CATEGORY_CHOICES
    product_counts = {
        category[0]: Product.objects.filter(category=category[0]).count()
        for category in categories
    }

    # Fetch active advertisements (only those within the active date range)
    advertisements = Advertisement.objects.filter(
        active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )

    context = {
        'products_with_likes': products_with_likes,  # Key change
        'all_products': all_products,  # Now shows 40 random products
        'categories': categories,
        'product_counts': product_counts,
        'advertisements': advertisements,  # Add ads to context
    }
    return render(request, 'store/home.html', context)



def product_detail(request, product_id):
    # Get the product or return a 404 if it doesn't exist
    product = get_object_or_404(Product, id=product_id)

    # Handle new comment posting
    if request.method == "POST":
        comment_content = request.POST.get('comment_content')
        if comment_content:
            customer = get_object_or_404(Customer, user=request.user)
            # Create and save the comment
            Comment.objects.create(
                user=request.user,  # The user posting the comment
                product=product,
                content=comment_content
            )
        return redirect('product_detail', product_id=product.id)  # Redirect to avoid re-posting on refresh

    # Return the page with product details and comments
    return render(request, 'store/product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        # Capture data from the form safely
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password', '')  # Avoids KeyError
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Ensure confirm_password exists
        if not confirm_password:
            messages.error(request, "Please confirm your password!")
            return redirect('register')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        # Create the user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        # Save additional details in Customer model
        Customer.objects.create(
            user=user,
            phone_number=phone,
            address=address
        )

        # Log the user in after registration
        login(request, user)

        # Redirect to the previous page or home
        next_url = request.GET.get('next', 'home')
        messages.success(request, 'Account created successfully!')
        return redirect(next_url)

    return render(request, 'store/register.html')

@csrf_exempt
def login_user(request):
    next_url = request.GET.get('next', '')  # Capture 'next' parameter from URL

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next', next_url)  # Preserve 'next' after form submission

        if not username or not password:  # Check if fields are empty
            messages.error(request, "Username and password are required!")
        else:
            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                return redirect(next_url if next_url else 'home')  # Redirect to next or home
            else:
                messages.error(request, "Invalid credentials!")

    return render(request, 'store/login.html', {"next": next_url})

@csrf_exempt
def logout_user(request):
    logout(request)
    return redirect('home')


# Product List






@login_required
def profile_view(request):
    customer = get_object_or_404(Customer, user=request.user)

    # Fetch all orders related to the customer, including order items and product details
    orders = Order.objects.filter(customer=customer).prefetch_related('order_items__product')

    return render(request, 'profile.html', {'customer': customer, 'orders': orders})



@login_required
def order_list(request):
    try:
        # Get customer profile with related user data
        customer = request.user.customer
    except Customer.DoesNotExist:
        return redirect('profile_creation')  # Redirect to profile setup if missing

    # Fetch orders with optimized database queries
    orders = Order.objects.filter(customer=customer).select_related(
        'customer__user'
    ).prefetch_related(
        'order_items__product__product_images'
    ).order_by('-ordered_at')

    # Get choices from the model
    payment_status_choices = dict(Order._meta.get_field('payment_status').choices)
    delivery_status_choices = dict(Order._meta.get_field('delivery_status').choices)

    # Add human-readable statuses to orders
    for order in orders:
        order.payment_status_display = payment_status_choices.get(order.payment_status, "Unknown")
        order.delivery_status_display = delivery_status_choices.get(order.delivery_status, "Unknown")

    return render(request, 'store/order_list.html', {
        'orders': orders,
        'payment_status_choices': payment_status_choices,
        'delivery_status_choices': delivery_status_choices
    })


# Add comment functionality
@login_required
@csrf_exempt
def add_comment(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        Comment.objects.create(user=request.user, product=product, content=content)
    return redirect('product_detail', pk=pk)



def product_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    # Fetch products based on query and category
    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category=category)

    # Add likes to the product list
    products_with_likes = [
        {
            'product': product,
            'likes': product.likes.count()
        }
        for product in products
    ]

    # Fetch random 50 products (instead of first 50)
    random_products = products.order_by('?')[:500]

    random_products_with_likes = [
        {
            'product': product,
            'likes': product.likes.count()
        }
        for product in random_products
    ]

    # Pagination for products (15 items per page)
    paginator = Paginator(random_products_with_likes, 50)  # 15 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch all categories as a list of tuples (value, label)
    categories = Product.objects.values('category').distinct()
    category_choices = [(category['category'], category['category']) for category in categories]

    context = {
        'products_with_likes': page_obj,
        'latest_products_with_likes': random_products_with_likes,  # Randomly ordered products
        'categories': category_choices,  # Pass categories as tuples
    }

    return render(request, 'store/product_list.html', context)




@csrf_exempt
def toggle_like(request, product_id):
    if request.user.is_authenticated:
        # Get the product
        product = get_object_or_404(Product, id=product_id)

        # Toggle like/unlike
        if request.user in product.likes.all():
            product.likes.remove(request.user)
            liked = False
        else:
            product.likes.add(request.user)
            liked = True

        # Return updated like count and status
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': product.likes.count()
        })
    return JsonResponse({'success': False, 'message': 'User not authenticated'})


def main_image(self):
    main_image = self.product_images.filter(main_image=True).first()
    if main_image:
        return main_image.image.url
    elif self.product_images.exists():
        return self.product_images.first().image.url  # fallback to first image
    return "/static/images/default.jpg"  # Fallback in case no image is available


@csrf_exempt
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    product = get_object_or_404(Product, id=product_id)

    if product.stock < 1:
        messages.error(request, "This product is out of stock!")
        return redirect('product_list')

    product_key = str(product_id)
    if product_key in cart:
        if cart[product_key]['quantity'] >= product.stock:
            messages.warning(request, f"Only {product.stock} units of {product.name} are available!")
            return redirect('cart_view')
        cart[product_key]['quantity'] += 1
    else:
        cart[product_key] = {'quantity': 1, 'price': float(product.price)}  # Store price

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, f"{product.name} added to cart. Current quantity: {cart[product_key]['quantity']}")
    return redirect('product_list')



@csrf_exempt
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    product_id_str = str(product_id)  # Ensure key is a string
    if product_id_str in cart:
        product = Product.objects.get(id=product_id)  # Get the product from the database
        product_name = product.name  # Extract product name
        del cart[product_id_str]  # Remove product from cart
        request.session['cart'] = cart  # Save updated cart
        messages.success(request, f"{product_name} has been removed from your cart.")  # Include product name in message

    return redirect('cart_view')


def clear_cart(request):
    request.session['cart'] = {}  # Empty the cart
    messages.success(request, "Your cart has been cleared.")
    return redirect('cart_view')

@csrf_exempt
def increase_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    product_id_str = str(product_id)

    # Check if product exists in cart
    if product_id_str in cart:
        if isinstance(cart[product_id_str], int):
            # Old format (e.g., cart["27"] = 2)
            cart[product_id_str] += 1
        elif isinstance(cart[product_id_str], dict) and 'quantity' in cart[product_id_str]:
            # New format (e.g., cart["27"] = {"quantity": 2})
            cart[product_id_str]['quantity'] += 1
        else:
            # If invalid format, reset to default structure
            cart[product_id_str] = {"quantity": 1}
    else:
        # Add product with correct format
        cart[product_id_str] = {"quantity": 1}

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_view')


@csrf_exempt
def decrease_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Use string keys to match the template
    product_id_str = str(product_id)

    if product_id_str in cart:
        # Check if the cart stores quantities directly or in a dictionary format
        if isinstance(cart[product_id_str], dict):
            quantity = cart[product_id_str].get("quantity", 1)
        else:
            quantity = cart[product_id_str]

        if quantity > 1:
            if isinstance(cart[product_id_str], dict):
                cart[product_id_str]["quantity"] -= 1  # Decrease quantity in dictionary
            else:
                cart[product_id_str] -= 1  # Decrease quantity directly
        else:
            del cart[product_id_str]  # Remove product if quantity is 1

    request.session['cart'] = cart
    request.session.modified = True  # Explicitly mark session as modified

    return redirect('cart_view')

@csrf_exempt
def cart_view(request):
    cart = request.session.get('cart', {})

    products = []
    total_price = 0

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=int(product_id))

            # Ensure `item_data` is always treated as a quantity (handle both cases)
            if isinstance(item_data, int):  # Old structure: cart["31"] = 2
                quantity = item_data
            elif isinstance(item_data, dict) and 'quantity' in item_data:
                quantity = item_data['quantity']
            else:
                quantity = 1  # Fallback in case of bad data

            subtotal = product.price * quantity
            total_price += subtotal

            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

        except Product.DoesNotExist:
            continue  # Ignore missing products

    return render(request, 'cart.html', {
        'cart': cart,
        'products': products,
        'total_price': total_price
    })


def about_view(request):
    team_members = TeamMember.objects.all()
    return render(request, 'about.html', {'team_members': team_members})


























@csrf_exempt
def checkout(request):
    cart = request.session.get('cart', {})

    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=int(product_id))

            quantity = item_data['quantity'] if isinstance(item_data, dict) and 'quantity' in item_data else 1
            unit_price = product.price  # ✅ Store unit price
            subtotal = unit_price * quantity  # ✅ Calculate subtotal
            total_price += subtotal  # ✅ Add to total price

            cart_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,  # ✅ Add unit price
                'subtotal': subtotal  # ✅ Add subtotal
            })

        except Product.DoesNotExist:
            continue  # Ignore missing products

    return render(request, 'store/checkout.html', {'cart_items': cart_items, 'total_price': total_price})


from django.urls import reverse

@csrf_exempt
@login_required(login_url='/register/')  # Redirect to login if not authenticated
def process_checkout(request):
    cart = request.session.get('cart', {})

    if not cart:  # If the cart is empty, redirect to the cart page
        return redirect('cart_view')

    total_price = 0
    order = Order.objects.create(customer=request.user.customer, total_price=total_price)

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=int(product_id))
            quantity = item_data['quantity']
            subtotal = product.price * quantity
            total_price += subtotal

            OrderItem.objects.create(order=order, product=product, quantity=quantity, subtotal=subtotal)

        except Product.DoesNotExist:
            continue  # Skip missing products

    order.total_price = total_price
    order.save()

    request.session['cart'] = {}  # Clear the cart after checkout
    request.session.modified = True

    # Redirect to order details page after successful checkout
    return redirect(reverse('order_detail', kwargs={'order_id': order.id}))



























# ---------------------------------------------------------------
# Message Page View
# ---------------------------------------------------------------
@csrf_exempt
def message_page(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get users who sent or received messages from the current user
    customers_who_messaged = None
    if request.user.is_staff:
        customers_who_messaged = User.objects.filter(
            Q(sent_messages__recipient=request.user) | Q(received_messages__sender=request.user)
        ).distinct()

    # Get all messages for the current user
    all_messages = Message.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user)
    ).order_by('timestamp')

    return render(request, 'message.html', {
        'all_messages': all_messages,
        'admins': User.objects.filter(is_staff=True),
        'customers_who_messaged': customers_who_messaged,
        'selected_customer': None,
    })



# ---------------------------------------------------------------
# Chat with Customer View (Mark messages as read here)
# ---------------------------------------------------------------
@csrf_exempt
def chat_with_customer(request, customer_id):
    if not request.user.is_authenticated:
        return redirect('login')

    customer = get_object_or_404(User, id=customer_id)

    # MARK MESSAGES AS READ WHEN CHAT IS OPENED
    # Update all messages from this customer to the current user as read
    Message.objects.filter(
        sender=customer,
        recipient=request.user,
        is_read=False  # Only mark unread messages
    ).update(is_read=True)

    # Get messages between current user and selected customer
    all_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=customer)) |
        (Q(sender=customer) & Q(recipient=request.user))
    ).order_by('timestamp')

    # Get users who sent or received messages from the current user
    customers_who_messaged = None
    if request.user.is_staff:
        customers_who_messaged = User.objects.filter(
            Q(sent_messages__recipient=request.user) | Q(received_messages__sender=request.user)
        ).distinct()

    return render(request, 'message.html', {
        'all_messages': all_messages,
        'admins': User.objects.filter(is_staff=True),
        'customers_who_messaged': customers_who_messaged,
        'selected_customer': customer,
    })

# ---------------------------------------------------------------
# Send Message View (Mark previous messages as read when replying)
# ---------------------------------------------------------------
@csrf_exempt
def send_message(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        if content or image:
            recipient = get_object_or_404(User, id=recipient_id)

            # MARK PREVIOUS MESSAGES AS READ WHEN REPLYING
            # Update all unread messages from the recipient to the current user
            Message.objects.filter(
                sender=recipient,
                recipient=request.user,
                is_read=False
            ).update(is_read=True)

            # Create the new message
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                image=image
            )

    return redirect('messages')

# ---------------------------------------------------------------
# Context Processor (Unread Message Count)
# ---------------------------------------------------------------
@csrf_exempt
def unread_message_count(request):
    unread_count = 0
    if request.user.is_authenticated:
        # Count messages where the user is the recipient and is_read=False
        unread_count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    return {'unread_message_count': unread_count}

















from django.utils.dateparse import parse_date  # ✅ Import parse_date

@staff_member_required
def admin_products(request):
    products = Product.objects.all().prefetch_related('product_images')

    # Get filter values from request
    category = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    out_of_stock = request.GET.get('out_of_stock', '')

    # Apply category filter
    if category:
        products = products.filter(category=category)

    # Apply date range filter
    if start_date and end_date:
        start_date = parse_date(start_date)  # ✅ This will now work
        end_date = parse_date(end_date)
        if start_date and end_date:
            products = products.filter(created_at__range=[start_date, end_date])

    # Apply out-of-stock filter
    if out_of_stock == '1':
        products = products.filter(stock=0)

    return render(request, 'admin/products.html', {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'selected_category': category,
        'start_date': start_date,
        'end_date': end_date,
        'out_of_stock': out_of_stock
    })




@staff_member_required
def admin_orders(request):
    today = timezone.now().date()

    # Get filter parameters from request
    status_filter = request.GET.get('status', None)
    delivery_status_filter = request.GET.get('delivery_status', None)
    date_filter = request.GET.get('date', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    # Optimize query with select_related & prefetch_related
    orders = Order.objects.prefetch_related(
        'order_items__product'  # Prefetch related products
    ).select_related(
        'customer__user'  # Select related customer and user data
    )

    # Apply filters
    if status_filter:
        orders = orders.filter(payment_status=status_filter)

    if delivery_status_filter:
        orders = orders.filter(delivery_status=delivery_status_filter)

    if date_filter == 'today':
        orders = orders.filter(ordered_at__date=today)

    if start_date and end_date:
        orders = orders.filter(ordered_at__date__range=[start_date, end_date])

    # Order by newest orders first
    orders = orders.order_by('-ordered_at')

    return render(request, 'admin/orders.html', {'orders': orders})



























@staff_member_required
def admin_users(request):
    users = User.objects.select_related('customer').all()
    return render(request, 'admin/users.html', {'users': users})

@staff_member_required
def admin_messages(request):
    messages = Message.objects.select_related('sender', 'recipient').all()
    return render(request, 'admin/messages.html', {'messages': messages})

@staff_member_required
def admin_team(request):
    team = TeamMember.objects.all()
    return render(request, 'admin/team.html', {'team': team})




# Product Views
@staff_member_required
@csrf_exempt
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # Handle images
            for file in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=file)
            messages.success(request, 'Product added successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'admin/product_form.html', {'form': form})

from django.db import transaction











@staff_member_required
@csrf_exempt
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            with transaction.atomic():  # Ensure atomic update
                form.save()

                # Handle additional image uploads
                if request.FILES.getlist('images'):
                    for file in request.FILES.getlist('images'):
                        ProductImage.objects.create(product=product, image=file)
                
                # Update main image selection
                main_image_id = request.POST.get('main_image')
                if main_image_id and ProductImage.objects.filter(id=main_image_id, product=product).exists():
                    ProductImage.objects.filter(product=product).update(main_image=False)
                    ProductImage.objects.filter(id=main_image_id).update(main_image=True)
                
                messages.success(request, 'Product updated successfully!')
                return redirect('admin_products')
        else:
            messages.error(request, 'There was an error updating the product.')

    else:
        form = ProductForm(instance=product)

    return render(request, 'admin/product_form.html', {'form': form, 'product': product})



@staff_member_required
@csrf_exempt
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, 'Product deleted successfully!')
            return redirect('admin_products')  # Redirect on successful DELETE

        except Exception as e:
            messages.error(request, f'Error deleting product: {e}')
            return redirect('admin_products')  # Redirect even on error

    elif request.method == 'GET':  # Explicitly handle GET requests
        messages.warning(request, "Cannot delete product via GET request. Use POST.")
        return redirect('admin_products')  # Redirect on GET

    else: # Handle other request methods (PUT, DELETE, etc.) if needed.
        messages.warning(request, "Invalid request method.")
        return redirect('admin_products')

# Team Member Views
@staff_member_required
@csrf_exempt
def add_team(request):
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member added successfully!')
            return redirect('admin_team')
    else:
        form = TeamMemberForm()
    return render(request, 'admin/team_form.html', {'form': form})

@staff_member_required
@csrf_exempt
def edit_team(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team member updated successfully!')
            return redirect('admin_team')
    else:
        form = TeamMemberForm(instance=member)
    return render(request, 'admin/team_form.html', {'form': form})

@staff_member_required
@csrf_exempt
def delete_team(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Team member deleted successfully!')
    return redirect('admin_team')



@staff_member_required
@csrf_exempt
def admin_users(request):
    users = User.objects.select_related('customer').all()
    return render(request, 'admin/users.html', {'users': users})

@staff_member_required
@csrf_exempt
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    customer, created = Customer.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        customer_form = CustomerForm(request.POST, request.FILES, instance=customer)

        if user_form.is_valid() and customer_form.is_valid():
            user_form.save()
            customer_form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('admin_users')
    else:
        user_form = UserForm(instance=user)
        customer_form = CustomerForm(instance=customer)

    return render(request, 'admin/edit_user.html', {
        'user_form': user_form,
        'customer_form': customer_form
    })




@login_required
@csrf_exempt
def edit_profile(request):
    customer = request.user.customer  # Get the logged-in user's associated customer profile

    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')  # Redirect to the same page after successful edit
    else:
        form = EditProfileForm(instance=request.user)  # Pre-fill the form with current user data

    return render(request, 'edit_profile.html', {'form': form, 'customer': customer})





@staff_member_required
@csrf_exempt
def admin_delete_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        # Optionally, perform any checks before deletion
        user.delete()
        messages.success(request, "User deleted successfully.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect('admin_users')  # Redirect back to the user list page


@staff_member_required
@csrf_exempt
def admin_messages(request):
    messages_list = Message.objects.select_related('sender', 'recipient').all()
    return render(request, 'admin/messages.html', {'messages': messages_list})

@staff_member_required
@csrf_exempt
def admin_view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.is_read = True
    message.save()
    return render(request, 'admin/view_message.html', {'message': message})

from django.http import HttpResponseForbidden


@staff_member_required
@csrf_exempt
def admin_delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST':
        message.delete()
        return redirect('admin_messages')  # Redirect to the list of messages (update this URL)

    return HttpResponseForbidden("Invalid request method.")  # Return an error for GET requests




@staff_member_required
def admin_product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Find order items related to this product
    order_items = OrderItem.objects.filter(product=product)

    return render(request, "admin/admin_product_detail.html", {
        "product": product,
        "order_items": order_items
    })





def admin_view_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(customer__user=user)
    messages = Message.objects.filter(sender=user)
    comments = Comment.objects.filter(user=user)
    liked_products = user.liked_products.all()
    return render(request, 'admin/view_user.html', {
        'user': user,
        'orders': orders,
        'messages': messages,
        'comments': comments,
        'liked_products': liked_products
    })

def admin_search(request):
    query = request.GET.get('query', '')

    # Search logic: You can search across multiple models
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__icontains=query)
    )

    # Search in Orders (including searching product names related to orders)
    orders = Order.objects.filter(
        Q(customer__user__username__icontains=query) |
        Q(order_items__product__name__icontains=query)  # Corrected to reference `order_items` and `product`
    ).prefetch_related('order_items')  # Prefetch order_items for efficient querying

    # Search in Users
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )

    messages = Message.objects.filter(
        Q(sender__username__icontains=query) |
        Q(recipient__username__icontains=query) |
        Q(content__icontains=query)
    )

    team_members = TeamMember.objects.filter(
        Q(name__icontains=query) |
        Q(role__icontains=query)
    )

    return render(request, 'admin/admin_search_results.html', {
        'query': query,
        'products': products,
        'orders': orders,
        'users': users,
        'messages': messages,
        'team_members': team_members,
    })



@login_required
@csrf_exempt
def payment_method(request, order_id):
    # Fetch the order by order_id
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)

        if form.is_valid():
            # Save payment details in order
            order.payment_message = form.cleaned_data['payment_message']
            order.payment_image = form.cleaned_data.get('payment_image')

            # Check if payment message or image is provided before setting payment status
            if order.payment_message or order.payment_image:
                order.payment_status = 'Pending'  # Only set to "Pending" if either message or image is provided
            else:
                order.payment_status = 'Not Provided'  # You can set this to any status you prefer if no payment info is provided
            order.save()

            # Set success message
            messages.success(request, f"Thank you {order.customer.user.username} for buying with us 🎉. Your payment is being processed. If approved, you will see a message. Thank you!")

            # Redirect to the order detail page
            return redirect('order_detail', order_id=order.id)

    else:
        form = PaymentForm()

    return render(request, 'store/payment_method.html', {'order': order, 'form': form})





@login_required
def order_detail(request, order_id):
    # Fetch the order by order_id and ensure it exists
    order = get_object_or_404(Order, id=order_id)

    # Get the associated order items
    order_items = order.order_items.all()

    # Pass the order, order_items, and payment status to the template
    return render(request, 'store/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'payment_status': order.payment_status,  # Pass payment status to the template
        'delivery_status': order.delivery_status,  # Pass delivery status to the template
    })









@login_required
@csrf_exempt
def payment_method(request, order_id):
    # Fetch the order by order_id
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)

        if form.is_valid():
            # Save payment details in the order
            order.payment_message = form.cleaned_data['payment_message']
            order.payment_image = form.cleaned_data.get('payment_image')

            # Set payment status to 'Pending' when details are submitted
            order.payment_status = 'Pending'
            order.save()

            # Set a success message
            messages.success(request, "Thank you for submitting your payment. Your payment is being processed. If approved, you'll receive a confirmation.")

            # Redirect to the order detail page
            return redirect('order_detail', order_id=order.id)

    else:
        form = PaymentForm()

    return render(request, 'store/payment_method.html', {'order': order, 'form': form})






# Approve Payment View
def approve_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.payment_status == 'Pending':  # Check if the payment is still pending
        order.payment_status = 'Confirmed'
        order.save()
    return redirect('admin_orders')  # Redirect to the order management page after approving*``




@staff_member_required
def admin_comment_list(request):
    product_id = request.GET.get('product_id')  # Get product ID from query parameters
    comments = Comment.objects.all().order_by('-timestamp')  # Default: all comments

    if product_id:
        comments = comments.filter(product_id=product_id)  # Filter by selected product

    products = Product.objects.all()  # Get all products for dropdown filter

    return render(request, 'admin/comments_list.html', {
        'comments': comments,
        'products': products,
        'selected_product_id': product_id
    })



@staff_member_required
def admin_view_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)  # Use Comment, not comment
    return render(request, 'admin/view_comment.html', {'comment': comment})

@staff_member_required
@csrf_exempt
def admin_edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)  # Use Comment, not comment
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment.content = content
            comment.save()
            return redirect('admin_comment_list')
    return render(request, 'admin/edit_comment.html', {'comment': comment})

@staff_member_required
@csrf_exempt
def admin_delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)  # Use Comment, not comment
    if request.method == 'POST':
        comment.delete()
        return redirect('admin_comment_list')
    return HttpResponseForbidden("Invalid request method.")

@login_required
def cancel_order(request, order_id):
    # Retrieve the order or return a 404 error if not found
    order = get_object_or_404(Order, id=order_id)

    # Check if order is still pending or processing before deleting
    if order.delivery_status in ['Pending', 'Processing']:
        # Delete the order from the database
        order.delete()
        messages.success(request, f"Your order #{order.id} has been deleted successfully.")
    else:
        messages.error(request, "You cannot cancel an order that has already been shipped or delivered.")

    return redirect('order_list')  # Redirect to a list of orders or a suitable page






def confirm_delivery(request, order_id):
    # Fetch the order using the provided order_id
    order = get_object_or_404(Order, id=order_id)

    # Only allow confirmation if payment is confirmed and status is not already 'Delivered'
    if order.payment_status == 'Confirmed' and order.delivery_status != 'Delivered':
        order.delivery_status = 'Delivered'
        order.save()
        messages.success(request, f"Order #{order.id} has been delivered successfully.")
    else:
        messages.error(request, f"Order #{order.id} cannot be delivered yet.")

    return redirect('admin_order_detail', order_id=order.id)



@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Debugging
    print(f"Fetching order: {order}")
    print(f"Order items count: {order.order_items.count()}")

    order_items = order.order_items.all()

    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'store/order_detail.html', context)




def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/order_detail.html', {'order': order})

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, "Order deleted successfully.")
    return redirect('admin_orders')










def admin_dashboard(request):
    # Key Metrics
    total_customers = Customer.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='Confirmed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_products = Product.objects.count()
    total_comments = Comment.objects.count()
    unread_messages = Message.objects.filter(is_read=False).count()

    # Aggregating orders by delivery_status and payment_status separately
    orders_by_status = list(Order.objects.values('delivery_status', 'payment_status')
                            .annotate(count=Count('id')))

    # Adjusting the aggregation to group the counts of both Pending and Confirmed payments for each delivery_status
    delivery_status_counts = {}
    for order in orders_by_status:
        delivery_status = order['delivery_status']
        payment_status = order['payment_status']
        if delivery_status not in delivery_status_counts:
            delivery_status_counts[delivery_status] = {'Pending': 0, 'Confirmed': 0}

        if payment_status == 'Pending':
            delivery_status_counts[delivery_status]['Pending'] += order['count']
        elif payment_status == 'Confirmed':
            delivery_status_counts[delivery_status]['Confirmed'] += order['count']

    # Now we can prepare the data to display
    orders_by_status_cleaned = [
        {
            'delivery_status': delivery_status,
            'pending_count': counts['Pending'],
            'confirmed_count': counts['Confirmed']
        }
        for delivery_status, counts in delivery_status_counts.items()
    ]

    # Aggregating revenue by category - joining OrderItem model
    revenue_by_category = list(Product.objects
        .values('category')
        .annotate(total_sales=Sum('orderitem__subtotal'))
        .filter(orderitem__order__payment_status='Confirmed'))  # Ensure we're only considering confirmed orders

    # Convert Decimal values to float
    revenue_by_category = [
        {**item, 'total_sales': float(item['total_sales']) if item['total_sales'] else 0}
        for item in revenue_by_category
    ]

    # Serialize the data to JSON format
    orders_by_status_json = json.dumps(orders_by_status_cleaned)
    revenue_by_category_json = json.dumps(revenue_by_category)

    # Add more data for the template if needed
    top_selling_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]

    most_liked_products = Product.objects.annotate(
        like_count=Count('likes')
    ).order_by('-like_count')[:5]

    top_customers = Customer.objects.annotate(
        total_spent=Sum('order__total_price')
    ).order_by('-total_spent')[:5]

    new_customers = Customer.objects.filter(
        user__date_joined__gte=datetime.today() - timedelta(days=30)
    ).order_by('-user__date_joined')[:5]

    low_stock_products = Product.objects.filter(stock__lt=10)

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'total_comments': total_comments,
        'unread_messages': unread_messages,
        'orders_by_status': orders_by_status_json,
        'revenue_by_category': revenue_by_category_json,
        'top_selling_products': top_selling_products,
        'most_liked_products': most_liked_products,
        'top_customers': top_customers,
        'new_customers': new_customers,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'admin/dashboard.html', context)



@staff_member_required
def all_products(request):

    products = Product.objects.all()

    return render(request, 'admin/all_products.html', {'products': products})



def sold_products_list(request):

    products = Product.objects.all().annotate(
        total_sold=Sum('orderitem__quantity')
    )
    return render(request, 'admin/sold_products_list.html', {'products': products})


def all_customers(request):
    # Fetch all customers ordered by the most recent registration date
    customers = Customer.objects.all().order_by('-user__date_joined')  # Ordering by the related User's join date

    return render(request, 'admin/all_customers.html', {'customers': customers})





def customer_contributions(request):
    # Annotate each customer with their total spending
    customers = Customer.objects.annotate(
        total_spent=Sum('order__total_price', filter=Q(order__payment_status='Confirmed'))
    ).order_by('-total_spent')

    return render(request, 'admin/customer_contributions.html', {'customers': customers})









# Password Reset View (The form to request a password reset)
class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

# Password Reset Done View (Confirmation that a reset link has been sent)
class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

# Password Reset Confirm View (Set a new password via token)
class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

# Password Reset Complete View (Confirmation that the password has been reset successfully)
class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


# In case you want a custom password reset form, here is an example:
def custom_password_reset_form(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Custom logic (for example, send a custom email)
            user = User.objects.filter(email=email).first()
            if user:
                # Send custom password reset email here
                send_mail(
                    'Password Reset Request',
                    'Here is your reset link: http://example.com/reset_link',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                return HttpResponse("Password reset email has been sent!")
    else:
        form = PasswordResetForm()
    return render(request, 'registration/password_reset_form.html', {'form': form})

# List all advertisements
def advertisement_list(request):
    advertisements = Advertisement.objects.all().order_by('-start_date')
    return render(request, 'admin/advertisement_list.html', {'advertisements': advertisements})



# Create a new advertisement
def create_advertisement(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Advertisement created successfully!")
            return redirect('advertisement_list')
    else:
        form = AdvertisementForm()
    return render(request, 'admin/advertisement_form.html', {'form': form})

# Edit an existing advertisement
def edit_advertisement(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES, instance=advertisement)
        if form.is_valid():
            form.save()
            messages.success(request, "Advertisement updated successfully!")
            return redirect('advertisement_list')
    else:
        form = AdvertisementForm(instance=advertisement)
    return render(request, 'admin/advertisement_form.html', {'form': form})

# Delete an advertisement
def delete_advertisement(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk)
    advertisement.delete()
    messages.success(request, "Advertisement deleted successfully!")
    return redirect('advertisement_list')



from .models import Notification

# List all notifications
def notification_list(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'admin/notification_list.html', {'notifications': notifications})



def create_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)  # Save notification without committing to DB
            notification.save()  # Save to get an ID

            # Handle recipient selection
            if form.cleaned_data.get('for_all_customers'):
                notification.user.set(User.objects.filter(is_staff=False))  # Assign to non-staff users (customers)
            elif form.cleaned_data.get('for_all_staff'):
                notification.user.set(User.objects.filter(is_staff=True))  # Assign to staff members
            else:
                selected_users = form.cleaned_data.get('users')
                if selected_users:
                    notification.user.set(selected_users)  # Assign only selected users
                else:
                    form.add_error('users', 'Please select at least one recipient.')

            notification.save()  # Save the notification with assigned users
            return redirect('notification_list')  # Redirect after saving
    else:
        form = NotificationForm()

    return render(request, 'admin/notification_form.html', {'form': form})


def edit_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)  # Get the notification to edit

    if request.method == 'POST':
        form = NotificationForm(request.POST, instance=notification)  # Pre-fill the form with existing data

        if form.is_valid():
            notification = form.save(commit=False)  # Don't save yet; we'll handle related fields manually

            # Safely check for the 'for_all' field in the cleaned data
            for_all = form.cleaned_data.get('for_all', False)  # Default to False if not present
            if for_all:
                notification.user.set(User.objects.all())  # Assign all users to this notification
            else:
                # If specific users are selected, assign them
                selected_users = form.cleaned_data.get('users', [])
                if selected_users:
                    notification.user.set(selected_users)  # Assign specific users
                else:
                    notification.user.clear()  # Clear users if none are selected

            notification.save()  # Save the notification after assigning users

            messages.success(request, "Notification updated successfully!")  # Success message
            return redirect('notification_list')  # Redirect to the notification list page

    else:
        # For GET requests, load the form with existing data
        form = NotificationForm(instance=notification)

    return render(request, 'admin/notification_form.html', {'form': form})







# Delete a notification
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.delete()
    messages.success(request, "Notification deleted successfully!")
    return redirect('notification_list')


# Bulk delete notifications
def delete_selected_notifications(request):
    if request.method == "POST":
        notification_ids = request.POST.getlist('notification_ids')  # Get selected notification IDs
        if notification_ids:
            Notification.objects.filter(id__in=notification_ids).delete()  # Delete selected notifications
            messages.success(request, "Selected notifications deleted successfully!")
        else:
            messages.warning(request, "No notifications selected!")

    return redirect('notification_list')  # Redirect back to list

