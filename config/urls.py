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
    path("logout/", views.logout_user, name="logout"),
   path("add-category/", views.add_category, name="add_category"),
   path("profile/", views.profile, name="profile"),
    path("reports/", views.reports, name="reports"),
]