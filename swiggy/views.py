from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view,  permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.db.models import Avg
from .models import RatingReview, Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, User
from .serializers import MenuItemSerializer, RatingReviewSerializer, RestaurantSerializer, UserLoginSerializer, UserRegistrationSerializer, UserSerializer
import paypalrestsdk
from django.conf import settings

from functools import wraps
from rest_framework.response import Response

def role_required(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=401)

            # SUPERUSER SHOULD ALWAYS HAVE ACCESS
            if request.user.is_superuser:
                return func(request, *args, **kwargs)

            # Normal role checking
            if request.user.role not in allowed_roles:
                return Response({"error": "Permission Denied"}, status=403)

            return func(request, *args, **kwargs)
        return wrapper
    return decorator



# register
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Assign default role if missing
        if not user.role:
            user.role = "CUSTOMER"
            user.save()

        # Create token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "User registered successfully",
            "user": UserSerializer(user).data,
            "token": token.key
        })
    return Response(serializer.errors, status=400)


# login
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data["user"]

        # If SUPERUSER → always assign ADMIN role
        if user.is_superuser:
            role = "ADMIN"
        else:
            role = user.role

        # Issue Authentication Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role,
            },
            "token": token.key,
        })
    
    return Response(serializer.errors, status=400)


# list restaurants
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_restaurants(request):
    restaurants = Restaurant.objects.all()
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data)

# search a restaurant by its name
@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@role_required(["RESTAURANT_OWNER"])
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
@role_required(["RESTAURANT_OWNER"])
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
@permission_classes([IsAuthenticated])
def list_menu(request):
    menu_items = MenuItem.objects.all()
    serializer = MenuItemSerializer(menu_items, many=True)
    return Response(serializer.data)

# delete menu
@api_view(['DELETE'])
@role_required(["RESTAURANT_OWNER"])
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    if request.user != menu_item.restaurant.owner:
        return Response({"error": "Unauthorized"}, status=403)

    menu_item.delete()
    return Response({"message": "Menu deleted"})


# add to cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    item_id = request.data.get("item_id")
    cart_item = get_object_or_404(CartItem, user=request.user, item_id=item_id)
    cart_item.delete()

    return Response({"message": "Item removed from cart"})

# view cart
@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@role_required(["ADMIN"])
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
@role_required(["ADMIN"])
def admin_list_all_restaurants(request):
    restaurants = Restaurant.objects.all()
    serializers = RestaurantSerializer(restaurants, many=True)
    return Response(serializers.data)

# admin update restaurants
@api_view(['PUT'])
@role_required(["ADMIN"])
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
@role_required(["ADMIN"])
def admin_delete_restaurants(request,restaurant_id):
    restaurant = Restaurant.objects.filter(id=restaurant_id).first()
    if not restaurant:
        return Response({"error":"Restaurant not found"})
    restaurant.delete()
    return Response({"message":"Restaurant deleted successfully"})

# admin list all orders
@api_view(['GET'])
@role_required(["ADMIN"])
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

#Accept an order for delivery
@api_view(['POST'])
@role_required(["DELIVERY_PARTNER"])
def delivery_accept_order(request, order_id):
    user = request.user

    # Only delivery partners can accept delivery
    if user.role != "DELIVERY_PARTNER":
        return Response({"error": "Only delivery partners can accept orders"}, status=403)

    order = get_object_or_404(Order, id=order_id)

    if order.status != "PREPARING":
        return Response({
            "error": "You can accept only orders in PREPARING state",
            "current_status": order.status
        }, status=400)

    # Update order status
    order.status = "OUT_FOR_DELIVERY"
    order.save()

    return Response({ "message": "Order taken for delivery", "order_id": order.id, "new_status": "OUT_FOR_DELIVERY"})

# Update delivery status
@api_view(['POST'])
@role_required(["DELIVERY_PARTNER"])
def delivery_update_status(request, order_id):
    user = request.user

    # Only delivery partner can update status
    if user.role != "DELIVERY_PARTNER":
        return Response({"error": "Only delivery partners can update delivery status"}, status=403)

    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get("status")

    if order.status != "OUT_FOR_DELIVERY":
        return Response({
            "error": "Order must be OUT_FOR_DELIVERY before marking delivered",
            "current_status": order.status
        }, status=400)

    if new_status != "DELIVERED":
        return Response({
            "error": "Invalid status. Allowed status: DELIVERED"
        }, status=400)

    order.status = "DELIVERED"
    order.save()

    return Response({"message": "Order delivered successfully","order_id": order.id, "new_status": "DELIVERED"})

