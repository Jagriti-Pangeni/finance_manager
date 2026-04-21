from django.contrib import admin
from .models import UserProfile,Category,Account,Transaction

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Account)
admin.site.register(Transaction)
