from rest_framework import serializers
from .models import Restaurant, MenuItem, CartItem, RatingReview


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')
    menu_item_price = serializers.ReadOnlyField(source='menu_item.price')
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'menu_item_name',
                  'menu_item_price', 'quantity', 'subtotal']

class RatingReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RatingReview
        fields = ['id', 'user', 'user_name', 'restaurant', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']