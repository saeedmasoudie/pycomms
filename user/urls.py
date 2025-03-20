from django.contrib.auth.decorators import login_required
from django.urls import path
from utils.checkers import anonymous_required
from . import views

urlpatterns = [
    path('login/', anonymous_required(views.LoginView.as_view()), name='login'),
    path('logout/', login_required(views.logout_view), name='logout'),
    path('signup/', anonymous_required(views.SignUpView.as_view()), name='signup'),
    path('forget-password/', anonymous_required(views.ForgetPasswordView.as_view()), name='forget-password'),
    path('reset-password/<uuid:key>', anonymous_required(views.ResetPasswordView.as_view()), name='reset-password'),
    path('profile/<username>', login_required(views.ProfileView.as_view()), name='profile'),
    path('profile-settings/', login_required(views.ProfileSettingsView.as_view()), name='profile-settings'),
]
