from django import forms
from django.core.exceptions import ValidationError
from .models import Request, Comment


class RequestForm(forms.ModelForm):
    """Форма создания заявки"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Если пользователь не привязан к квартире, показываем предупреждение
        if self.user and not self.user.has_apartment():
            self.fields = {}  # Убираем все поля
            self.add_error(None, 'Для создания заявки необходимо привязать квартиру.')

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем, привязана ли квартира
        if self.user and not self.user.has_apartment():
            raise ValidationError(
                'Для создания заявки необходимо привязать квартиру.'
                'Пожалуйста, перейдите в личный кабинет → "Мои данные" → "Привязать квартиру".'
            )

        return cleaned_data

    class Meta:
        model = Request
        fields = ['request_type', 'title', 'description', 'priority']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое описание проблемы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Подробно опишите проблему...'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    """Форма добавления комментария"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Если пользователь не привязан к квартире, показываем предупреждение
        if self.user and not self.user.has_apartment():
            self.fields = {}  # Убираем все поля
            self.add_error(None, 'Для оставления отзывов необходимо привязать квартиру.')

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем, привязана ли квартира
        if self.user and not self.user.has_apartment():
            raise ValidationError(
                'Для оставления отзывов необходимо привязать квартиру.'
                'Пожалуйста, перейдите в личный кабинет → "Мои данные" → "Привязать квартиру".'
            )

        return cleaned_data

    class Meta:
        model = Comment
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишите ваш опыт работы с управляющей компанией...'
            }),
            'rating': forms.Select(attrs={'class': 'form-control'}, choices=[
                (1, '★☆☆☆☆ - Плохо'),
                (2, '★★☆☆☆ - Удовлетворительно'),
                (3, '★★★☆☆ - Хорошо'),
                (4, '★★★★☆ - Очень хорошо'),
                (5, '★★★★★ - Отлично'),
            ]),
        }