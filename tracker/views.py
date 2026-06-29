import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction, Category, Account
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import login
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


def home(request):
    return render(request, "tracker/homepage.html")


def loginpage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            # ✅ render instead of redirect — keeps username in form
            return render(request, "tracker/login.html", {
                "username": username
            })

    return render(request, "tracker/login.html")


def register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("eMail", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("conf_password", "")

        # Bundle form data to re-fill fields on error
        form_data = {
            "name": name,
            "eMail": email,
        }

        def error(msg):
            messages.error(request, msg)
            return render(request, "tracker/register.html", form_data)

        # ── USERNAME VALIDATION ──────────────────────────────────────────
        if not name:
            return error("Username is required.")

        if len(name) < 3 or len(name) > 20:
            return error("Username must be between 3 and 20 characters.")

        if not re.match(r'^[a-zA-Z0-9_ .-]+$', name):
            return error("Username can only contain letters, numbers, underscores (_), dots (.), and hyphens (-).")

        if re.match(r'^[_.\-]', name) or re.match(r'[_.\-]$', name):
            return error("Username cannot start or end with a special character.")

        if re.search(r'[_.\-]{2,}', name):
            return error("Username cannot have consecutive special characters.")
        
        if not name.replace(" ", ""):
            return error("Username cannot be only spaces.")

        RESERVED_USERNAMES = ['admin', 'root', 'superuser', 'administrator', 'support', 'help', 'null', 'undefined']
        if name.lower() in RESERVED_USERNAMES:
            return error("This username is reserved. Please choose another.")

        if User.objects.filter(username__iexact=name).exists():
            return error("Username already exists.")

        # ── EMAIL VALIDATION ─────────────────────────────────────────────
        if not email:
            return error("Email is required.")

        email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return error("Enter a valid email address.")

        BLOCKED_EMAIL_DOMAINS = ['tempmail.com', 'throwaway.email', 'mailinator.com', 'guerrillamail.com']
        email_domain = email.split('@')[-1]
        if email_domain in BLOCKED_EMAIL_DOMAINS:
            return error("Disposable email addresses are not allowed.")

        if User.objects.filter(email__iexact=email).exists():
            return error("An account with this email already exists.")

        # ── PASSWORD VALIDATION ──────────────────────────────────────────
        if not password:
            return error("Password is required.")
        
        if ' ' in password:
            return error("Password cannot contain spaces.")

        if len(password) < 8:
            return error("Password must be at least 8 characters long.")

        if len(password) > 128:
            return error("Password must not exceed 128 characters.")

        if not re.search(r'\d', password):
            return error("Password must contain at least one number.")

        COMMON_PASSWORDS = ['password', '12345678', 'password1', 'qwerty123', 'iloveyou']
        if password.lower() in COMMON_PASSWORDS:
            return error("This password is too common. Please choose a stronger one.")

        if name.lower() in password.lower():
            return error("Password should not contain your username.")

        if password != confirm_password:
            return error("Passwords do not match.")

        # ── CREATE USER ──────────────────────────────────────────────────
        user = User.objects.create_user(username=name, email=email, password=password)
        user.save()

        Account.objects.create(user=user, balance=Decimal('0.00'))

        Category.objects.bulk_create([
            Category(name="Salary", type="income", user=user),
            Category(name="Freelance", type="income", user=user),
            Category(name="Food", type="expense", user=user),
            Category(name="Transport", type="expense", user=user),
            Category(name="Bills", type="expense", user=user),
        ])

        login(request, user)
        messages.success(request, "Account created successfully!")
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
        date_str = request.POST.get("date")

        if not amount:
            messages.error(request, "Amount is required.")
            return redirect('dashboard')

        try:
            amount = Decimal(amount)
        except InvalidOperation:
            messages.error(request, "Enter a valid numeric amount.")
            return redirect('dashboard')

        if amount <= 0:
            messages.error(request, "Income amount must be greater than zero.")
            return redirect('dashboard')

        if amount > Decimal('9999999.99'):
            messages.error(request, "Income amount is unrealistically large.")
            return redirect('dashboard')

        if round(amount, 2) != amount:
            messages.error(request, "Amount can have at most 2 decimal places.")
            return redirect('dashboard')

        if not date_str:
            messages.error(request, "Date is required.")
            return redirect('dashboard')

        try:
            income_date = date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Enter a valid date in YYYY-MM-DD format.")
            return redirect('dashboard')

        today = date.today()
        if income_date > today + timedelta(days=1):
            messages.error(request, "Income date cannot be more than 1 day in the future.")
            return redirect('dashboard')

        if income_date < today - timedelta(days=365):
            messages.error(request, "Income date cannot be more than 1 year in the past.")
            return redirect('dashboard')

        if not category_id:
            messages.error(request, "Category is required.")
            return redirect('dashboard')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('dashboard')

        account = Account.objects.filter(user=request.user).first()
        if not account:
            messages.error(request, "No account found. Please create an account first.")
            return redirect('dashboard')

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            transaction_type='income',
            date=income_date
        )
        account.balance += amount
        account.save()
        messages.success(request, f"Income of {amount} added successfully.")

    return redirect('dashboard')


@login_required(login_url='/login/')
def add_expense(request):
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = request.POST.get("amount")
        date_str = request.POST.get("date")

        if not amount:
            messages.error(request, "Amount is required.")
            return redirect('dashboard')

        try:
            amount = Decimal(amount)
        except InvalidOperation:
            messages.error(request, "Enter a valid numeric amount.")
            return redirect('dashboard')

        if amount <= 0:
            messages.error(request, "Expense amount must be greater than zero.")
            return redirect('dashboard')

        if amount > Decimal('9999999.99'):
            messages.error(request, "Expense amount is unrealistically large.")
            return redirect('dashboard')

        if round(amount, 2) != amount:
            messages.error(request, "Amount can have at most 2 decimal places.")
            return redirect('dashboard')

        if not date_str:
            messages.error(request, "Date is required.")
            return redirect('dashboard')

        try:
            expense_date = date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Enter a valid date in YYYY-MM-DD format.")
            return redirect('dashboard')

        today = date.today()
        if expense_date > today + timedelta(days=1):
            messages.error(request, "Expense date cannot be more than 1 day in the future.")
            return redirect('dashboard')

        if expense_date < today - timedelta(days=365):
            messages.error(request, "Expense date cannot be more than 1 year in the past.")
            return redirect('dashboard')

        if not category_id:
            messages.error(request, "Category is required.")
            return redirect('dashboard')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('dashboard')

        account = Account.objects.filter(user=request.user).first()
        if not account:
            messages.error(request, "No account found. Please create an account first.")
            return redirect('dashboard')

        if account.balance < amount:
            messages.error(request, f"Insufficient balance. Your current balance is {account.balance}.")
            return redirect('dashboard')

        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            transaction_type='expense',
            date=expense_date
        )
        messages.success(request, f"Expense of {amount} added successfully.")

    return redirect('dashboard')