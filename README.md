# Elie Tech

Elie Tech is an online electronics store built with Django. It allows customers to browse and order products, communicate via a chat system, and make payments using MTN MoMoPay. The platform also includes an admin panel for managing products, customers, orders, and messages.

## Features
- **Product Browsing & Ordering**: Customers can browse available products and place orders.
- **User Authentication**: Login, signup, and logout functionality.
- **Customer Management**: Track customer details and orders.
- **Chat System**: Customers can communicate with support.
- **Payments via MTN MoMoPay**: Payment codes available: `641647 (ELIE)` or `0790235414 (nizeyimana elie)`.
- **Admin Dashboard**: Manage products, customers, orders, messages, and comments.
- **Bootstrap-Styled Templates**: Responsive UI with `base.html` as the main template.

## Installation

### Prerequisites
Ensure you have the following installed on your system:
- Python 3.x
- Django
- PostgreSQL or SQLite (for database management)

### Setup
1. **Clone the repository:**
   ```sh
   git clone https://github.com/ElieDev1/elie-tech.git
   cd elie-tech
   ```
2. **Create a virtual environment and activate it:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run migrations:**
   ```sh
   python manage.py migrate
   ```
5. **Create a superuser (for admin access):**
   ```sh
   python manage.py createsuperuser
   ```
6. **Start the development server:**
   ```sh
   python manage.py runserver
   ```

## Usage
- Visit `http://127.0.0.1:8000/` to access the store.
- Log in as an admin at `http://127.0.0.1:8000/admin/`.
- Users can browse, order products, and communicate via chat.

## Models
- **Product**: Stores product details (name, description, price, stock, category, images, likes, comments).
- **ProductImage**: Manages product images, including a flag for the main image.
- **Customer**: Stores customer details (user, phone number, address, profile picture).
- **Order**: Tracks orders with relationships to `Customer` and `Product`.
- **Message**: Handles user-to-user communication.
- **Comment**: Allows users to comment on products.
- **TeamMember**: Represents team members with roles and images.

## Contributing
Contributions are welcome! Feel free to fork this repository, submit pull requests, or report issues.

## License
This project is licensed under the MIT License.

## Contact
For any inquiries, reach out via the chat system on the website or email `nizeyelie25@gmail.com`.

