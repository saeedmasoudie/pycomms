from django import forms
from django.contrib.auth.password_validation import MinimumLengthValidator, validate_password
from django_countries.fields import CountryField
from user.models import CustomUser
from django.core.validators import validate_email


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email or Username here'}), required=True,
        label='')
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password here'}), required=True,
        label='')
    remember_me = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), required=False,
                                     label='')


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='', required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="",
                                       required=True)
    terms = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), required=True, label='')
    country = CountryField(blank_label='Select Country').formfield(widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'country', 'first_name', 'last_name']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username here'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email here'})
        }

        labels = {
            'username': '',
            'email': '',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ForgetPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email here'}),
                             required=True, validators=[validate_email])


class PasswordResetForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password here'}), required=True,
        label='', validators=[MinimumLengthValidator])
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password here'}), label="",
        required=True, validators=[MinimumLengthValidator])

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")

        return cleaned_data

class DateInput(forms.DateInput):
    input_type = 'date'

class ProfileSettingsForm1(forms.ModelForm):
    country = CountryField(blank_label='Select Country').formfield(widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'date_of_birth', 'bio', 'country', 'avatar', 'profile_cover']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Bio', 'rows': '5'}),
            'date_of_birth': DateInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'specific-file-input', 'placeholder': 'Avatar'}),
            'profile_cover': forms.FileInput(attrs={'class': 'specific-file-input', 'placeholder': 'Profile Cover'}),
        }
        labels = {
            'first_name': '',
            'last_name': '',
            'bio': '',
            'date_of_birth': '',
            'avatar': '',
            'profile_cover': '',
        }

class ProfileSettingsForm2(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'}), required=True, label='')
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}), required=True, label='', validators=[MinimumLengthValidator])
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}), required=True, label='', validators=[MinimumLengthValidator])

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if new_password and confirm_new_password and new_password != confirm_new_password:
            self.add_error('confirm_new_password', "Passwords do not match")
        validate_password(new_password, self.user)
        return cleaned_data

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect")
        return current_password