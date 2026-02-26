from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets


class CustomUserManager(BaseUserManager):

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)

        verification_code = secrets.token_urlsafe(20)

        user = self.model(
            email=email,
            full_name=full_name,
            verification_code=verification_code,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_confirmed', True)
        extra_fields.setdefault('apartment_confirmed', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, full_name, password, **extra_fields)



class CustomUser(AbstractUser):

    username = None

    email = models.EmailField(
        _('Email'),
        unique=True,
        help_text=_('Будет использоваться для входа в систему')
    )

    full_name = models.CharField(
        _('ФИО'),
        max_length=150,
        help_text=_('Введите ФИО полностью как в паспорте')
    )

    phone = models.CharField(
        _('Телефон'),
        max_length=20,
        blank=True,
        null=True
    )

    email_confirmed = models.BooleanField(
        _('Email подтвержден'),
        default=False
    )

    verification_code = models.CharField(
        _('Код подтверждения'),
        max_length=100,
        blank=True,
        null=True
    )

    apartment = models.ForeignKey(
        'core.Apartment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Привязанная квартира'),
        related_name='users'
    )

    apartment_confirmed = models.BooleanField(
        _('Квартира подтверждена'),
        default=False
    )

    personal_account = models.CharField(
        _('Лицевой счет'),
        max_length=50,
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(
        _('Подтверждённый жилец'),
        default=False
    )

    created_at = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='Загрузите фото профиля'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def has_apartment(self):
        return self.apartment is not None and self.apartment_confirmed

    def generate_new_verification_code(self):
        self.verification_code = secrets.token_urlsafe(20)
        self.save()
        return self.verification_code

