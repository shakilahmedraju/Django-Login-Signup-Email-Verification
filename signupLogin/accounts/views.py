from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url='/login')
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            if User.objects.filter(username = username).first():
                messages.success(request, 'Username is taken')
                return redirect('/register')
            
            if User.objects.filter(email = email).first():
                messages.success(request, 'Email is taken')
                return redirect('/register')
            
            user_obj = User.objects.create(username=username, email=email)
            user_obj.set_password(password)
            user_obj.save()

            auth_token=str(uuid.uuid4())

            profile_obj = Profile.objects.create(user=user_obj, auth_token=auth_token)
            profile_obj.save()

            send_mail_afer_registration(email, auth_token)

            return redirect('/token')

        except Exception as e:
            print(e)

    return render(request, 'register.html')

def login_attempt(request):
    if request.method == "POST":
        username = request.POST.get('username')        
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request, 'User not found')
            return redirect('/login')
        
        profile_obj = Profile.objects.filter(user=user_obj).first()
        if not profile_obj.is_verified:
            messages.success(request, 'Your account is not verified yet, check mail')
            return redirect('/login')
        
        user = authenticate(username=username, password=password)
        if user is None:
            messages.success(request, 'wrong password')
            return redirect('/login')
        
        login(request, user)
        return redirect('/')       

    return render(request, 'login.html')


def logout(request):
    return render(request, 'logout.html')

def success(request):
    return render(request, 'success.html')

def token_send(request):
    return render(request, 'token_send.html')


"""
==============================================
Mail Send and Verification
==============================================
"""
def verify(request, auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()

        if profile_obj.is_verified:
            messages.success(request, 'Your account is already verified')
            return redirect('/login')

        if profile_obj:
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, 'Your account has been verified')
            return redirect('/login')
        else:
            return redirect('/error')
        
    except Exception as e:
        print(e)

def error_page(request):
    return render(request, 'error.html')


def send_mail_afer_registration(email, token):
    subject = "Your accounts need to be verrified"
    message = f'Hi Paste the link to verify your account http://127.0.0.1:8000/verify/{token}/'
    email_form = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_form, recipient_list)
    return True

"""
==============================================
forget Password Change Password
==============================================
"""
def forget_password(request):
    if request.method == "POST":
        username = request.POST.get('username')

        try:
            if not User.objects.filter(username = username).first():
                messages.success(request, 'Not user found with this username')
                return redirect('/forget-password')
            
            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())

            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.auth_token = token
            profile_obj.save()

            send_forget_password_mail(user_obj.email, token)
            messages.success(request, 'An Email is sent')
            return redirect('/forget-password')
            
        except Exception as e:
            print(e)
    return render(request, 'forget-password.html')



def send_forget_password_mail(email, token):    
    subject = "Your forget password link"
    message = f'Hi click on the link to reset password http://127.0.0.1:8000/change-password/{token}/'
    email_form = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_form, recipient_list)
    return True



def change_password(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(auth_token=token).first()
        context = {'user_id' : profile_obj.user_id}

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.success(request, 'No user id found')
                return redirect(f'/change-password/{token}/')
            
            if new_password != confirm_password:            
                messages.success(request, 'Both Password should be equal')
                return redirect(f'/change-password/{token}/')
            
            user_obj = User.objects.get(id = user_id)
            user_obj.set_password(new_password)
            user_obj.save()

            messages.success(request, 'Password Update Successfully. Please login')
            return redirect('/login')

        
    except Exception as e:
            print(e)

    return render(request, 'change-password.html', context)