import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction, Category,Account
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import login
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


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
        name = request.POST.get("name", "").strip()
        email = request.POST.get("eMail", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("conf_password", "")

        # ── USERNAME VALIDATION ──────────────────────────────────────────
        if not name:
            messages.error(request, "Username is required.")
            return redirect('register')

        if len(name) < 3 or len(name) > 20:
            messages.error(request, "Username must be between 3 and 20 characters.")
            return redirect('register')

        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            messages.error(request, "Username can only contain letters, numbers, underscores (_), dots (.), and hyphens (-).")
            return redirect('register')

        if re.match(r'^[_.\-]', name) or re.match(r'[_.\-]$', name):
            messages.error(request, "Username cannot start or end with a special character.")
            return redirect('register')

        if re.search(r'[_.\-]{2,}', name):
            messages.error(request, "Username cannot have consecutive special characters.")
            return redirect('register')

        RESERVED_USERNAMES = ['admin', 'root', 'superuser', 'administrator', 'support', 'help', 'null', 'undefined']
        if name.lower() in RESERVED_USERNAMES:
            messages.error(request, "This username is reserved. Please choose another.")
            return redirect('register')

        if User.objects.filter(username__iexact=name).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        # ── EMAIL VALIDATION ─────────────────────────────────────────────
        if not email:
            messages.error(request, "Email is required.")
            return redirect('register')

        email_regex = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            messages.error(request, "Enter a valid email address.")
            return redirect('register')

        BLOCKED_EMAIL_DOMAINS = ['tempmail.com', 'throwaway.email', 'mailinator.com', 'guerrillamail.com']
        email_domain = email.split('@')[-1]
        if email_domain in BLOCKED_EMAIL_DOMAINS:
            messages.error(request, "Disposable email addresses are not allowed.")
            return redirect('register')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register')

        # ── PASSWORD VALIDATION ──────────────────────────────────────────
        if not password:
            messages.error(request, "Password is required.")
            return redirect('register')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('register')

        if len(password) > 128:
            messages.error(request, "Password must not exceed 128 characters.")
            return redirect('register')

        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('register')

        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect('register')

        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one number.")
            return redirect('register')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('register')

        COMMON_PASSWORDS = ['password', '12345678', 'password1', 'qwerty123', 'iloveyou']
        if password.lower() in COMMON_PASSWORDS:
            messages.error(request, "This password is too common. Please choose a stronger one.")
            return redirect('register')

        if name.lower() in password.lower():
            messages.error(request, "Password should not contain your username.")
            return redirect('register')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # ── CREATE USER ──────────────────────────────────────────────────
        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )
        user.save()
        messages.success(request, "Account created successfully! Please log in.")

        # Create default categories (IMPORTANT FIX)
        Category.objects.bulk_create([
            Category(name="Salary", type="income", user=user),
            Category(name="Freelance", type="income", user=user),
            Category(name="Food", type="expense", user=user),
            Category(name="Transport", type="expense", user=user),
            Category(name="Bills", type="expense", user=user),
        ])

        # Login user
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
        date_str = request.POST.get("date")

        # ── AMOUNT VALIDATION ────────────────────────────────────────────
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
            messages.error(request, "Income amount is unrealistically large. Please enter a valid amount.")
            return redirect('dashboard')

        if round(amount, 2) != amount:
            messages.error(request, "Amount can have at most 2 decimal places.")
            return redirect('dashboard')

        # ── DATE VALIDATION ──────────────────────────────────────────────
        if not date_str:
            messages.error(request, "Date is required.")
            return redirect('dashboard')

        try:
            income_date = date.fromisoformat(date_str)  # expects YYYY-MM-DD
        except ValueError:
            messages.error(request, "Enter a valid date in YYYY-MM-DD format.")
            return redirect('dashboard')

        today = date.today()
        max_past_days = 365  # allow up to 1 year back
        max_future_days = 1  # allow only tomorrow at most

        if income_date > today + timedelta(days=max_future_days):
            messages.error(request, "Income date cannot be more than 1 day in the future.")
            return redirect('dashboard')

        if income_date < today - timedelta(days=max_past_days):
            messages.error(request, "Income date cannot be more than 1 year in the past.")
            return redirect('dashboard')

        # ── CATEGORY VALIDATION ──────────────────────────────────────────
        if not category_id:
            messages.error(request, "Category is required.")
            return redirect('dashboard')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('dashboard')

        # ── ACCOUNT VALIDATION ───────────────────────────────────────────
        account = Account.objects.filter(user=request.user).first()
        if not account:
            messages.error(request, "No account found. Please create an account first.")
            return redirect('dashboard')

        # ── CREATE TRANSACTION ───────────────────────────────────────────
        Transaction.objects.create(
            user=request.user,
            account=account,
            category=category,
            amount=amount,
            transaction_type='income',
            date=income_date
        )
        messages.success(request, f"Income of {amount} added successfully.")

    return redirect('dashboard')


@login_required(login_url='/login/')
def add_expense(request):
    if request.method == "POST":
        category_id = request.POST.get("category")
        amount = request.POST.get("amount")
        date_str = request.POST.get("date")

        # ── AMOUNT VALIDATION ────────────────────────────────────────────
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
            messages.error(request, "Expense amount is unrealistically large. Please enter a valid amount.")
            return redirect('dashboard')

        if round(amount, 2) != amount:
            messages.error(request, "Amount can have at most 2 decimal places.")
            return redirect('dashboard')

        # ── DATE VALIDATION ──────────────────────────────────────────────
        if not date_str:
            messages.error(request, "Date is required.")
            return redirect('dashboard')

        try:
            expense_date = date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Enter a valid date in YYYY-MM-DD format.")
            return redirect('dashboard')

        today = date.today()
        max_past_days = 365  # allow up to 1 year back
        max_future_days = 1  # allow only tomorrow at most

        if expense_date > today + timedelta(days=max_future_days):
            messages.error(request, "Expense date cannot be more than 1 day in the future.")
            return redirect('dashboard')

        if expense_date < today - timedelta(days=max_past_days):
            messages.error(request, "Expense date cannot be more than 1 year in the past.")
            return redirect('dashboard')

        # ── CATEGORY VALIDATION ──────────────────────────────────────────
        if not category_id:
            messages.error(request, "Category is required.")
            return redirect('dashboard')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('dashboard')

        # ── ACCOUNT VALIDATION ───────────────────────────────────────────
        account = Account.objects.filter(user=request.user).first()
        if not account:
            messages.error(request, "No account found. Please create an account first.")
            return redirect('dashboard')

        # ── BALANCE CHECK ─────────────────────────────────────────────────
        if account.balance < amount:
            messages.error(request, f"Insufficient balance. Your current balance is {account.balance}.")
            return redirect('dashboard')

        # ── CREATE TRANSACTION ───────────────────────────────────────────
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
