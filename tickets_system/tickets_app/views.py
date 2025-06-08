from datetime import timedelta

from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Ticket, Event, Participant, Order, OrderDetails
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.db import connection

class IndexView(generic.ListView):
    template_name = 'tickets_app/index.html'
    context_object_name = 'latest_events'

    def get_queryset(self):
        now = timezone.now()
        unlock_reserved_tickets()
        return Event.objects.all().filter(event_date__gt=now).order_by('event_date')

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
                order = Order.objects.create(user=request.user, status='pending')

                for ticket_id in selected_ticket_ids:
                    ticket = Ticket.objects.select_for_update().get(id=ticket_id)
                    if ticket.status != 'available':
                        raise Exception(f"Bilet {ticket.seat} jest już niedostępny.")

                    participant = Participant.objects.create(user=request.user)
                    ticket.status = 'reserved'
                    ticket.reserved_until = timezone.now() + timedelta(minutes=10)
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
    except Order.DoesNotExist:
        order = None
        order_details = []
    else:
        order_details = OrderDetails.objects.filter(order=order).select_related('ticket', 'participant')

        if request.method == "POST":
            for detail in order_details:
                participant = detail.participant
                participant.first_name = request.POST.get(f'first_name_{participant.id}', '')
                participant.last_name = request.POST.get(f'last_name_{participant.id}', '')
                participant.pesel = request.POST.get(f'pesel_{participant.id}', '')
                participant.save()
            return redirect('finalize_cart')

    return render(request, 'tickets_app/cart.html', {
        'order': order,
        'order_details': order_details
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
    return redirect('my_tickets')


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
def my_tickets(request):
    user_id = request.user.id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT order_id, "ticket_UUID", event_id, event_name, seat, updated_at
            FROM user_tickets_view
            WHERE user_id = %s
        """, [user_id])
        rows = cursor.fetchall()

    tickets = [
        {
            'order_id': row[0],
            'ticket_id': row[1],
            'event_id': row[2],
            'event_name': row[3],
            'seat_number': row[4],
            'updated_at': row[5],
        }
        for row in rows
    ]

    return render(request, 'tickets_app/my_tickets.html', {'tickets': tickets})


@require_POST
@login_required
def cancel_order(request, order_id):
    user = request.user

    try:
        # Pobierz zamówienie użytkownika
        order = Order.objects.get(id=order_id, user=user)

        if order.status == 'canceled':
            messages.warning(request, "Zamówienie już zostało anulowane.")
            return redirect('my_tickets')

        # Znajdź wszystkie bilety w tym zamówieniu
        order_details = OrderDetails.objects.filter(order=order)

        # Zmień status każdego biletu z powrotem na 'available'
        for detail in order_details:
            ticket = detail.ticket
            ticket.status = 'available'
            ticket.reserved_until = None
            ticket.save()

        # Zmień status zamówienia
        order.status = 'canceled'
        order.save()

        messages.success(request, "Zamówienie zostało anulowane.")
    except Order.DoesNotExist:
        messages.error(request, "Nie znaleziono zamówienia.")
    except Exception as e:
        messages.error(request, f"Wystąpił błąd: {e}")

    return redirect('my_tickets')
