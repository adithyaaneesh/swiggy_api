from django.db import models
from django.contrib.auth.models import User
# Create your models here.


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
    restaurant_name = models.CharField(max_length=100)
    restaurant_address = models.TextField(max_length=255)
    rest_phonenum = models.PositiveIntegerField()
    rest_email = models.EmailField(max_length=100)
    rating = models.FloatField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.restaurant_name

class MenuItem(models.Model):
    FOOD_TYPE_CHOICES = [
        ('veg', "Veg"),
        ('non-veg', "Non-Veg"),
    ]

    restaurant_name = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="menu_images/")
    is_available = models.BooleanField(default=True)
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, default='veg')

    def __str__(self):
        return f"{self.name} - {self.food_type}"
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart - {self.user.username}"

class FoodItem(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.item.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("PREPARING", "Preparing"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
