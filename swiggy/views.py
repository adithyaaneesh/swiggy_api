from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Restaurant, MenuItem, Cart, CartItem, FoodItem, Order, OrderItem
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

# delete menu
@api_view(['DELETE'])
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)
    menu_item.delete()
    return Response({"message": f"Item {menu_id} deleted successfully!!!"})

# add to cart
@api_view(['POST'])
def add_to_cart(request):
    item_id = request.data.get("item_id")
    qty = int(request.data.get("quantity", 1))

    item = get_object_or_404(FoodItem, id=item_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, item=item,
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


@api_view(['POST'])
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return Response({"error": "Cart is empty"}, status=400)

    total = sum([c.subtotal for c in cart_items])

    order = Order.objects.create(
        user=request.user,
        total_amount=total,
        status="PLACED"
    )

    for c in cart_items:
        OrderItem.objects.create(
            order=order,
            item=c.item,
            quantity=c.quantity,
            price=c.item.price
        )

    cart_items.delete()

    return Response({
        "message": "Order placed successfully",
        "order_id": order.id,
        "total": total
    })

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
