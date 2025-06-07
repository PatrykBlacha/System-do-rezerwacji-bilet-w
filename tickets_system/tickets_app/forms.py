from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=64, required=True)
    last_name = forms.CharField(max_length=64, required=True)
    email = forms.EmailField(required=True)
    address = forms.CharField(max_length=128, required=False)  # dodaj adres (opcjonalnie)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "address", "password1", "password2")
