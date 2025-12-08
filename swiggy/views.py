from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, User
from .serializers import MenuItemSerializer, RestaurantSerializer, CartItemSerializer


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

    serializer = MenuItemSerializer(items, many=True)
    return Response(serializer.data)


# restaurant add their menu list 
@api_view(['POST'])
def add_menu(request):
    user = request.user
    if user.role != "RESTAURANT_OWNER":
        return Response({"error": "Only restaurant owners can add menus"}, status=403)

    restaurant = Restaurant.objects.filter(owner=user).first()

    data = request.data.copy()
    data["restaurant"] = restaurant.id

    serializer = MenuItemSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors)


# update the menu list
@api_view(['PUT', 'PATCH'])
def update_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    if request.user != menu_item.restaurant.owner:
        return Response({"error": "You cannot update this menu"}, status=403)

    serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors)

# list all menus
@api_view(['GET'])
def list_menu(request):
    menu_items = MenuItem.objects.all()
    serializer = MenuItemSerializer(menu_items, many=True)
    return Response(serializer.data)

# delete menu
@api_view(['DELETE'])
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    if request.user != menu_item.restaurant.owner:
        return Response({"error": "Unauthorized"}, status=403)

    menu_item.delete()
    return Response({"message": "Menu deleted"})


# add to cart
@api_view(['POST'])
def add_to_cart(request):
    menu_id = request.data.get("menu_item")
    qty = int(request.data.get("quantity", 1))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={'quantity': qty}
    )

    if not created:
        cart_item.quantity += qty
        cart_item.save()

    return Response({"message": "Item added to cart"})


# remove from cart
@api_view(['POST'])
def remove_from_cart(request):
    item_id = request.data.get("item_id")
    cart_item = get_object_or_404(CartItem, user=request.user, item_id=item_id)
    cart_item.delete()

    return Response({"message": "Item removed from cart"})

# view cart
@api_view(['GET'])
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)

    total = sum([c.subtotal for c in cart_items])

    data = [{
        "item": c.item.name,
        "price": float(c.item.price),
        "quantity": c.quantity,
        "subtotal": float(c.subtotal)
    } for c in cart_items]

    return Response({
        "items": data,
        "total": float(total)
    })

# place order
@api_view(['POST'])
def place_order(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()

    if not items.exists():
        return Response({"error": "Cart is empty"}, status=400)

    total = sum(i.subtotal for i in items)

    order = Order.objects.create(
        user=request.user,
        total_amount=total,
        status="PENDING"
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            menu_item=item.menu_item,
            quantity=item.quantity,
            price=item.menu_item.price
        )

    items.delete()

    return Response({"message": "Order placed", "order_id": order.id})


# update order status
@api_view(['POST'])
def update_order_status(request, order_id):
    new_status = request.data.get("status")

    order = get_object_or_404(Order, id=order_id)

    # Allowed workflow
    WORKFLOW = {
        "PENDING": "ACCEPTED",
        "ACCEPTED": "PREPARING",
        "PREPARING": "OUT_FOR_DELIVERY",
        "OUT_FOR_DELIVERY": "DELIVERED",
    }

    current = order.status

    # Validate status
    if current not in WORKFLOW:
        return Response({"error": "Invalid current status"}, status=400)

    expected_next = WORKFLOW[current]

    if new_status != expected_next:
        return Response({
            "error": "Invalid status update",
            "allowed_next_status": expected_next
        }, status=400)

    # Update
    order.status = new_status
    order.save()

    return Response({
        "message": "Order status updated",
        "order_id": order.id,
        "previous_status": current,
        "new_status": new_status
    })

# admin manage users 
@api_view(['GET'])
def admin_list_users(request):
    users = User.objects.all()
    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
        }
        for u in users
    ]
    return Response(data)

# admin list restaurants 
@api_view(['GET'])
def admin_list_all_restaurants(request):
    restaurants = Restaurant.objects.all()
    serializers = RestaurantSerializer(restaurants, many=True)
    return Response(serializers.data)

# admin update restaurants
@api_view(['PUT'])
def admin_update_restaurants(request,restaurant_id):
    restaurant = Restaurant.objects.filter(id=restaurant_id).first()
    if not restaurant:
        return Response({"error":"Restaurant not found"})
    serializers = RestaurantSerializer(restaurant,data=request.data)

    if serializers.is_valid():
        serializers.save()
        return Response(serializers.data)
    return Response(serializers.errors)

# admin delete restaurants
@api_view(['PUT'])
def admin_delete_restaurants(request,restaurant_id):
    restaurant = Restaurant.objects.filter(id=restaurant_id).first()
    if not restaurant:
        return Response({"error":"Restaurant not found"})
    restaurant.delete()
    return Response({"message":"Restaurant deleted successfully"})

# admin list all orders
@api_view(['GET'])
def admin_list_orders(request):
    orders = Order.objects.all().order_by('-created_at')

    data = [
        {
            "id": o.id,
            "user": o.user.username,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "created_at": o.created_at,
        }
        for o in orders
    ]
    return Response(data)