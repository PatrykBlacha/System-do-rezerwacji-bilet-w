from django.contrib.auth.models import User
from django.db import models

class Event(models.Model):
    name = models.CharField(max_length=64)
    event_date = models.DateField()
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'events'
class Ticket(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold')
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    def __str__(self):
        return f"Ticket: {self.id} for {self.event.name}, seat: {self.seat}, price: {self.price}"
    class Meta:
        db_table = 'tickets'

class Client(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    address = models.CharField(max_length=64)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    class Meta:
        db_table = 'clients'

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Order by {self.client} for ticket {self.ticket}"
    class Meta:
        db_table = 'orders'
