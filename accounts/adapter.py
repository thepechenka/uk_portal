from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.urls import reverse
from .views import CustomPasswordResetView, CustomPasswordResetFromKeyView


class CustomAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        """Сохраняет пользователя с дополнительными полями"""
        user = super().save_user(request, user, form, commit=False)
        user.full_name = form.cleaned_data.get('full_name', '')

        if commit:
            user.save()
        return user

    def get_password_reset_view(self):
        """Возвращает кастомный view для сброса пароля"""
        return CustomPasswordResetView.as_view()

    def get_password_reset_from_key_view(self):
        """Возвращает кастомный view для ввода нового пароля"""
        return CustomPasswordResetFromKeyView.as_view()