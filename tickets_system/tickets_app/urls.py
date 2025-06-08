from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("<int:event_id>/", views.tickets_view, name="tickets"),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<int:order_id>/', views.order_details, name='order_details'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('cart/', views.cart_view, name='cart'),
    path('finalize/', views.finalize_cart, name='finalize_cart'),
]