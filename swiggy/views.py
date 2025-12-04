from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Restaurant, MenuItem
from .serializers import RestaurantSerializer, MenuItemSerializers
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
