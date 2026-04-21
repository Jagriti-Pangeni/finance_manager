from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction, Category,Account
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import login



# Create your views here.
def home(request):
    return render(request, "tracker/homepage.html")



def loginpage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)  # Check credentials
        if user is not None:
            login(request, user)  # Log the user in
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password")  # Show error if login fails

    return render(request, "tracker/login.html")  # Render login form for GET requests
def register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("eMail")
        password = request.POST.get("password")
        confirm_password = request.POST.get("conf_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=name).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        # ✅ Create user
        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )

        # ✅ Create default account
        Account.objects.create(
            user=user,
            name="Main Account",
            account_type="cash",
            balance=0
        )

        # ✅ Create default categories (IMPORTANT FIX)
        Category.objects.bulk_create([
            Category(name="Salary", type="income", user=user),
            Category(name="Freelance", type="income", user=user),
            Category(name="Food", type="expense", user=user),
            Category(name="Transport", type="expense", user=user),
            Category(name="Bills", type="expense", user=user),
        ])

        # ✅ Login user
        login(request, user)

        return redirect('dashboard')

    return render(request, "tracker/register.html")

@login_required(login_url='/login/')
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    balance = total_income - total_expense

    income_categories = Category.objects.filter(user=request.user, type='income')
    expense_categories = Category.objects.filter(user=request.user, type='expense')

    return render(request, "tracker/dashboard.html", {
        "transactions": transactions,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "income_categories": income_categories,
        "expense_categories": expense_categories
    })

@login_required(login_url='/login/')
def add_income(request):
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = request.POST.get("amount")
        date = request.POST.get("date")

        category = Category.objects.get(id=category_id)
        account = Account.objects.filter(user=request.user).first()

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            transaction_type='income',
            date=date
        )

    return redirect('dashboard')


@login_required(login_url='/login/')
def add_expense(request):
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = request.POST.get("amount")
        date = request.POST.get("date")

        category = Category.objects.get(id=category_id)
        account = Account.objects.filter(user=request.user).first()

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            transaction_type='expense',
            date=date
        )

    return redirect('dashboard')

