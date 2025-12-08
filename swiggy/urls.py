from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # path('api/restaurants', views.list_all_restaurants, name='all_restaurants'),
    path('api/search_restaurant', views.search_restaurant, name='search_restaurants'),

    # MENU
    path('api/add_menu', views.add_menu, name='add_menu'),
    path('api/update_menu/<int:menu_id>', views.update_menu, name='update_menu'),
    path('api/all_menu', views.list_menu, name='all_menu'),
    path('api/delete_menu/<int:menu_id>', views.delete_menu, name='delete_menu'),

    # CART
    path('api/add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('api/remove_from_cart', views.remove_from_cart, name='remove_from_cart'),
    path('api/view_cart', views.view_cart, name='view_cart'),

    # ORDER
    path('api/place_order', views.place_order, name='place_order'),
    path('api/update_order_status/<int:order_id>', views.update_order_status, name='update_order_status'),

    # ADMIN
    path('admin/users', views.admin_list_users, name='all_users'),
    path('admin/restaurants', views.admin_list_all_restaurants, name='all_restaurants'),
    path('admin/update_restaurant/<int:restaurant_id>', views.admin_update_restaurants, name='update_restaurant'),
    path('admin/delete_restaurant/<int:restaurant_id>', views.admin_delete_restaurants, name='delete_restaurant'),
    path('admin/orders', views.admin_list_orders, name='all_orders'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
