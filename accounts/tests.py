from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomSignupForm, ProfileUpdateForm
from core.models import House, Apartment
from allauth.account.models import EmailAddress

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Тесты для модели CustomUser"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user_data = {
            'email': 'test@example.com',
            'full_name': 'Иванов Иван Иванович',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user(self):
        """Тест создания обычного пользователя"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.full_name, 'Иванов Иван Иванович')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_active)

    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            full_name='Админ Админов',
            password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.apartment_confirmed)
        self.assertTrue(admin.is_verified)

    def test_user_str_method(self):
        """Тест строкового представления"""
        expected = f"{self.user.full_name} ({self.user.email})"
        self.assertEqual(str(self.user), expected)

    def test_has_apartment_method(self):
        """Тест метода has_apartment"""
        # Создаем дом и квартиру
        house = House.objects.create(
            address='ул. Тестовая, 1',
            floor_count=5
        )
        apartment = Apartment.objects.create(
            house=house,
            number='1',
            account_number='123456',
            owner_fio='Иванов Иван'
        )

        # Пользователь без квартиры
        self.assertFalse(self.user.has_apartment())

        # Привязываем квартиру
        self.user.apartment = apartment
        self.user.apartment_confirmed = True
        self.user.save()

        self.assertTrue(self.user.has_apartment())

    def test_generate_verification_code(self):
        """Тест генерации кода подтверждения"""
        old_code = self.user.verification_code
        new_code = self.user.generate_new_verification_code()

        self.assertIsNotNone(new_code)
        self.assertNotEqual(old_code, new_code)
        # Проверяем что код не пустой, без жесткой привязки к длине
        self.assertTrue(len(new_code) > 20)
        self.assertIsInstance(new_code, str)


class CustomUserManagerTests(TestCase):
    """Тесты для менеджера пользователей"""

    def test_create_user_no_email(self):
        """Тест создания пользователя без email"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                full_name='Тест',
                password='pass123'
            )

    def test_create_user_with_extra_fields(self):
        """Тест создания пользователя с доп. полями"""
        user = User.objects.create_user(
            email='test2@example.com',
            full_name='Тест Тестов',
            password='pass123',
            phone='+7 999 123-45-67'
        )
        self.assertEqual(user.phone, '+7 999 123-45-67')
        self.assertIsNotNone(user.verification_code)


class CustomUserFormTests(TestCase):
    """Тесты для форм"""

    def setUp(self):
        self.valid_data = {
            'email': 'newuser@example.com',
            'full_name': 'Новый Пользователь',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }

    def test_custom_user_creation_form_valid(self):
        """Тест валидной формы регистрации"""
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_password_mismatch(self):
        """Тест несовпадения паролей"""
        data = self.valid_data.copy()
        data['password2'] = 'differentpass'
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_custom_user_creation_form_duplicate_email(self):
        """Тест уникальности email"""
        User.objects.create_user(
            email='newuser@example.com',
            full_name='Существующий',
            password='pass123'
        )
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_custom_signup_form(self):
        """Тест формы allauth"""
        form_data = {
            'email': 'allauth@example.com',
            'full_name': 'Аллаuth Тестов',
            'password1': 'allauthpass123',
            'password2': 'allauthpass123'
        }
        form = CustomSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Проверяем, что username не требуется
        self.assertNotIn('username', form.fields)

    def test_profile_update_form(self):
        """Тест формы обновления профиля"""
        user = User.objects.create_user(
            email='update@example.com',
            full_name='Старое Имя',
            password='pass123'
        )

        form_data = {
            'full_name': 'Новое Имя',
            'phone': '+7 999 888-77-66'
        }

        form = ProfileUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

        updated_user = form.save()
        self.assertEqual(updated_user.full_name, 'Новое Имя')
        self.assertEqual(updated_user.phone, '+7 999 888-77-66')


class AccountViewsTests(TestCase):
    """Тесты для представлений (views)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='viewuser@example.com',
            full_name='View User',
            password='viewpass123'
        )
        # Подтверждаем email для тестов, где это нужно
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )

    def test_register_view_get(self):
        """Тест GET запроса к странице регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register.html')

    def test_register_view_post_valid(self):
        """Тест POST запроса с валидными данными"""
        data = {
            'email': 'register@example.com',
            'full_name': 'Register User',
            'password1': 'register123',
            'password2': 'register123'
        }
        response = self.client.post(reverse('register'), data)

        # Должен перенаправить на страницу успеха
        self.assertRedirects(response, reverse('register_success'))

        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(email='register@example.com').exists())

    def test_register_view_post_invalid(self):
        """Тест POST запроса с невалидными данными"""
        data = {
            'email': 'invalid',
            'full_name': '',
            'password1': '123',
            'password2': '456'
        }
        response = self.client.post(reverse('register'), data)

        # Должен остаться на странице регистрации
        self.assertEqual(response.status_code, 200)
        # Проверяем, что пользователь не создан
        self.assertFalse(User.objects.filter(email='invalid').exists())

    def test_login_view(self):
        """Тест страницы входа"""
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')

    def test_login_post_success(self):
        """Тест успешного входа"""
        login_data = {
            'login': 'viewuser@example.com',
            'password': 'viewpass123'
        }
        response = self.client.post(reverse('account_login'), login_data)

        # Должен перенаправить в профиль
        self.assertRedirects(response, reverse('profile'))

    def test_profile_view_authenticated(self):
        """Тест доступа к профилю для авторизованного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile.html')
        self.assertContains(response, self.user.full_name)

    def test_profile_view_unauthenticated(self):
        """Тест доступа к профилю без авторизации"""
        response = self.client.get(reverse('profile'))
        # Проверяем что это редирект
        self.assertEqual(response.status_code, 302)
        # Проверяем что редирект на страницу логина
        self.assertTrue(response.url.startswith(reverse('account_login')))