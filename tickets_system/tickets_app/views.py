from datetime import timedelta

from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Ticket, Event, Client, Order
from django.contrib.auth import login
from .forms import CustomUserCreationForm

class IndexView(generic.ListView):
    template_name = 'tickets_app/index.html'
    context_object_name = 'latest_events'

    def get_queryset(self):
        now = timezone.now()
        return Event.objects.all().filter(event_date__gt=now).order_by('event_date')

def tickets_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    tickets = Ticket.objects.filter(event=event, status='available').order_by('seat')
    return render(request, 'tickets_app/tickets.html', {'event': event, "tickets": tickets})

@transaction.atomic
def reserve_ticket_view(request, ticket_id):
    try:
        ticket = Ticket.objects.select_for_update().get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return HttpResponse("Ticket not found.", status=404)

    now = timezone.now()

    if ticket.status == 'available' or (ticket.status == 'reserved' and ticket.reserved_until < now):
        ticket.status = 'reserved'
        ticket.reserved_until = now + timedelta(minutes=10)
        ticket.save()

        return redirect('confirm_purchase', ticket_id=ticket.id)
    else:
        return HttpResponse("Ticket is not available.", status=400)


@login_required(login_url='/accounts/login/')
def order_confirmation(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Sprawdź, czy bilet jest nadal zarezerwowany i dostępny
    if not (ticket.status == 'reserved' and ticket.reserved_until > timezone.now()):
        messages.error(request, "Ten bilet nie jest już dostępny.")
        return redirect('home')

    if request.method == 'POST':
        ticket.status = 'sold'
        ticket.save()

        client = get_object_or_404(Client, user=request.user)

        order = Order.objects.create(
            client=client,
            ticket=ticket,
            status='completed'
        )

        messages.success(request, "Twoje zamówienie zostało potwierdzone!")
        return redirect('order_success', order_id=order.id)

    # Jeśli metoda GET — pokaż podsumowanie zamówienia z przyciskiem
    return render(request, 'tickets_app/order_confirmation.html', {'ticket': ticket})

def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    ticket = order.ticket
    return render(request, 'tickets_app/order_success.html', {'ticket': ticket, 'order': order})

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Ustaw dodatkowe pola User
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # Tworzymy Client powiązany z tym User
            Client.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data.get('address', '')  # jeśli adres jest podany
            )

            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
