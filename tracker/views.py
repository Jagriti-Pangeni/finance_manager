from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

# Create your views here.
def home(request):
    return render(request, "tracker/homepage.html")
    
def loginpage(request):
     if request.method=='POST':
        username=request.POST.get("Uname")
        password=request.POST.get("pass")
        validate_user=authenticate(username=username, password=password)
        if validate_user is None:
            messages.error(request, 'wrong credentials')
            return redirect('loginpage')
        else:
            login(request, validate_user)
            return redirect('homepage')
    return render(request,"tracker/login.html")

def register(request):
    if request.method =="POST":
        username=request.POST.get("name")
        email=request.POST.get("eMail")
        password=request.POST.get("password")
        confirm_password=request.POST.get("conf_password")

        if len(password)<8:
            messages.error(request,'password must be 8 characters or longer')
            return redirect('register')
        
        all_username=User.objects.filter(username=username)
        if all_username:
            messages.error(request,'Error! username already exists')
            return redirect('register')
        
        new_user=User.objects.create_user(username=username,email=email,password=password)
        new_user.save()
    return render(request,"tracker/register.html")