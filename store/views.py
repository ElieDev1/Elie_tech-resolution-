from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from .models import *
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q, Count

from django.core.paginator import Paginator

from .forms import *



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
        # Capture data from the form
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST['phone']
        address = request.POST['address']

        # Create the user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        
        # Optionally, save the phone and address in a custom model (Customer)
        customer = Customer.objects.create(
            user=user,
            phone_number=phone,
            address=address
        )

        # Provide feedback and redirect
        messages.success(request, 'Account created successfully!')
        return redirect('login')  # Redirect to login page or wherever you want

    return render(request, 'store/register.html')


@csrf_exempt
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

@csrf_exempt
def logout_user(request):
    logout(request)
    return redirect('home')


# Product List





# Profile View
@login_required
def profile_view(request):
    customer = get_object_or_404(Customer, user=request.user)
    return render(request, 'profile.html', {'customer': customer})



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Order, Customer

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
        if cart[product_id_str] > 1:
            cart[product_id_str] -= 1
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



@login_required
@csrf_exempt
def process_checkout(request):
    cart = request.session.get('cart', {})
    total_price = 0

    # Create a new order
    order = Order.objects.create(customer=request.user.customer, total_price=total_price)

    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=int(product_id))
            quantity = item_data['quantity']
            subtotal = product.price * quantity
            total_price += subtotal

            # Create OrderItem and add it to the order
            OrderItem.objects.create(order=order, product=product, quantity=quantity, subtotal=subtotal)

        except Product.DoesNotExist:
            continue  # Skip missing products

    # Update the total price after adding all items
    order.total_price = total_price
    order.save()

    # Clear the cart after the order is created
    request.session['cart'] = {}
    request.session.modified = True

    # Redirect to the order details page
    return redirect('order_detail', order_id=order.id)






















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





















from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    context = {
        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'order_items': OrderItem.objects.count(),  # Fixed typo in context key
        'users': User.objects.count(),
        'pending_orders': Order.objects.filter(payment_status='Pending')  # Updated to use payment_status
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def admin_products(request):
    products = Product.objects.all().prefetch_related('product_images')
    return render(request, 'admin/products.html', {'products': products})

from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_orders(request):
    # Use prefetch_related to fetch related products via OrderItem
    orders = Order.objects.prefetch_related(
        'order_items__product'  # Prefetch related products through the order_items relation
    ).select_related(
        'customer__user'  # Select related customer and user data
    ).order_by('-ordered_at')  # Order by the ordered_at field in descending order (newest first)

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

@staff_member_required
@csrf_exempt
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            # Handle image updates
            if request.FILES.getlist('images'):
                ProductImage.objects.filter(product=product).delete()
                for file in request.FILES.getlist('images'):
                    ProductImage.objects.create(product=product, image=file)
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin/product_form.html', {'form': form})

@staff_member_required
@csrf_exempt
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
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
            return redirect('edit_profile')  # Redirect to the same page after successful edit
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


@staff_member_required  # Ensures only admin users can access this page
def admin_view_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'admin/view_product.html', {'product': product})







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



from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def admin_comment_list(request):
    comments = Comment.objects.all().order_by('-timestamp')  # Use Comment, not comment
    return render(request, 'admin/comments_list.html', {'comments': comments})

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














def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/order_detail.html', {'order': order})

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, "Order deleted successfully.")
    return redirect('admin_orders')

























