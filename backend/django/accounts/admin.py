from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 유저 어드민"""

    list_display = ['id', 'username', 'name', 'gender', 'age', 'is_login', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['gender', 'is_login', 'is_active', 'is_staff']
    search_fields = ['username', 'name']
    ordering = ['-date_joined']
    list_display_links = ['id', 'username']

    fieldsets = (
        ('계정 정보', {'fields': ('username', 'password')}),
        ('개인 정보', {'fields': ('name', 'gender', 'age')}),
        ('상태', {'fields': ('is_login', 'is_active', 'is_staff', 'is_superuser')}),
        ('권한', {'fields': ('groups', 'user_permissions')}),
        ('날짜', {'fields': ('date_joined', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'gender', 'age', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    readonly_fields = ['date_joined', 'updated_at']
