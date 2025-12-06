from rest_framework import serializers
from .models import Restaurant, MenuItem, CartItem


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"

class MenuItemSerializers(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"

class CartItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')
    menu_item_price = serializers.ReadOnlyField(source='menu_item.price')
    total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_price', 'quantity', 'total']
