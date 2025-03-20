from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.gis.geoip2 import GeoIP2
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

def staff_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = f"{reverse('login')}?next={request.get_full_path()}"
            return HttpResponseRedirect(login_url)
        elif not request.user.is_staff:
            return redirect('homepage')
        return view_func(request, *args, **kwargs)
    return login_required(user_passes_test(lambda u: u.is_staff)(_wrapped_view_func))

def anonymous_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('homepage')  # Change 'home' to the URL name you want to redirect authenticated users to
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_country_code(ip):
    if ip == '127.0.0.1':
        return 'ir'
    g = GeoIP2()
    code = g.country_code(ip)
    return code.lower()
