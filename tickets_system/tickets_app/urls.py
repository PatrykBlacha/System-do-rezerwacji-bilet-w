from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("<int:event_id>/", views.tickets_view, name="tickets"),
    path("reserve/<int:ticket_id>/", views.reserve_ticket_view, name="reserve_ticket"),
    path("confirm/<int:ticket_id>/", views.order_confirmation, name="confirm_purchase"),
    path("success/<int:order_id>/", views.order_success, name="order_success"),
]