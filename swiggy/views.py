from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Restaurant
from .serializers import RestaurantSerializer
# Create your views here.


# list restaurants
@api_view(['GET'])
def list_all_restaurants(request):
    restaurants = Restaurant.objects.all()
    serializer = RestaurantSerializer(restaurants, many = True)
    return Response(serializer.data)