from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.db.models import Avg
from functools import wraps
from .models import User, Restaurant, MenuItem, Cart, CartItem, Order, OrderItem, RatingReview
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    RestaurantSerializer, MenuItemSerializer, CartItemSerializer, RatingReviewSerializer
)
import paypalrestsdk
from django.conf import settings

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# --- Role-based decorator ---
def role_required(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=401)
            if request.user.is_superuser or request.user.role in allowed_roles:
                return func(request, *args, **kwargs)
            return Response({"error": "Permission Denied"}, status=403)
        return wrapper
    return decorator

# --- AUTH ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"message": "User registered successfully","user": UserSerializer(user).data,"token": token.key}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"message": "Login successful","user": UserSerializer(user).data,"token": token.key})
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    data = UserSerializer(user).data
    if user.role == "RESTAURANT_OWNER":
        restaurant = Restaurant.objects.filter(owner=user).first()
        if restaurant:
            data["restaurant"] = RestaurantSerializer(restaurant).data
    if user.role == "CUSTOMER":
        cart, _ = Cart.objects.get_or_create(user=user)
        data["cart"] = {"items_count": cart.items.count(), "total": float(sum(i.subtotal for i in cart.items.all()))}
    return Response(data)

# --- RESTAURANTS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_restaurant(request):
    if request.user.role not in ["RESTAURANT_OWNER","ADMIN"]:
        return Response({"error":"Not allowed"}, status=403)
    data = request.data.copy()
    data["owner"] = request.user.id
    serializer = RestaurantSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message":"Restaurant added","restaurant": serializer.data}, status=201)
    return Response(serializer.errors)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_restaurant(request):
    name = request.GET.get("restaurant_name","")
    restaurants = Restaurant.objects.filter(restaurant_name__icontains=name)
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data if restaurants.exists() else {"message":"No restaurant found"})

# --- MENU ---
@api_view(['POST'])
@role_required(["RESTAURANT_OWNER"])
def add_menu(request):
    restaurant = get_object_or_404(Restaurant, owner=request.user)
    data = request.data.copy()
    data["restaurant"] = restaurant.id
    serializer = MenuItemSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['PUT','PATCH'])
@role_required(["RESTAURANT_OWNER"])
def update_menu(request, menu_id):
    menu = get_object_or_404(MenuItem, id=menu_id)
    if menu.restaurant.owner != request.user:
        return Response({"error":"Cannot update this menu"}, status=403)
    serializer = MenuItemSerializer(menu, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['DELETE'])
