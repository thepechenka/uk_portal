from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from .models import CustomUser
from core.models import Request, Apartment
import secrets
from .decorators import verified_email_required
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from allauth.account.views import PasswordResetView, PasswordResetFromKeyView
from django.urls import reverse_lazy
import logging
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

logger = logging.getLogger(__name__)


def send_verification_email(request, user):
    """Отправляет письмо с подтверждением email"""
    confirm_url = request.build_absolute_uri(
        f'/accounts/verify/{user.verification_code}/'
    )

    context = {
        'user': user,
        'confirm_url': confirm_url,
        'site_name': 'УК "Новый город"',
    }

    html_message = render_to_string('account/email/verification_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Подтверждение регистрации на портале УК "Новый город"',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_request_notification(request_obj):
    """Отправляет уведомление о новой заявке на email пользователя и админам"""
    user = request_obj.user
    site_url = 'http://127.0.0.1:8000'  # замените на ваш домен в продакшене

    # 1. Отправка пользователю (существующий шаблон)
    user_html = render_to_string('account/email/new_request_notification.html', {
        'request': request_obj,
        'user': user,
        'site_url': site_url,
    })
    user_plain = strip_tags(user_html)

    send_mail(
        subject=f'Новая заявка #{request_obj.id} создана',
        message=user_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=user_html,
        fail_silently=False,
    )

    # 2. Отправка админам (НОВЫЙ шаблон)
    if hasattr(settings, 'ADMINS') and settings.ADMINS:
        admin_html = render_to_string('account/email/admin_request_notification.html', {
            'request': request_obj,
            'user': user,
            'site_url': site_url,
        })
        admin_plain = strip_tags(admin_html)

        admin_emails = [admin[1] for admin in settings.ADMINS]
        send_mail(
            subject=f'❗ НОВАЯ ЗАЯВКА #{request_obj.id} от {user.full_name}',
            message=admin_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=admin_html,
            fail_silently=False,
        )

    logger.info(f"Уведомление о заявке #{request_obj.id} отправлено на {user.email}")


def validate_registration_data(email, full_name, password1, password2):
    """Проверяет данные регистрации"""
    if not all([email, full_name, password1, password2]):
        return 'Все поля обязательны для заполнения!'

    if password1 != password2:
        return 'Пароли не совпадают!'

    if len(password1) < 8:
        return 'Пароль должен быть не менее 8 символов!'

    if CustomUser.objects.filter(email=email).exists():
        return 'Пользователь с таким email уже существует!'

    return None


def get_user_stats(user):
    """Возвращает статистику заявок пользователя"""
    return {
        'total_requests': Request.objects.filter(user=user).count(),
        'new_requests': Request.objects.filter(user=user, status='new').count(),
        'active_requests': Request.objects.filter(user=user, status='in_progress').count(),
        'completed_requests': Request.objects.filter(user=user, status='done').count(),
    }


def get_recent_requests(user):
    """Возвращает последние 5 заявок пользователя"""
    if user.has_apartment():
        return Request.objects.filter(user=user).order_by('-created_at')[:5]
    return []


def bind_apartment_to_user(user, personal_account, apartment_number, owner_fio):
    """Привязывает квартиру к пользователю"""
    try:
        apartment = Apartment.objects.get(
            account_number=personal_account,
            number=apartment_number,
            owner_fio__iexact=owner_fio
        )

        if apartment.users.exclude(id=user.id).exists():
            return False, 'Эта квартира уже привязана к другому пользователю'

        user.apartment = apartment
        user.personal_account = personal_account
        user.apartment_confirmed = True
        user.is_verified = True
        user.save()
        return True, 'Квартира успешно привязана'

    except Apartment.DoesNotExist:
        return False, 'Квартира не найдена. Проверьте лицевой счет, номер квартиры и ФИО'
    except Apartment.MultipleObjectsReturned:
        return False, 'Найдено несколько квартир. Обратитесь в управляющую компанию'


@sensitive_post_parameters()
@csrf_protect
def register_view(request):
    """Регистрация нового пользователя с подтверждением email"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        error = validate_registration_data(email, full_name, password1, password2)
        if error:
            messages.error(request, error)
            return render(request, 'account/register.html')

        try:
            user = CustomUser.objects.create_user(
                email=email,
                full_name=full_name,
                password=password1
            )

            user.verification_code = secrets.token_urlsafe(32)
            user.is_active = False
            user.email_confirmed = False
            user.save()

            send_verification_email(request, user)

            messages.success(request, 'Регистрация успешна! Проверьте вашу почту для подтверждения.')
            return redirect('register_success')

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, f'Ошибка при регистрации: {str(e)}')

    return render(request, 'account/register.html')


def register_success_view(request):
    """Страница успешной регистрации"""
    return render(request, 'account/register_success.html')


def verify_email_view(request, verification_code):
    """Подтверждение email"""
    try:
        user = CustomUser.objects.get(
            verification_code=verification_code,
            is_active=False
        )

        user.email_confirmed = True
        user.is_active = True
        user.verification_code = None
        user.save()

        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True
        )

        messages.success(request, 'Email успешно подтвержден! Теперь вы можете войти.')

    except CustomUser.DoesNotExist:
        messages.error(request, 'Неверный код подтверждения.')

    return redirect('account_login')


def resend_verification_email_view(request):
    """Повторная отправка письма"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        try:
            user = CustomUser.objects.get(email=email)

            if user.email_confirmed:
                messages.info(request, 'Ваш email уже подтвержден.')
            else:
                user.verification_code = secrets.token_urlsafe(32)
                user.save()
                send_verification_email(request, user)
                messages.info(request, 'Новое письмо с подтверждением отправлено.')

        except CustomUser.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден.')

        return redirect('account_login')

    return render(request, 'account/resend_verification.html')


@verified_email_required
def profile_view(request):
    """Личный кабинет пользователя"""
    user = request.user

    if request.method == 'POST':
        if 'bind_apartment' in request.POST:
            personal_account = request.POST.get('personal_account', '').strip()
            apartment_number = request.POST.get('apartment_number', '').strip()
            owner_fio = request.POST.get('owner_fio', '').strip()

            if not all([personal_account, apartment_number, owner_fio]):
                messages.error(request, 'Заполните все поля для привязки квартиры')
            else:
                success, message = bind_apartment_to_user(
                    user, personal_account, apartment_number, owner_fio
                )
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)

        elif 'update_profile' in request.POST:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()

            if not full_name:
                messages.error(request, 'Укажите ФИО')
            else:
                user.full_name = full_name
                user.phone = phone if phone else None

                if 'avatar' in request.FILES:
                    user.avatar = request.FILES['avatar']

                user.save()
                messages.success(request, 'Профиль обновлен')

    context = {
        'user': user,
        'stats': get_user_stats(user),
        'requests': get_recent_requests(user),
    }

    return render(request, 'account/profile.html', context)


