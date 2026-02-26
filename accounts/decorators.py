from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def verified_email_required(view_func):
    """Декоратор для проверки подтвержденного email"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для доступа необходимо войти в систему.')
            return redirect('account_login')

        try:
            from allauth.account.models import EmailAddress
            if hasattr(request.user, 'emailaddress_set'):
                email_address = request.user.emailaddress_set.filter(primary=True, verified=True).first()
                if not email_address:
                    messages.warning(
                        request,
                        'Для доступа к этой странице необходимо подтвердить ваш email. '
                        'Проверьте вашу почту и перейдите по ссылке в письме.'
                    )
                    return redirect('account_email_verification_sent')
        except ImportError:
            if not hasattr(request.user, 'email_confirmed') or not request.user.email_confirmed:
                messages.warning(
                    request,
                    'Для доступа к этой странице необходимо подтвердить ваш email.'
                )
                return redirect('account_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def apartment_required(view_func):
    """Декоратор для проверки, что пользователь привязан к квартире"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для доступа необходимо войти в систему.')
            return redirect('account_login')

        try:
            from allauth.account.models import EmailAddress
            if hasattr(request.user, 'emailaddress_set'):
                email_address = request.user.emailaddress_set.filter(primary=True, verified=True).first()
                if not email_address:
                    messages.warning(request, 'Сначала подтвердите ваш email.')
                    return redirect('account_email_verification_sent')
        except ImportError:
            if not hasattr(request.user, 'email_confirmed') or not request.user.email_confirmed:
                messages.warning(request, 'Сначала подтвердите ваш email.')
                return redirect('account_login')

        if not hasattr(request.user, 'has_apartment') or not request.user.has_apartment():
            messages.error(
                request,
                'Для выполнения этого действия необходимо привязать квартиру. '
                'Пожалуйста, перейдите в личный кабинет → "Мои данные" → "Привязать квартиру".'
            )
            return redirect('profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def verified_email_and_apartment_required(view_func):
    """Декоратор для проверки подтвержденного email и привязанной квартиры"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для доступа необходимо войти в систему.')
            return redirect('account_login')

        email_verified = False
        try:
            from allauth.account.models import EmailAddress
            if hasattr(request.user, 'emailaddress_set'):
                email_address = request.user.emailaddress_set.filter(primary=True, verified=True).first()
                email_verified = email_address is not None
        except ImportError:
            email_verified = hasattr(request.user, 'email_confirmed') and request.user.email_confirmed

        if not email_verified:
            messages.warning(request, 'Сначала подтвердите ваш email.')
            return redirect('account_email_verification_sent')

        if not hasattr(request.user, 'has_apartment') or not request.user.has_apartment():
            messages.error(
                request,
                ' Для этого действия необходимо привязать квартиру. '
                'Пожалуйста, перейдите в личный кабинет и привяжите вашу квартиру.'
            )
            return redirect('profile')

        return view_func(request, *args, **kwargs)

    return _wrapped_view