@role_required(["RESTAURANT_OWNER"])
def delete_menu(request, menu_id):
    menu = get_object_or_404(MenuItem, id=menu_id)
    if menu.restaurant.owner != request.user:
        return Response({"error":"Unauthorized"}, status=403)
    menu.delete()
    return Response({"message":"Menu deleted"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_menu(request):
    items = MenuItem.objects.all()
    serializer = MenuItemSerializer(items, many=True)
    return Response(serializer.data)

# --- CART ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    menu_id = request.data.get("menu_item")
    qty = int(request.data.get("quantity",1))
    cart,_ = Cart.objects.get_or_create(user=request.user)
    menu_item = get_object_or_404(MenuItem, id=menu_id)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item, defaults={"quantity":qty})
    if not created:
        cart_item.quantity += qty
        cart_item.save()
    return Response({"message":"Item added to cart"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    item_id = request.data.get("item_id")
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, id=item_id)
    cart_item.delete()
    return Response({"message":"Item removed from cart"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart,_ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = sum([i.subtotal for i in items])
    data = CartItemSerializer(items, many=True).data
    return Response({"items": data, "total": total})

# --- ORDERS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()
    if not items.exists():
        return Response({"error":"Cart is empty"}, status=400)
    total = sum([i.subtotal for i in items])
    order = Order.objects.create(user=request.user, total_amount=total)
    for item in items:
        OrderItem.objects.create(order=order, menu_item=item.menu_item, quantity=item.quantity, price=item.menu_item.price)
    items.delete()
    return Response({"message":"Order placed","order_id": order.id})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get("status")
    WORKFLOW = {"PENDING":"ACCEPTED","ACCEPTED":"PREPARING","PREPARING":"OUT_FOR_DELIVERY","OUT_FOR_DELIVERY":"DELIVERED"}
    if order.status not in WORKFLOW or new_status != WORKFLOW[order.status]:
        return Response({"error":"Invalid status update","allowed_next_status": WORKFLOW.get(order.status)}, status=400)
    order.status = new_status
    order.save()
    return Response({"message":"Order status updated","order_id":order.id,"new_status":new_status})

# --- RATINGS / REVIEWS ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_restaurant(request, restaurant_id):
    rating = int(request.data.get("rating",0))
    comment = request.data.get("comment","")
    if rating<1 or rating>5:
        return Response({"error":"Rating must be between 1 and 5"}, status=400)
    review, created = RatingReview.objects.get_or_create(user=request.user, restaurant_id=restaurant_id, defaults={"rating":rating,"comment":comment})
    if not created:
        review.rating = rating
        review.comment = comment
        review.save()
    avg_rating = RatingReview.objects.filter(restaurant_id=restaurant_id).aggregate(avg=Avg('rating'))['avg']
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.rating = round(avg_rating,1)
    restaurant.save()
    return Response({"message":"Review added" if created else "Review updated","rating": review.rating,"comment":review.comment,"average_rating":restaurant.rating})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def restaurant_reviews(request, restaurant_id):
    reviews = RatingReview.objects.filter(restaurant_id=restaurant_id).order_by('-created_at')
    serializer = RatingReviewSerializer(reviews, many=True)
    return Response(serializer.data)

# --- ADMIN ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(["ADMIN"])
def admin_list_users(request):
    serializer = UserSerializer(User.objects.all(), many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(["ADMIN"])
def admin_list_all_restaurants(request):
    serializer = RestaurantSerializer(Restaurant.objects.all(), many=True)
    return Response(serializer.data)

@api_view(['PUT','PATCH'])
@permission_classes([IsAuthenticated])
@role_required(["ADMIN"])
def admin_update_restaurants(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    serializer = RestaurantSerializer(restaurant, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@role_required(["ADMIN"])
def admin_delete_restaurants(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    return Response({"message":"Restaurant deleted"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@role_required(["ADMIN"])
def admin_list_orders(request):
    data=[]
    for order in Order.objects.all():
        items = [{"menu_item": i.menu_item.name,"quantity":i.quantity,"price":float(i.price)} for i in order.items.all()]
        data.append({"order_id": order.id,"user": order.user.username,"status":order.status,"total_amount":float(order.total_amount),"items":items,"created_at": order.created_at})
    return Response(data)

# --- DELIVERY ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(["DELIVERY_PARTNER"])
def delivery_accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status != "ACCEPTED":
        order.status = "PREPARING"
        order.save()
        return Response({"message":f"Order {order.id} accepted for delivery","status":order.status})
    return Response({"error":"Order cannot be accepted"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@role_required(["DELIVERY_PARTNER"])
def delivery_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get("status")
    allowed_status = ["PREPARING","OUT_FOR_DELIVERY","DELIVERED"]
    if new_status not in allowed_status:
        return Response({"error":"Invalid status"}, status=400)
    order.status = new_status
    order.save()
    return Response({"message":f"Order {order.id} status updated","new_status":order.status})

# --- PAYPAL ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_paypal_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status!="DELIVERED":
        return Response({"error": f"Cannot pay for order with status {order.status}"}, status=400)
    payment = paypalrestsdk.Payment({
        "intent":"sale",
        "payer":{"payment_method":"paypal"},
        "redirect_urls":{
            "return_url": f"http://localhost:8000/api/paypal/execute/{order.id}/",
            "cancel_url": f"http://localhost:8000/api/paypal/cancel/{order.id}/"
        },
        "transactions":[{"item_list":{"items":[{"name":f"Order {order.id}","sku":f"order_{order.id}","price":str(order.total_amount),"currency":"USD","quantity":1}]},"amount":{"total":str(order.total_amount),"currency":"USD"},"description":f"Payment for Order {order.id}"}]
    })
    if payment.create():
        for link in payment.links:
            if link.rel=="approval_url":
                return Response({"approval_url": str(link.href)})
    else:
        return Response({"error":payment.error}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def execute_paypal_payment(request, order_id):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        order.status = "ACCEPTED"
        order.save()
        return Response({"message":"Payment successful","order_id":order.id})
    else:
        return Response({"error":payment.error}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancel_paypal_payment(request, order_id):
    return Response({"message": f"Payment for order {order_id} was cancelled."})
