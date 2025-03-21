import json

from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import View, TemplateView
from django_ratelimit.decorators import ratelimit

from home.models import Channel, ChannelMember, BannedMember
from home.templates.forms import NewChannelForm
from user.models import CustomUser
from utils.checkers import get_country_code, get_client_ip


# Create your views here.
class HomePageView(View):
    template_name = 'home/home.html'
    def get(self, request):
        form = NewChannelForm()
        members = CustomUser.objects.count()
        channels = Channel.objects.count()
        online = ChannelMember.objects.filter(active=True).count()
        site_data = {'members': members, 'channels': channels, 'online': online}
        context = {
            'channels': Channel.objects.all().prefetch_related('messages', 'members').annotate(
                extra_count=Count('members', filter=Q(members__active=True)) - 3),
            'site_data': site_data,
            'form': form
        }
        return render(request, self.template_name, context)

    @method_decorator(ratelimit(key='ip', rate='5/h', block=False))
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise PermissionDenied
        form = NewChannelForm(request.POST)
        members = CustomUser.objects.count()
        channels = Channel.objects.count()
        online = ChannelMember.objects.filter(active=True).count()
        site_data = {'members': members, 'channels': channels, 'online': online}
        if form.is_valid():
            new_channel = form.save(commit=False)
            new_channel.owner = request.user
            new_channel.save()
            return redirect('homepage')
        context = {
            'channels': Channel.objects.all().prefetch_related('messages', 'members').annotate(
                extra_count=Count('members', filter=Q(members__active=True)) - 3),
            'site_data': site_data,
            'form': form
        }
        return render(request, self.template_name, context)

class TermsPageView(TemplateView):
    template_name = 'home/TermsofService.html'

class PrivacyPageView(TemplateView):
    template_name = 'home/PrivacyPolicy.html'

class InDevelopmentPageView(TemplateView):
    template_name = 'home/in-dev.html'

def join_channel(request, channel_id):
    user = request.user
    channel = get_object_or_404(Channel, id=channel_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        password = data.get('password', 0)  # Ensure you get a cleaned string

        # Check if user is banned
        if BannedMember.objects.filter(channel=channel, user=user).exists():
            return JsonResponse({"error": "You are banned from this channel."}, status=403)

        # Handle password-protected channels
        if channel.password:
            if not password:
                return JsonResponse({"error": "Password is required."}, status=403)
            if not channel.check_password(password):
                return JsonResponse({"error": "Incorrect password."}, status=403)

        # Add user to channel if not already a member
        member, created = ChannelMember.objects.get_or_create(
            channel=channel,
            user=user,
            defaults={"active": True}
        )
        if not created:
            member.active = True
            member.save()

        ip = get_client_ip(request)
        # Get list of active members
        active_members = ChannelMember.objects.filter(channel=channel, active=True).select_related("user")
        user_list = [{
            "name": m.user.full_name(),
            "username": m.user.username,
            "flag": get_country_code(ip),
            "avatar": m.user.avatar.url if m.user.avatar else '/static/images/avatar.jpg',
            "userId": m.user.id,
        } for m in active_members]

        return JsonResponse({"message": "Joined successfully.", "users": user_list})

    return JsonResponse({"error": "Invalid request."}, status=400)

def leave_channel(request, channel_id):
    user = request.user
    channel = get_object_or_404(Channel, id=channel_id)
    # Mark user as inactive in the channel
    ChannelMember.objects.filter(channel=channel, user=user).update(active=False)
    return JsonResponse({"message": "Left successfully."})

def check_channel_password(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    return JsonResponse({"password_protected": channel.is_password_protected()})