@login_required
def my_requests_view(request):
    """Страница моих заявок с фильтрацией"""
    requests = Request.objects.filter(user=request.user).order_by('-created_at')

    status = request.GET.get('status', '')
    request_type = request.GET.get('request_type', '')
    priority = request.GET.get('priority', '')
    date_filter = request.GET.get('date', '')

    if status:
        requests = requests.filter(status=status)
    if request_type:
        requests = requests.filter(request_type=request_type)
    if priority:
        requests = requests.filter(priority=int(priority))
    if date_filter:
        requests = requests.filter(created_at__date=date_filter)

    paginator = Paginator(requests, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'requests': page_obj,
    }

    return render(request, 'account/my_requests.html', context)


# Функция для вызова из view создания заявки
def send_request_email_notification(request_obj):
    """Обертка для отправки уведомления о заявке"""
    try:
        send_request_notification(request_obj)
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о заявке #{request_obj.id}: {str(e)}")


class CustomPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset.html'
    success_url = reverse_lazy('account_reset_password_done')

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"Password reset view called: {request.path}")
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetFromKeyView(PasswordResetFromKeyView):
    template_name = 'account/password_reset_from_key.html'
    success_url = reverse_lazy('account_reset_password_from_key_done')

    def dispatch(self, request, *args, **kwargs):
        logger.info(f"Password reset from key view called: {request.path}")
        return super().dispatch(request, *args, **kwargs)