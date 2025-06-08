from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("<int:event_id>/", views.tickets_view, name="tickets"),
    path("reserve/<int:ticket_id>/", views.reserve_ticket_view, name="reserve_ticket"),
    path("confirm/<int:ticket_id>/", views.order_confirmation, name="confirm_purchase"),
    path("success/<int:order_id>/", views.order_success, name="order_success"),
    path('events/<int:event_id>/group-purchase/', views.group_purchase_view, name='group_purchase'),
    path('events/reserve/<int:ticket_id>/', views.reserve_ticket_view, name='reserve_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
]