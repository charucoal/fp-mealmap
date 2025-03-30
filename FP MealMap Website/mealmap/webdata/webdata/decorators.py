from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect

# NOTE: admin account is only Django-admin site
# hence, admin is auto-logged out if accessing MealMap pages

# ensures that only logged out users can access pages
def check_login(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user

            if user.username == 'admin':
                logout(request)
                return redirect('home')
            
            # ensures account is valid
            if not hasattr(user, "account_type"):
                logout(request)
                return HttpResponse('Your account is missing credentials. Please contact support.', status=400)

            # redirects to customer homepage
            if user.account_type == 'customer':
                return redirect('customer-home')
            
            # redirects to business homepage
            elif user.account_type == 'business':
                return redirect('business-home')
            
            else:
                logout(request)
                return HttpResponse('Invalid account type. Please contact support.', status=400)

        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# ensures that logged in users who are customers can access pages
def customer_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user

            if user.username == 'admin':
                logout(request)
                return redirect('home')
            
            # ensures account is valid
            if not hasattr(user, "account_type"):
                logout(request)
                return HttpResponse('Your account is missing credentials. Please contact support.', status=400)
            
            # prevents any account not a customer from accessing these pages
            if user.account_type != 'customer':
                return HttpResponseForbidden("You are not authorized to view this page.")
        
        # redirects to login page if user is not authenticated
        else:
            return redirect('login')

        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# ensures that logged in users who are businesses can access pages
def business_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user

            if user.username == 'admin':
                logout(request)
                return redirect('home')
            
            # ensures account is valid
            if not hasattr(user, "account_type"):
                logout(request)
                return HttpResponse('Your account is missing credentials. Please contact support.', status=400)
            
            # prevents any account not a business from accessing these pages
            if user.account_type != 'business':
                return HttpResponseForbidden("You are not authorized to view this page.")
        
        # redirects to login page if user is not authenticated
        else:
            return redirect('login')

        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
