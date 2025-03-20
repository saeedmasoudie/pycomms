from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path('', login_required(views.HomePageView.as_view()), name='homepage'),
    path('terms-of-service/', views.TermsPageView.as_view(), name='terms'),
    path('privacy-policy/', views.PrivacyPageView.as_view(), name='privacy'),
    path("in-dev/", views.InDevelopmentPageView.as_view(), name="in_dev"),
    path("join-channel/<int:channel_id>/", views.join_channel, name="join_channel"),
    path("leave-channel/<int:channel_id>/", views.leave_channel, name="leave_channel"),
    path("check-channel/<int:channel_id>/", views.check_channel_password, name="check_channel_password"),
]