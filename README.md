# 📱 Electronics Inventory Management System

A complete inventory management system for electronics products like Mobile Phones, Laptops, and Accessories.

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/your-username/electronics-inventory-system)
![GitHub stars](https://img.shields.io/github/stars/your-username/electronics-inventory-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-username/electronics-inventory-system?style=social)
![GitHub license](https://img.shields.io/badge/license-MIT-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Celery](https://img.shields.io/badge/Celery-5.3-green)
![Redis](https://img.shields.io/badge/Redis-7.0-red)

</div>

---

## 📌 Table of Contents

- [🎯 Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [📸 Screenshots](#-screenshots)
- [🚀 Installation](#-installation)
- [📁 Project Structure](#-project-structure)
- [🔧 Configuration](#-configuration)
- [💳 Payment Integration](#-payment-integration)
- [🌐 API Endpoints](#-api-endpoints)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📞 Contact](#-contact)

---

## 🎯 Features

### 🔐 Authentication & Users
- ✅ User Registration & Login
- ✅ Password Reset
- ✅ Role-based Access (Admin, Manager, Staff)
- ✅ Profile Management

### 📦 Product Management
- ✅ Add/Edit/Delete Products
- ✅ Category Management
- ✅ Stock Tracking & Alerts
- ✅ Barcode / SKU Generation
- ✅ Product Images & Gallery
- ✅ Product Specifications & Highlights

### 🛒 Shopping Cart
- ✅ Add to Cart / Remove from Cart
- ✅ Quantity Update
- ✅ Cart Persistence (Session-based)
- ✅ Cart Summary & Total

### 💳 Payment Integration
- ✅ SSLCommerz Payment Gateway
- ✅ COD (Cash on Delivery)
- ✅ bKash, Nagad, Card Payment
- ✅ Secure Checkout

### 📊 Dashboard & Reports
- ✅ Sales Reports
- ✅ Stock Reports
- ✅ Low Stock Alerts
- ✅ Order Management
- ✅ Customer Management

### ⚡ Background Tasks (Celery)
- ✅ Email Notifications (Async)
- ✅ Order Processing (Async)
- ✅ Stock Update Alerts
- ✅ Scheduled Reports
- ✅ Database Backup Automation

### 📱 Responsive Design
- ✅ Mobile First Design
- ✅ Fully Responsive
- ✅ Cross-browser Compatible

---

## 🛠️ Tech Stack

<div align="center">

### 🎨 **Frontend**

<img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
<img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
<img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
<img src="https://img.shields.io/badge/Font_Awesome-339AF0?style=for-the-badge&logo=fontawesome&logoColor=white" />
<img src="https://img.shields.io/badge/Google_Fonts-4285F4?style=for-the-badge&logo=googlefonts&logoColor=white" />

### ⚙️ **Backend**

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
<img src="https://img.shields.io/badge/Django_REST-ff1709?style=for-the-badge&logo=django&logoColor=white" />

### 🗄️ **Database & Cache**

<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
<img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
<img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />

### ⚡ **Task Queue & Background Jobs**

<img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" />
<img src="https://img.shields.io/badge/Flower-FF6C00?style=for-the-badge&logo=flower&logoColor=white" />
<img src="https://img.shields.io/badge/Celery_Beat-37814A?style=for-the-badge&logo=celery&logoColor=white" />

### 💳 **Payment Gateway**

<img src="https://img.shields.io/badge/SSLCommerz-FF6C00?style=for-the-badge&logo=sslcommerz&logoColor=white" />
<img src="https://img.shields.io/badge/bKash-FF6600?style=for-the-badge&logo=bkash&logoColor=white" />
<img src="https://img.shields.io/badge/Nagad-FF6600?style=for-the-badge&logo=nagad&logoColor=white" />

### 🛠️ **DevOps & Tools**

<img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" />
<img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" />
<img src="https://img.shields.io/badge/Ngrok-1F1E37?style=for-the-badge&logo=ngrok&logoColor=white" />
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />

### 🧪 **Testing**

<img src="https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" />

</div>

---

Step 4: Install & Run Redis

# Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis

# Linux/Mac
sudo apt-get install redis-server
sudo service redis-server start

# Or using Docker
docker run -d -p 6379:6379 redis


Step 9: Start Celery Worker & Beat (in separate terminals)

# Terminal 1 - Celery Worker
celery -A config worker -l info

# Terminal 2 - Celery Beat (Scheduler)
celery -A config beat -l info

# Terminal 3 - Flower (Monitoring)
celery -A config flower --port=5555

Celery Configuration:
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


settings.py (Celery) :

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_BEAT_SCHEDULE = {
    'send-low-stock-alerts': {
        'task': 'products.tasks.send_low_stock_alerts',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'generate-daily-sales-report': {
        'task': 'order.tasks.generate_daily_sales_report',
        'schedule': crontab(hour=23, minute=59),  # Daily at 11:59 PM
    },
    'backup-database': {
        'task': 'core.tasks.backup_database',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}


Celery Tasks Example :

# products/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Product

@shared_task
def send_low_stock_alerts():
    """Send email alerts for low stock products"""
    low_stock_products = Product.objects.filter(
        quantity__lte=models.F('min_stock_level')
    )
    
    if low_stock_products.exists():
        message = "Low Stock Alert:\n\n"
        for product in low_stock_products:
            message += f"- {product.name}: {product.quantity} left (Min: {product.min_stock_level})\n"
        
        send_mail(
            subject='Low Stock Alert',
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['admin@example.com'],
            fail_silently=False,
        )
    return f"Sent alert for {low_stock_products.count()} products"


    💳 Payment Integration:

    SSLCommerz
* Register at SSLCommerz

* Get Store ID & Store Password

* Set SSL_IS_SANDBOX=True for testing

Test Cards:

* VISA: 4111111111111111

* MasterCard: 5111111111111111

* Amex: 371111111111114

bKash
* Register at bKash Developer

* Get App Key & App Secret

* Test Account: 017XXXXXXXX (Sandbox)

Nagad
* Register at Nagad Developer

* Get Merchant ID & API Key

🌐 API Endpoints
📦 Products API
Method	Endpoint	Description
GET	/api/products/	Get all products
GET	/api/products/{id}/	Get a specific product
GET	/api/products/{id}/detail/	Get product details (alternative)
GET	/api/products/low_stock/	Get all low stock products
GET	/api/products/out_of_stock/	Get all out of stock products
POST	/api/products/	Create a new product
PUT	/api/products/{id}/	Update a product
DELETE	/api/products/{id}/	Delete a product
📂 Categories API
Method	Endpoint	Description
GET	/api/categories/	Get all categories
GET	/api/categories/{id}/	Get a specific category
🛒 Cart API
Method	Endpoint	Description
GET	/api/cart/	View cart
POST	/api/cart/	Add item to cart
PUT	/api/cart/	Update cart quantity
DELETE	/api/cart/	Remove item from cart
POST	/api/cart/clear/	Clear entire cart
GET	/api/cart/count/	Get cart item count
👤 Customers API
Method	Endpoint	Description
GET	/api/customer/	Get all customers
GET	/api/customer/{id}/	Get a specific customer
📦 Orders API
Method	Endpoint	Description
GET	/api/orders/	Get all orders
GET	/api/orders/{id}/	Get a specific order
💳 Checkout API
Method	Endpoint	Description
POST	/checkout/api/initiate/	Initiate payment


