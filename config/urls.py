# config/urls.py
from django.contrib import admin
from django.urls import path
from tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name="home"),
    path("login/", views.loginpage, name="login"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("add-income/", views.add_income, name="add_income"),
    path("add-expense/", views.add_expense, name="add_expense"),
]