#  Add or update rating
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_restaurant(request, restaurant_id):
    user = request.user
    rating = request.data.get("rating")
    comment = request.data.get("comment", "")

    if not rating:
        return Response({"error": "Rating is required"}, status=400)

    rating = int(rating)
    if rating < 1 or rating > 5:
        return Response({"error": "Rating must be between 1 and 5"}, status=400)

    # Create or update review
    review, created = RatingReview.objects.get_or_create(
        user=user,
        restaurant_id=restaurant_id,
        defaults={'rating': rating, 'comment': comment}
    )

    if not created:
        review.rating = rating
        review.comment = comment
        review.save()
        msg = "Review updated"
    else:
        msg = "Review added"

    # --- Recalculate average rating for the restaurant ---
    avg_rating = RatingReview.objects.filter(restaurant_id=restaurant_id).aggregate(avg=Avg('rating'))['avg']
    
    restaurant = Restaurant.objects.get(id=restaurant_id)
    restaurant.rating = round(avg_rating, 1)  # Round to 1 decimal
    restaurant.save()

    return Response({ "message": msg, "rating": review.rating, "comment": review.comment, "average_rating": restaurant.rating })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def restaurant_reviews(request, restaurant_id):
    reviews = RatingReview.objects.filter(restaurant_id=restaurant_id).order_by('-created_at')
    serializer = RatingReviewSerializer(reviews, many=True)
    return Response(serializer.data)

# paypal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Create Payment API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_paypal_payment(request, order_id):
    user = request.user
    order = Order.objects.filter(id=order_id, user=user).first()
    if not order:
        return Response({"error": "Order not found"}, status=404)

    if order.status != "PENDING":
        return Response({"error": f"Cannot pay for order with status {order.status}"}, status=400)

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": f"http://localhost:8000/api/paypal/execute/{order.id}/",
            "cancel_url": f"http://localhost:8000/api/paypal/cancel/{order.id}/"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"Order {order.id}",
                    "sku": f"order_{order.id}",
                    "price": str(order.total_amount),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(order.total_amount),
                "currency": "USD"
            },
            "description": f"Payment for Order {order.id}"
        }]
    })

    if payment.create():
        # Extract approval URL for redirect
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return Response({"approval_url": approval_url})
    else:
        return Response({"error": payment.error}, status=400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execute_paypal_payment(request, order_id):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    order = Order.objects.filter(id=order_id).first()
    if not order:
        return Response({"error": "Order not found"}, status=404)

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        order.status = "ACCEPTED"  # or "PAID" depending on your workflow
        order.save()
        return Response({"message": "Payment successful", "order_id": order.id})
    else:
        return Response({"error": payment.error}, status=400)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancel_paypal_payment(request, order_id):
    return Response({"message": f"Payment for order {order_id} was cancelled."}) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    
    # Base user data
    profile_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "phone": user.phone,
    }
    if user.is_superuser:
        profile_data["role"] = "ADMIN"

    # Restaurant Owner → attach restaurant details
    if user.role == "RESTAURANT_OWNER":
        restaurant = Restaurant.objects.filter(owner=user).first()
        if restaurant:
            profile_data["restaurant"] = {
                "id": restaurant.id,
                "restaurant_name": restaurant.restaurant_name,
                "address": restaurant.restaurant_address,
                "phone": restaurant.rest_phonenum,
                "email": restaurant.rest_email,
                "rating": restaurant.rating,
                "category": restaurant.category,
            }
        else:
            profile_data["restaurant"] = None

    # Delivery Partner → attach delivery profile
    if user.role == "DELIVERY_PARTNER":
        # You can extend later with delivery stats
        profile_data["delivery_partner"] = {
            "assigned_orders": Order.objects.filter(status="OUT_FOR_DELIVERY").count(),
            "delivered_orders": Order.objects.filter(status="DELIVERED").count(),
        }

    # Customer → cart details
    if user.role == "CUSTOMER":
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.all()

        profile_data["cart"] = {
            "items_count": cart_items.count(),
            "total": float(sum(item.subtotal for item in cart_items))
        }

    return Response(profile_data)
