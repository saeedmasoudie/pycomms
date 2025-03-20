import json

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import now
from django.views import View
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from user.forms import LoginForm, SignupForm, ForgetPasswordForm, PasswordResetForm, ProfileSettingsForm1, \
    ProfileSettingsForm2
from user.models import CustomUser


class LoginView(View):
    template_name = 'user/login.html'
    def get(self, request):
        next_url = request.GET.get('next', reverse('homepage'))
        context = {
            'form': LoginForm(),
            'next': next_url,
        }
        return render(request, self.template_name, context)

    @method_decorator(ratelimit(key='ip', rate='20/h', block=False))
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise PermissionDenied
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            user = CustomUser.objects.filter(Q(username=username) | Q(email=username)).first()
            next_url = self.request.POST.get('next')
            if user and user.check_password(password):
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                else:
                    return redirect('homepage')
            else:
                messages.error(request, "Username or Password is wrong!")
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


class SignUpView(View):
    template_name = 'user/sign-up.html'
    def get(self, request):
        context = {
            'form': SignupForm()
        }
        return render(request, self.template_name, context)

    @method_decorator(ratelimit(key='ip', rate='10/h', block=False))
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise PermissionDenied
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')

        context = {
            'form': form
        }
        return render(request, self.template_name, context)


class ForgetPasswordView(View):
    template_name = 'user/forget-password.html'
    def get(self, request):
        context = {
            'form': ForgetPasswordForm()
        }
        return render(request, self.template_name, context)

    @method_decorator(ratelimit(key='ip', rate='100/h', block=False))
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            raise PermissionDenied
        form = ForgetPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                # todo: send email
                messages.success(request, "check your email inbox / spam and click on the link we just sent.")
            else:
                messages.error(request, "this email is not registered in website!")
                return redirect('forget-password')
        context = {
            'form': form
        }
        return render(request, self.template_name, context)

class ResetPasswordView(View):
    template_name = 'user/reset-password.html'
    def get(self, request, key):
        get_object_or_404(CustomUser, reset_key=key, date_key__gte=now())
        context = {
            'form': PasswordResetForm()
        }
        return render(request, self.template_name, context)
    def post(self, request, key):
        user = get_object_or_404(CustomUser, reset_key=key, date_key__gte=now())
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            messages.success(request, "Your password was successfully updated!")
            return redirect('login')
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


def logout_view(request):
    if not request.user.is_authenticated:
        raise Http404()
    logout(request)
    request.session.flush()
    return redirect('login')

class ProfileView(View):
    template_name = 'user/profile.html'
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        context = {
            'user': user,
        }
        return render(request, self.template_name, context)

class ProfileSettingsView(View):
    template_name = 'user/settings.html'
    def get(self, request):
        user = CustomUser.objects.filter(pk=request.user.id).first()
        context = {
            'form1': ProfileSettingsForm1(instance=user),
            'form2': ProfileSettingsForm2(),
            'user': user,
        }
        return render(request, self.template_name, context)
    def post(self, request):
        form_type = request.POST.get('form_type')
        user = get_object_or_404(CustomUser, pk=request.user.id)
        if form_type == 'form1':
            form = ProfileSettingsForm1(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                return redirect('profile-settings')
            context = {
                'form1': form,
                'form2': ProfileSettingsForm2(),
            }
            return render(request, self.template_name, context)
        elif form_type == 'form2':
            form = ProfileSettingsForm2(request.POST, user=user)
            if form.is_valid():
                current_password = form.cleaned_data['current_password']
                new_password = form.cleaned_data['new_password']
                if user.check_password(current_password):
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Your password was successfully updated!")
                else:
                    messages.error(request, "Current password is incorrect!")
                return redirect('profile-settings')
            context = {
                'form1': ProfileSettingsForm1(instance=user),
                'form2': form,
            }
            return render(request, self.template_name, context)
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = json.loads(request.body)
            action = data.get('action')
            success = False
            reason = "Something went wrong."
            if action == 'remove_avatar':
                if user.avatar:
                    user.avatar.delete()
                    user.save()
                    success = True
                else:
                    reason = "You don't have an avatar."
                    success = False
            elif action == 'remove_profile_cover':
                if user.profile_cover:
                    user.profile_cover.delete()
                    success = True
                else:
                    reason = "You don't have an cover."
                    success = False
            return JsonResponse({'success': success, 'reason': reason })
        return HttpResponseForbidden()
