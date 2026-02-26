from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class House(models.Model):
    """Модель дома"""
    # Основная информация
    address = models.CharField(_('Адрес'), max_length=255)
    built_year = models.IntegerField(_('Год постройки'), blank=True, null=True)

    # Характеристики дома
    house_type = models.CharField(_('Тип дома'), max_length=100, blank=True, null=True)  # Панельный, Кирпичный и т.д.
    ceiling_type = models.CharField(_('Тип перекрытий'), max_length=100, blank=True, null=True)  # Железобетонные и т.д.
    ceiling_height = models.FloatField(_('Высота потолков'), blank=True, null=True, help_text='в метрах')
    floor_count = models.IntegerField(_('Этажность'), default=1)
    entrance_count = models.IntegerField(_('Парадных (подъездов)'), default=1)
    apartments_count = models.IntegerField(_('Квартир'), default=0)
    elevator_count = models.IntegerField(_('Лифтов'), default=0, help_text='Количество лифтов')

    # Коммуникации и состояние
    has_gas = models.BooleanField(_('Газ'), default=False)
    heating_type = models.CharField(_('Отопление'), max_length=100, blank=True, null=True)  # Центральное и т.д.
    has_garbage_chute = models.BooleanField(_('Мусоропровод'), default=False)
    is_emergency = models.BooleanField(_('Аварийность'), default=False)
    is_demolition = models.BooleanField(_('Под снос'), default=False)

    # Координаты для карты
    latitude = models.FloatField(_('Широта'), blank=True, null=True, help_text='Например: 53.7683')
    longitude = models.FloatField(_('Долгота'), blank=True, null=True, help_text='Например: 87.1597')

    # Служебные поля
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Дом')
        verbose_name_plural = _('Дома')
        ordering = ['address']

    def __str__(self):
        return self.address

    @property
    def coords(self):
        """Возвращает координаты в формате для карты"""
        if self.latitude and self.longitude:
            return [self.latitude, self.longitude]
        return None

class Apartment(models.Model):

    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        verbose_name=_('Дом'),
        related_name='apartments'
    )
    number = models.CharField(_('Номер квартиры'), max_length=10)
    area = models.DecimalField(_('Площадь'), max_digits=6, decimal_places=2, blank=True, null=True)
    rooms = models.IntegerField(_('Количество комнат'), blank=True, null=True)
    floor = models.IntegerField(_('Этаж'), blank=True, null=True)
    entrance = models.IntegerField(_('Подъезд'), blank=True, null=True)
    account_number = models.CharField(_('Лицевой счет'), max_length=50, unique=True)
    owner_fio = models.CharField(_('ФИО собственника'), max_length=150)
    owner_phone = models.CharField(_('Телефон собственника'), max_length=20, blank=True, null=True)
    is_rented = models.BooleanField(_('Сдается в аренду'), default=False)

    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Квартира')
        verbose_name_plural = _('Квартиры')
        ordering = ['house', 'number']
        unique_together = [['house', 'number']]

    def __str__(self):
        return f"кв. {self.number}, {self.house.address}"

    debt = models.DecimalField(
        'Задолженность',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Текущая задолженность по квартплате'
    )


class Request(models.Model):

    class RequestType(models.TextChoices):
        REPAIR = 'repair', _('Ремонт')
        EMERGENCY = 'emergency', _('Аварийная')
        CONSULTATION = 'consultation', _('Консультация')
        PAYMENT = 'payment', _('Оплата')
        OTHER = 'other', _('Другое')

    class Status(models.TextChoices):
        NEW = 'new', _('Новая')
        IN_PROGRESS = 'in_progress', _('В работе')
        DONE = 'done', _('Завершена')
        CANCELLED = 'cancelled', _('Отменена')

    class Priority(models.IntegerChoices):
        LOW = 1, _('Низкий')
        MEDIUM = 2, _('Средний')
        HIGH = 3, _('Высокий')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name='requests'
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        verbose_name=_('Квартира'),
        related_name='requests'
    )
    request_type = models.CharField(
        _('Тип заявки'),
        max_length=20,
        choices=RequestType.choices,
        default=RequestType.REPAIR
    )
    title = models.CharField(_('Заголовок'), max_length=200)
    description = models.TextField(_('Описание'))
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    priority = models.IntegerField(
        _('Приоритет'),
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    admin_comment = models.TextField(_('Комментарий УК'), blank=True, null=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    completed_at = models.DateTimeField(_('Дата завершения'), blank=True, null=True)

    class Meta:
        verbose_name = _('Заявка')
        verbose_name_plural = _('Заявки')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField('Содержание')
    rating = models.IntegerField('Оценка', choices=[
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ])
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    is_approved = models.BooleanField('Одобрено', default=False)  # ← ДОБАВЬ ЭТО!

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отзыв от {self.user}'


class News(models.Model):
    """Модель новости"""
    title = models.CharField(_('Заголовок'), max_length=200)
    content = models.TextField(_('Содержание'))
    short_description = models.TextField(_('Краткое описание'), max_length=500)
    image = models.ImageField(_('Изображение'), upload_to='news/', blank=True, null=True)
    is_published = models.BooleanField(_('Опубликовано'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Новость')
        verbose_name_plural = _('Новости')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class HouseReport(models.Model):
    """Модель для отчетов по дому"""
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        verbose_name='Дом',
        related_name='reports'
    )
    year = models.IntegerField('Год отчета')
    report_file = models.FileField(
        'PDF файл',
        upload_to='reports/%Y/',
        help_text='Загрузите PDF файл с отчетом'
    )
    title = models.CharField('Название отчета', max_length=200, blank=True)
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)

    class Meta:
        verbose_name = 'Отчет по дому'
        verbose_name_plural = 'Отчеты по домам'
        ordering = ['-year', 'house']
        unique_together = ['house', 'year']

    def __str__(self):
        return f"{self.house.address} - {self.year} год"

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"Отчет за {self.year} год"
        super().save(*args, **kwargs)