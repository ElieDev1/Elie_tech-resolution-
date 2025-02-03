from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from .models import *
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from collections import defaultdict
from django.core.paginator import Paginator
from decimal import Decimal



def home(request):
    # Products with like counts (for the main grid)
    products_with_likes = Product.objects.annotate(likes_count=Count('likes')).order_by('-likes_count')

    # All products (for the carousel)
    all_products = Product.objects.all()

    # Categories with product counts
    categories = Product.CATEGORY_CHOICES
    product_counts = {
        category[0]: Product.objects.filter(category=category[0]).count()
        for category in categories
    }

    context = {
        'products_with_likes': products_with_likes,  # Key change
        'all_products': all_products,
        'categories': categories,
        'product_counts': product_counts,
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
            comment.objects.create(
                user=request.user,  # The user posting the comment
                product=product,
                content=comment_content
            )
        return redirect('product_detail', product_id=product.id)  # Redirect to avoid re-posting on refresh

    # Return the page with product details and comments
    return render(request, 'store/product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']

        user = User.objects.create_user(username=username, email=email, password=password)
        Customer.objects.create(user=user, phone_number=phone, address=address)

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'store/register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials!")
    
    return render(request, 'store/login.html')

def logout_user(request):
    logout(request)
    return redirect('home')


# Product List





# Profile View
@login_required
def profile_view(request):
    customer = get_object_or_404(Customer, user=request.user)
    return render(request, 'profile.html', {'customer': customer})





def order_list(request):
    # Retrieve all orders for the logged-in user
    orders = Order.objects.filter(customer=request.user.customer).order_by('ordered_at')

    # Group orders by rounded ordered_at time (e.g., rounded to the nearest minute)
    grouped_orders = {}
    for order in orders:
        # Round the ordered_at timestamp to the nearest minute (you can adjust as needed)
        order_time = order.ordered_at.replace(second=0, microsecond=0)

        if order_time not in grouped_orders:
            grouped_orders[order_time] = []
        grouped_orders[order_time].append(order)

    # Pass the grouped orders to the template
    return render(request, 'orders.html', {'grouped_orders': grouped_orders})




# Add comment functionality
@login_required
def add_comment(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        comment.objects.create(user=request.user, product=product, content=content)
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
    random_products = products.order_by('?')[:50]
    
    random_products_with_likes = [
        {
            'product': product,
            'likes': product.likes.count()
        }
        for product in random_products
    ]

    # Pagination for products (15 items per page)
    paginator = Paginator(random_products_with_likes, 15)  # 15 products per page
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




def add_to_cart(request, product_id):
    # Get or initialize the cart
    cart = request.session.get('cart', {})
    
    # Get the product with safety checks
    product = get_object_or_404(Product, id=product_id)
    
    # Validate stock availability
    if product.stock < 1:
        messages.error(request, "This product is out of stock!")
        return redirect('product_list')
    
    # Update cart quantity
    product_key = str(product_id)
    if product_key in cart:
        # Check if adding exceeds stock
        if cart[product_key]['quantity'] >= product.stock:
            messages.warning(request, f"Only {product.stock} units of {product.name} are available!")
            return redirect('cart_view')
        cart[product_key]['quantity'] += 1
    else:
        cart[product_key] = {'quantity': 1}
    
    # Persist cart in session
    request.session['cart'] = cart
    request.session.modified = True
    
    messages.success(request, f"{product.name} added to cart. Current quantity: {cart[product_key]['quantity']}")
    return redirect('product_list')  # Redirect  product list

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


def decrease_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Use string keys to match the template
    product_id_str = str(product_id)
    if product_id_str in cart:
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        else:
            del cart[product_id_str]  # Remove product if quantity is 1

    request.session['cart'] = cart
    request.session.modified = True  # Explicitly mark session as modified
    return redirect('cart_view')


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



@login_required
def checkout(request):
    # Retrieve the cart from session
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect('cart')  # Redirect to cart page

    # Initialize product details and total price
    products = []
    total_price = Decimal(0)

    # Ensure that cart is a dictionary and iterate through it
    if isinstance(cart, dict):
        for product_id, item in cart.items():
            try:
                # Ensure 'item' is a dictionary and contains the 'quantity' key
                if isinstance(item, dict) and 'quantity' in item:
                    product = Product.objects.get(id=product_id)
                    subtotal = product.price * item['quantity']
                    products.append({
                        'product': product,
                        'quantity': item['quantity'],
                        'subtotal': subtotal
                    })
                    total_price += subtotal
                else:
                    messages.error(request, f"Invalid cart item format for product ID {product_id}.")
                    continue  # Skip this item if it's not in the correct format
            except Product.DoesNotExist:
                messages.error(request, f"Product with ID {product_id} does not exist.")
                continue
    else:
        # Reset the cart if not a valid dictionary
        request.session['cart'] = {}
        messages.error(request, "Something went wrong with your cart.")
        return redirect('cart')

    # Handle POST request when user confirms the order
    if request.method == 'POST':
        customer = Customer.objects.get(user=request.user)
        
        # Create an order for each product in the cart
        for product_id, item in cart.items():
            if isinstance(item, dict) and 'quantity' in item:
                try:
                    product = Product.objects.get(id=product_id)  # Access product using the correct ID
                    total_price = product.price * item['quantity']
                    
                    order = Order.objects.create(
                        customer=customer,
                        product=product,
                        quantity=item['quantity'],
                        total_price=total_price,
                        payment_approved=False,  # Set to False until payment is confirmed
                    )
                except Product.DoesNotExist:
                    messages.error(request, f"Product with ID {product_id} does not exist.")
                    continue  # Skip this product if it does not exist

        # Empty the cart after checkout
        request.session['cart'] = {}

        messages.success(request, "Your order has been placed successfully. We will notify you once the payment is processed.")
        return redirect('order_list')  # Redirect to the order list page or any success page

    return render(request, 'store/checkout.html', {'products': products, 'total_price': total_price})



@login_required
def pay_order(request, order_id):
    # Retrieve the order by ID
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)

    # Check if the order is already paid
    if order.payment_approved:
        messages.info(request, "This order has already been paid for.")
        return redirect('order_list')

    # Process the payment here
    # For simplicity, let's assume the payment is successful
    order.payment_approved = True
    order.save()

    messages.success(request, "Payment successful!")
    return redirect('order_list')



@login_required
def order_list(request):
    # Get the Customer instance for the logged-in user
    customer = request.user.customer

    # Get all orders for the current user (via the Customer instance)
    orders = Order.objects.filter(customer=customer)

    # Group orders by their 'ordered_at' timestamp (date only for simplicity)
    grouped_orders = defaultdict(list)
    for order in orders:
        # Group by the formatted date (you can use strftime for more control)
        grouped_orders[order.ordered_at.strftime("%Y-%m-%d %H:%M:%S")].append(order)

    # Calculate the total price for each group and each order's subtotal
    order_groups = []
    for group_date, orders_in_group in grouped_orders.items():
        total_price_for_group = 0
        for order in orders_in_group:
            # Calculate subtotal (unit price * quantity)
            order.subtotal_price = order.product.price * order.quantity
            total_price_for_group += order.subtotal_price
        
        # Add the total price for the group to the context for rendering in the template
        order_groups.append({
            'group_date': group_date,
            'orders': orders_in_group,
            'total_price_for_group': total_price_for_group
        })

    context = {
        'grouped_orders': order_groups,
    }
    return render(request, 'store/order_list.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Message

# ---------------------------------------------------------------
# Message Page View
# ---------------------------------------------------------------
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
def unread_message_count(request):
    unread_count = 0
    if request.user.is_authenticated:
        # Count messages where the user is the recipient and is_read=False
        unread_count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    return {'unread_message_count': unread_count}