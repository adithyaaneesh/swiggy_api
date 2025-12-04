from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Restaurant, MenuItem, Cart, CartItem
from .serializers import RestaurantSerializer, MenuItemSerializers, CartItemSerializer
# Create your views here.


# list restaurants
@api_view(['GET'])
def list_all_restaurants(request):
    restaurants = Restaurant.objects.all()
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data)

# search a restaurant by its name
@api_view(['GET'])
def search_restaurant(request):
    restaurant_name = request.GET.get("restaurant_name", "")
    if not restaurant_name:
        return Response({"error": "Please provide a valid restaurant name"})
    restaurant = Restaurant.objects.filter(restaurant_name__icontains=restaurant_name)
    serializer = RestaurantSerializer(restaurant, many=True)
    if restaurant.exists():
        return Response(serializer.data)
    return Response({"message": "No restaurant found matching the search."})

# filter by price, rating and category
@api_view(['GET'])
def menu_items_filter(request):
    items = MenuItem.objects.all()

    # FILTER BY PRICE
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        items = items.filter(price__gte=min_price)
    if max_price:
        items = items.filter(price__lte=max_price)

    # FILTER BY CATEGORY (Restaurant category)
    category = request.GET.get('category')
    if category:
        items = items.filter(restaurant__category__iexact=category)

    # FILTER BY RATING (Restaurant rating)
    min_rating = request.GET.get('min_rating')
    if min_rating:
        items = items.filter(restaurant__rating__gte=min_rating)

    serializer = MenuItemSerializers(items, many=True)
    return Response(serializer.data)


# restaurant add their menu list 
@api_view(['POST'])
def add_menu(request):
    is_many = isinstance(request.data, list)
    serializer = MenuItemSerializers(data=request.data, many=is_many)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

# update the menu list
@api_view(['PUT', 'PATCH'])
def update_menu(request,menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)
    partial_update = request.method == 'PATCH'
    serializer = MenuItemSerializers(instances = menu_item, data=request.data, partial=partial_update)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

# list all menus
@api_view(['GET'])
def list_menu(request):
    menu_items = MenuItem.objects.all()
    serializer = MenuItemSerializers(menu_items, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)
    menu_item.delete()
    return Response({"message": f"Item {menu_id} deleted successfully!!!"})


@api_view(['POST'])
def add_to_cart(request):
    user = request.user
    # Ensure user has a cart
    cart, created = Cart.objects.get_or_create(user=user)

    menu_item_id = request.data.get('menu_item')
    quantity = request.data.get('quantity', 1)

    menu_item = get_object_or_404(MenuItem, id=menu_item_id)

    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
    if not created:
        cart_item.quantity += int(quantity)
        cart_item.save()
    else:
        cart_item.quantity = int(quantity)
        cart_item.save()

    serializer = CartItemSerializer(cart_item)
    return Response({"message": "Item added to cart", "cart_item": serializer.data})


@api_view(['POST'])
def remove_from_cart(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    menu_item_id = request.data.get('menu_item')

    cart_item = CartItem.objects.filter(cart=cart, menu_item__id=menu_item_id).first()
    if not cart_item:
        return Response({"error": "Item not in cart"})

    cart_item.delete()
    return Response({"message": "Item removed from cart"})