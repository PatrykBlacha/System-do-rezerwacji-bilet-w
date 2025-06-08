from datetime import timedelta

from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

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

@login_required
@transaction.atomic
def reserve_ticket_view(request, ticket_id):
    try:
        client = Client.objects.get(user=request.user)
        print(f"[DEBUG] Client ID: {client.id}, Ticket ID: {ticket_id}")
    except Client.DoesNotExist:
        print("[ERROR] Client does not exist")
        messages.error(request, "Brak danych klienta.")
        return redirect('home')

    try:
        with connection.cursor() as cursor:
            cursor.execute("CALL reserve_ticket_for_client(%s, %s);", [client.id, ticket_id])
            cursor.execute("SELECT status FROM tickets WHERE id = %s", [ticket_id])
            status = cursor.fetchone()
            print(f"[DEBUG] Ticket status after reservation: {status}")
            messages.success(request, "Zarezerwowano bilet.")
    except Exception as e:
        print(f"[ERROR] Exception during reservation: {e}")
        messages.error(request, f"Błąd rezerwacji: {e}")
        return redirect('home')

    return redirect('confirm_purchase', ticket_id=ticket_id)



from django.db import connection


@login_required
@transaction.atomic
def order_confirmation(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, "Brak danych klienta.")
        return redirect('home')

    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT purchase_ticket(%s, %s);", [client.id, ticket.id])
        except Exception as e:
            messages.error(request, f"Błąd przy zakupie: {e}")
            return redirect('home')

        order = Order.objects.filter(client=client, ticket=ticket).order_by('-created_at').first()
        return redirect('order_success', order_id=order.id)

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
                email=form.cleaned_data['email']
            )

            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
@transaction.atomic
def group_purchase_view(request, event_id):
    print("[DEBUG] Group purchase view accessed")
    event = get_object_or_404(Event, id=event_id)
    tickets = Ticket.objects.filter(event=event, status='available').order_by('seat')

    if request.method == 'POST':
        ticket_ids = request.POST.getlist('ticket_ids')

        first_names = []
        last_names = []
        emails = []
        addresses = []

        for ticket_id in ticket_ids:
            first_names.append(request.POST.get(f'first_name_{ticket_id}'))
            last_names.append(request.POST.get(f'last_name_{ticket_id}'))
            emails.append(request.POST.get(f'email_{ticket_id}'))
            addresses.append(request.POST.get(f'address_{ticket_id}'))

        print("[DEBUG] ticket_ids:", ticket_ids)
        print("[DEBUG] first_names:", first_names)

        if not all([ticket_ids, first_names, last_names, emails, addresses]):
            messages.error(request, "Wszystkie dane klientów muszą być wypełnione.")
            return redirect('group_purchase', event_id=event_id)

        if not (len(ticket_ids) == len(first_names) == len(last_names) == len(emails) == len(addresses)):
            messages.error(request, "Dla każdego biletu muszą być podane kompletne dane klienta.")
            return redirect('group_purchase', event_id=event_id)

        client_ids = []
        for i in range(len(ticket_ids)):
            client = Client.objects.create(
                first_name=first_names[i],
                last_name=last_names[i],
                email=emails[i],
                address=addresses[i]
            )
            client_ids.append(client.id)

        try:
            with transaction.atomic():
                for client_id, ticket_id in zip(client_ids, ticket_ids):
                    ticket = Ticket.objects.select_for_update().get(id=ticket_id)

                    if ticket.status != 'available':
                        raise Exception(f"Bilet {ticket.id} nie jest dostępny.")

                    ticket.status = 'sold'
                    ticket.save()

                    Order.objects.create(
                        client_id=client_id,
                        ticket=ticket,
                        status='completed',
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )

            messages.success(request, "Zakup grupowy zakończony sukcesem.")
            return redirect('home')

        except Exception as e:
            messages.error(request, f"Błąd: {e}")
            return redirect('group_purchase', event_id=event_id)

    return render(request, 'tickets_app/group_purchase.html', {'event': event, 'tickets': tickets})



@login_required
def my_tickets(request):
    user_id = request.user.id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT order_id, ticket_id, event_id, seat, updated_at
            FROM user_tickets_view
            WHERE user_id = %s
        """, [user_id])
        rows = cursor.fetchall()

    tickets = [
        {
            'order_id': row[0],
            'ticket_id': row[1],
            'event_id': row[2],
            'seat_number': row[3],
            'updated_at': row[4],
        }
        for row in rows
    ]

    return render(request, 'tickets_app/my_tickets.html', {'tickets': tickets})


@require_POST
@login_required
def cancel_order(request, order_id):
    user_id = request.user.id

    with connection.cursor() as cursor:
        cursor.execute("SELECT client_id FROM orders WHERE id = %s", [order_id])
        row = cursor.fetchone()
        if not row or row[0] != user_id:
            messages.error(request, "Nie masz dostępu do tego biletu.")
            return redirect('my_tickets')

        try:
            cursor.execute("SELECT cancel_order(%s)", [order_id])
            messages.success(request, "Bilet został anulowany.")
        except Exception as e:
            messages.error(request, f"Błąd: {str(e)}")

    return redirect('my_tickets')
