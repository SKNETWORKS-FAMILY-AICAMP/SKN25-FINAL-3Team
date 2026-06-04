from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('name',)}),
    )
    list_display = ('username', 'name', 'email', 'is_staff', 'date_joined')
