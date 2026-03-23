from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "tracker/homepage.html")
    
def loginpage(request):
    return render(request,"tracker/login.html")

def register(request):
    return render(request,"tracker/register.html")