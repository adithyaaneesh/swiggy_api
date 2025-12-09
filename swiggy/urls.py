from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # AUTH
    path("api/register/", views.register_user, name="register"),
    path("api/login/", views.login_user, name="login"),
    path("api/profile/", views.profile, name="profile"),

    # RESTAURANTS / MENUS
    path('api/add_restaurant/', views.add_restaurant, name='add_restaurant'),
    path('api/add_menu/', views.add_menu, name='add_menu'),
    path('api/update_menu/<int:menu_id>/', views.update_menu, name='update_menu'),
    path('api/all_menu/', views.list_menu, name='all_menu'),
    path('api/delete_menu/<int:menu_id>/', views.delete_menu, name='delete_menu'),
    path('api/search_restaurant/', views.search_restaurant, name='search_restaurants'),

    # CART
    path('api/add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('api/remove_from_cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/view_cart/', views.view_cart, name='view_cart'),

    # ORDERS
    path('api/place_order/', views.place_order, name='place_order'),
    # path('api/update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),

    # RATINGS / REVIEWS
    path('api/rate_restaurant/<int:restaurant_id>/', views.rate_restaurant, name='rate_restaurant'),
    path('api/restaurant_reviews/<int:restaurant_id>/', views.restaurant_reviews, name='restaurant_reviews'),

    # ADMIN
    path('api/admin/users/', views.admin_list_users, name='admin_list_users'),
    path('api/admin/restaurants/', views.admin_list_all_restaurants, name='admin_list_all_restaurants'),
    path('api/admin/update_restaurant/<int:restaurant_id>/', views.admin_update_restaurants, name='admin_update_restaurant'),
    path('api/admin/delete_restaurant/<int:restaurant_id>/', views.admin_delete_restaurants, name='admin_delete_restaurant'),
    path('api/admin/orders/', views.admin_list_orders, name='admin_list_orders'),

    # DELIVERY
    path("api/delivery/accept/<int:order_id>/", views.delivery_accept_order, name="delivery_accept_order"),
    path("api/delivery/update-status/<int:order_id>/", views.delivery_update_status, name="delivery_update_status"),

    # PAYPAL
    path('api/paypal/create/<int:order_id>/', views.create_paypal_payment, name="create_paypal_payment"),
    path('api/paypal/execute/<int:order_id>/', views.execute_paypal_payment, name="execute_paypal_payment"),
    path('api/paypal/cancel/<int:order_id>/', views.cancel_paypal_payment, name="cancel_paypal_payment"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)









# from django.urls import path
# from . import views
# from django.conf import settings
# from django.conf.urls.static import static

# urlpatterns = [
#     # AUTH
#     path("api/register/", views.register_user, name="register"),
#     path("api/login/", views.login_user, name="login"),
#     path("api/profile/", views.profile, name="profile"),

#     # RESTAURANTS
#     path('api/add_restaurant/', views.add_restaurant, name='add_restaurant'),
#     path('api/add_menu/', views.add_menu, name='add_menu'),
#     path('api/update_menu/<int:menu_id>/', views.update_menu, name='update_menu'),
#     path('api/all_menu/', views.list_menu, name='all_menu'),
#     path('api/delete_menu/<int:menu_id>/', views.delete_menu, name='delete_menu'),
#     path('api/search_restaurant/', views.search_restaurant, name='search_restaurants'),

#     # CART
#     path('api/add_to_cart/', views.add_to_cart, name='add_to_cart'),
#     path('api/remove_from_cart/', views.remove_from_cart, name='remove_from_cart'),
#     path('api/view_cart/', views.view_cart, name='view_cart'),

#     # ORDER
#     path('api/place_order/', views.place_order, name='place_order'),
#     path('api/update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),

#     # RATINGS / REVIEWS
#     path('api/rate_restaurant/<int:restaurant_id>/', views.rate_restaurant, name='rate_restaurant'),
#     path('api/restaurant_reviews/<int:restaurant_id>/', views.restaurant_reviews, name='restaurant_reviews'),

#     # ADMIN
#     path('api/admin/users/', views.admin_list_users, name='admin_list_users'),
#     path('api/admin/restaurants/', views.admin_list_all_restaurants, name='admin_list_all_restaurants'),
#     path('api/admin/update_restaurant/<int:restaurant_id>/', views.admin_update_restaurants, name='admin_update_restaurant'),
#     path('api/admin/delete_restaurant/<int:restaurant_id>/', views.admin_delete_restaurants, name='admin_delete_restaurant'),
#     path('api/admin/orders/', views.admin_list_orders, name='admin_list_orders'),

#     # DELIVERY PARTNER
#     path("api/delivery/accept/<int:order_id>/", views.delivery_accept_order, name="delivery_accept_order"),
#     path("api/delivery/update-status/<int:order_id>/", views.delivery_update_status, name="delivery_update_status"),

#     # PAYPAL PAYMENT
#     path('api/paypal/create/<int:order_id>/', views.create_paypal_payment, name="create_paypal_payment"),
#     path('api/paypal/execute/<int:order_id>/', views.execute_paypal_payment, name="execute_paypal_payment"),
#     path('api/paypal/cancel/<int:order_id>/', views.cancel_paypal_payment, name="cancel_paypal_payment"),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


