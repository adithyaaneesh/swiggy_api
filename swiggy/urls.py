from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/list_all_restaurants', views.list_all_restaurants, name='list_all_restaurants'),
    path('api/add_menu', views.add_menu, name='add_menu'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
