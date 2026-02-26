from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.safestring import mark_safe

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'phone', 'get_apartment_debt', 'get_avatar', 'is_staff', 'is_active',
                    'apartment_confirmed')
    search_fields = ('email', 'full_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone', 'avatar')}),  # добавил avatar
        ('Apartment', {'fields': ('apartment', 'personal_account', 'apartment_confirmed', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

    def get_apartment_debt(self, obj):
        if obj.apartment:
            return obj.apartment.debt
        return '-'

    get_apartment_debt.short_description = 'Долг'

    def get_avatar(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.avatar.url}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />')
        return '-'

    get_avatar.short_description = 'Аватар'