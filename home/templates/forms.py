from django import forms

from home.models import Channel


class NewChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'password']

        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password Here'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name Here'}),
        }

        labels = {
            'password': '',
            'name': '',
        }