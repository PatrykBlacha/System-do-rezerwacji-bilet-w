from datetime import timedelta

from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .models import Ticket, Event, Participant, Order, OrderDetails
from django.contrib.auth import login
from .forms import CustomUserCreationForm

class IndexView(TemplateView):
    template_name = 'tickets_app/index.html'


class EventsView(generic.ListView):
    template_name = 'tickets_app/events.html'
    context_object_name = 'latest_events'

    def get_queryset(self):
        now = timezone.now()
        unlock_reserved_tickets()
        search_query = self.request.GET.get('search', '')
        events = Event.objects.filter(event_date__gt=now).order_by('event_date')
        if search_query:
            events = events.filter(name__icontains=search_query)

        return events

def unlock_reserved_tickets():
    now = timezone.now()

    expired_tickets = Ticket.objects.filter(
        status='reserved',
        reserved_until__lt=now
    )

    for ticket in expired_tickets:
        ticket.status = 'available'
        ticket.reserved_until = None
        ticket.save()

        details = OrderDetails.objects.filter(ticket=ticket)
        for detail in details:
            order = detail.order
            order_tickets = OrderDetails.objects.filter(order=order).select_related('ticket')

            if all(d.ticket.status == 'available' for d in order_tickets):
                order.status = 'canceled'
                order.save()

@login_required
@transaction.atomic
def tickets_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    tickets = Ticket.objects.select_for_update().filter(event=event, status='available').order_by('seat')

    if request.method == "POST":
        selected_ticket_ids = request.POST.getlist('ticket_ids')

        if not selected_ticket_ids:
            messages.error(request, "Nie wybrano żadnych biletów.")
            return redirect('tickets', event_id=event_id)

        try:
            with transaction.atomic():

                try:
                    order = Order.objects.get(
                        user=request.user,
                        status='pending'
                    )
                except Order.DoesNotExist:
                    order = Order.objects.create(
                        user=request.user,
                        status='pending'
                    )

                for ticket_id in selected_ticket_ids:
                    ticket = Ticket.objects.select_for_update().get(id=ticket_id)
                    if ticket.status != 'available':
                        raise Exception(f"Bilet {ticket.seat} jest już niedostępny.")

                    participant = Participant.objects.create(user=request.user, first_name='', last_name='', pesel='')
                    ticket.status = 'reserved'
                    ticket.save()

                    OrderDetails.objects.create(
                        order=order,
                        participant=participant,
                        ticket=ticket
                    )

            messages.success(request, "Bilety zostały dodane do koszyka.")
            return redirect('cart')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('tickets', event_id=event_id)

    return render(request, 'tickets_app/tickets.html', {'event': event, "tickets": tickets})


@login_required
def cart_view(request):
    try:
        order = Order.objects.get(user=request.user, status='pending')
        order_details = OrderDetails.objects.filter(order=order).select_related('ticket', 'participant')
        total = order.total_price()
        for detail in order_details:
            detail.ticket.reserved_until = timezone.now() + timedelta(minutes=10)
            detail.ticket.save()

        if request.method == "POST":
            for detail in order_details:
                participant = detail.participant
                participant.first_name = request.POST.get(f'first_name_{participant.id}', '')
                participant.last_name = request.POST.get(f'last_name_{participant.id}', '')
                participant.pesel = request.POST.get(f'pesel_{participant.id}', '')

            return redirect('finalize_cart')

    except Order.DoesNotExist:
        order = None
        order_details = []
        total = 0

    return render(request, 'tickets_app/cart.html', {
        'order': order,
        'order_details': order_details,
        'total': total
    })


@login_required
@transaction.atomic
def finalize_cart(request):
    try:
        order = Order.objects.select_for_update().get(user=request.user, status='pending')
    except Order.DoesNotExist:
        messages.error(request, "Brak zamówienia do finalizacji.")
        return redirect('home')

    order_details = OrderDetails.objects.filter(order=order).select_related('ticket', 'participant')

    for detail in order_details:
        ticket = detail.ticket
        ticket.status = 'sold'
        ticket.save()

    order.status = 'completed'
    order.updated_at = timezone.now()
    order.save()

    messages.success(request, "Zakup zakończony sukcesem!")
    return redirect('order_details', order_id=order.id)


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-updated_at')

    return render(request, 'tickets_app/my_orders.html', {'orders': orders})

@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    details = OrderDetails.objects.filter(order=order).select_related('ticket', 'participant')

    return render(request, 'tickets_app/order_details.html', {
        'order': order,
        'details': details
    })

@require_POST
@login_required
def cancel_order(request, order_id):
    user = request.user

    try:
        order = Order.objects.get(id=order_id, user=user)

        if order.status == 'canceled':
            messages.warning(request, "Zamówienie już zostało anulowane.")
            return redirect('my_orders')

        order_details = OrderDetails.objects.filter(order=order)

        for detail in order_details:
            ticket = detail.ticket
            ticket.status = 'available'
            ticket.reserved_until = None
            ticket.save()

        order.status = 'canceled'
        order.save()

        messages.success(request, "Zamówienie zostało anulowane.")
    except Order.DoesNotExist:
        messages.error(request, "Nie znaleziono zamówienia.")
    except Exception as e:
        messages.error(request, f"Wystąpił błąd: {e}")

    return redirect('order_details', order_id=order_id)
