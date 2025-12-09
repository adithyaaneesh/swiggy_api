from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("RESTAURANT_OWNER", "Restaurant Owner"),
        ("DELIVERY_PARTNER", "Delivery Partner"),
        ("CUSTOMER", "Customer"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="CUSTOMER")
    phone = models.CharField(max_length=20, null=True, blank=True)

class Restaurant(models.Model):
    CATEGORY_CHOICES = [
        ("salad", "Salad"),
        ("breakfast", "Breakfast"),
        ("lunch", "Lunch"),
        ("dinner", "Dinner"),
        ("snacks", "Snacks"),
        ("shakes", "Shakes"),
        ("desert", "Desert"),
        ("ice-cream", "Ice Cream"),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="restaurants")
    restaurant_name = models.CharField(max_length=100)
    restaurant_address = models.TextField(max_length=255)
    rest_phonenum = models.CharField(max_length=15)
    rest_email = models.EmailField(max_length=100)
    rating = models.FloatField(default=0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.restaurant_name

class MenuItem(models.Model):
    FOOD_TYPE_CHOICES = [
        ('veg', "Veg"),
        ('non-veg', "Non-Veg"),
    ]
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="menu_images/", null=True, blank=True)
    is_available = models.BooleanField(default=True)
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"{self.user.username}'s Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE,null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("PREPARING", "Preparing"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class RatingReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'restaurant')

    def __str__(self):
        return f"{self.user} → {self.restaurant} : {self.rating}"
