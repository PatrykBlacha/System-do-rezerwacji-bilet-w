from django.contrib import admin

from .models import Event, Ticket, Client

admin.site.register(Event)

admin.site.register(Ticket)

admin.site.register(Client)