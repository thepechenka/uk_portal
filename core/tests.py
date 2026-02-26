from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import House, Apartment, Request, Comment, News, HouseReport
from .forms import RequestForm, CommentForm
from allauth.account.models import EmailAddress

User = get_user_model()

class HouseModelTests(TestCase):
    """Тесты для модели House"""

    def setUp(self):
        self.house = House.objects.create(
            address='ул. Тестовая, 1',
            built_year=2000,
            house_type='Панельный',
            floor_count=9,
            entrance_count=2,
            apartments_count=72,
            latitude=53.762599,
            longitude=87.142835
        )

    def test_house_creation(self):
        self.assertEqual(self.house.address, 'ул. Тестовая, 1')
        self.assertEqual(self.house.built_year, 2000)
        self.assertEqual(str(self.house), 'ул. Тестовая, 1')

    def test_coords_property(self):
        self.assertEqual(self.house.coords, [53.762599, 87.142835])

        house_no_coords = House.objects.create(address='ул. Тестовая, 2')
        self.assertIsNone(house_no_coords.coords)


class ApartmentModelTests(TestCase):
    """Тесты для модели Apartment"""

    def setUp(self):
        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Иванов Иван Иванович',
            debt=5000.00
        )

    def test_apartment_creation(self):
        self.assertEqual(self.apartment.number, '42')
        self.assertEqual(self.apartment.account_number, '123456789')
        self.assertEqual(self.apartment.owner_fio, 'Иванов Иван Иванович')
        self.assertEqual(self.apartment.debt, 5000.00)
        self.assertEqual(str(self.apartment), 'кв. 42, ул. Тестовая, 1')

    def test_unique_together_constraint(self):
        with self.assertRaises(Exception):
            Apartment.objects.create(
                house=self.house,
                number='42',
                account_number='987654321',
                owner_fio='Петров Петр Петрович'
            )


class RequestModelTests(TestCase):
    """Тесты для модели Request"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Test User'
        )
        self.request = Request.objects.create(
            user=self.user,
            apartment=self.apartment,
            request_type='repair',
            title='Тестовая заявка',
            description='Описание тестовой заявки',
            priority=2
        )

    def test_request_creation(self):
        self.assertEqual(self.request.title, 'Тестовая заявка')
        self.assertEqual(self.request.status, 'new')
        self.assertEqual(self.request.get_status_display(), 'Новая')
        self.assertEqual(str(self.request), 'Тестовая заявка - Новая')

    def test_status_choices(self):
        self.request.status = 'in_progress'
        self.request.save()
        self.assertEqual(self.request.get_status_display(), 'В работе')

        self.request.status = 'done'
        self.request.save()
        self.assertEqual(self.request.get_status_display(), 'Завершена')

        self.request.status = 'cancelled'
        self.request.save()
        self.assertEqual(self.request.get_status_display(), 'Отменена')


class CommentModelTests(TestCase):
    """Тесты для модели Comment"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.comment = Comment.objects.create(
            user=self.user,
            content='Отличная работа!',
            rating=5,
            is_approved=False
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.content, 'Отличная работа!')
        self.assertEqual(self.comment.rating, 5)
        self.assertFalse(self.comment.is_approved)
        self.assertEqual(str(self.comment), f'Отзыв от {self.user}')

    def test_rating_choices(self):
        self.assertEqual(self.comment.get_rating_display(), '★★★★★')

        self.comment.rating = 1
        self.comment.save()
        self.assertEqual(self.comment.get_rating_display(), '★☆☆☆☆')


class NewsModelTests(TestCase):
    """Тесты для модели News"""

    def setUp(self):
        self.news = News.objects.create(
            title='Тестовая новость',
            content='Полное содержание тестовой новости',
            short_description='Краткое описание',
            is_published=True
        )

    def test_news_creation(self):
        self.assertEqual(self.news.title, 'Тестовая новость')
        self.assertEqual(self.news.content, 'Полное содержание тестовой новости')
        self.assertTrue(self.news.is_published)
        self.assertEqual(str(self.news), 'Тестовая новость')

    def test_unpublished_news(self):
        self.news.is_published = False
        self.news.save()
        self.assertFalse(self.news.is_published)


class HouseReportModelTests(TestCase):
    """Тесты для модели HouseReport"""

    def setUp(self):
        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.report = HouseReport.objects.create(
            house=self.house,
            year=2025,
            title='Годовой отчет 2025'
        )

    def test_report_creation(self):
        self.assertEqual(self.report.house, self.house)
        self.assertEqual(self.report.year, 2025)
        self.assertEqual(self.report.title, 'Годовой отчет 2025')
        self.assertEqual(str(self.report), 'ул. Тестовая, 1 - 2025 год')

    def test_auto_title_on_save(self):
        report = HouseReport.objects.create(
            house=self.house,
            year=2026
        )
        self.assertEqual(report.title, 'Отчет за 2026 год')

    def test_unique_together_constraint(self):
        HouseReport.objects.create(
            house=self.house,
            year=2024
        )
        with self.assertRaises(Exception):
            HouseReport.objects.create(
                house=self.house,
                year=2024
            )


class RequestFormTests(TestCase):
    """Тесты для формы RequestForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Test User'
        )
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )

    def test_valid_form_with_apartment(self):
        form_data = {
            'request_type': 'repair',
            'title': 'Тестовая заявка',
            'description': 'Описание заявки',
            'priority': 2
        }
        form = RequestForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_without_apartment(self):
        user_no_apt = User.objects.create_user(
            email='test2@example.com',
            full_name='Test User 2',
            password='testpass123'
        )
        form_data = {
            'request_type': 'repair',
            'title': 'Тестовая заявка',
            'description': 'Описание заявки',
            'priority': 2
        }
        form = RequestForm(data=form_data, user=user_no_apt)
        self.assertFalse(form.is_valid())

    def test_form_missing_fields(self):
        form_data = {
            'request_type': 'repair',
            'title': '',
            'description': '',
            'priority': 2
        }
        form = RequestForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())


class CommentFormTests(TestCase):
    """Тесты для формы CommentForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )
        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Test User'
        )
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )

    def test_valid_form_with_apartment(self):
        form_data = {
            'content': 'Отличная работа!',
            'rating': 5
        }
        form = CommentForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_without_apartment(self):
        user_no_apt = User.objects.create_user(
            email='test2@example.com',
            full_name='Test User 2',
            password='testpass123'
        )
        form_data = {
            'content': 'Отличная работа!',
            'rating': 5
        }
        form = CommentForm(data=form_data, user=user_no_apt)
        self.assertFalse(form.is_valid())

    def test_form_missing_fields(self):
        form_data = {
            'content': '',
            'rating': ''
        }
        form = CommentForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())


class HomeViewTests(TestCase):
    """Тесты для HomeView"""

    def setUp(self):
        self.client = Client()

        for i in range(5):
            News.objects.create(
                title=f'Новость {i}',
                content=f'Содержание {i}',
                short_description=f'Описание {i}',
                is_published=True
            )

        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )

        for i in range(3):
            Comment.objects.create(
                user=self.user,
                content=f'Отзыв {i}',
                rating=5,
                is_approved=True
            )

    def test_home_view_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_view_context(self):
        response = self.client.get(reverse('home'))
        self.assertIn('news_list', response.context)
        self.assertIn('approved_comments', response.context)
        self.assertEqual(len(response.context['news_list']), 3)
        self.assertEqual(len(response.context['approved_comments']), 3)


class NewsListViewTests(TestCase):
    """Тесты для NewsListView"""

    def setUp(self):
        self.client = Client()

        for i in range(10):
            News.objects.create(
                title=f'Новость {i}',
                content=f'Содержание {i}',
                short_description=f'Описание {i}',
                is_published=True
            )

        News.objects.create(
            title='Неопубликованная новость',
            content='Содержание',
            short_description='Описание',
            is_published=False
        )

    def test_news_list_view_status_code(self):
        response = self.client.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/news_list.html')

    def test_news_list_pagination(self):
        response = self.client.get(reverse('news_list'))
        self.assertEqual(len(response.context['news_list']), 9)

    def test_news_list_only_published(self):
        response = self.client.get(reverse('news_list'))
        for news in response.context['news_list']:
            self.assertTrue(news.is_published)

    def test_news_list_ordering(self):
        response = self.client.get(reverse('news_list'))
        news_list = response.context['news_list']
        for i in range(len(news_list) - 1):
            self.assertGreaterEqual(
                news_list[i].created_at,
                news_list[i + 1].created_at
            )


class ApiHousesTests(TestCase):
    """Тесты для api_houses"""

    def setUp(self):
        self.client = Client()

        self.house = House.objects.create(
            address='ул. Тестовая, 1',
            built_year=2000,
            floor_count=9,
            apartments_count=72,
            latitude=53.762599,
            longitude=87.142835
        )

        HouseReport.objects.create(
            house=self.house,
            year=2025,
            title='Отчет 2025'
        )

    def test_api_houses_status_code(self):
        response = self.client.get('/api/houses/')
        self.assertEqual(response.status_code, 200)

    def test_api_houses_data_structure(self):
        response = self.client.get('/api/houses/')
        data = response.json()

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

        house_data = data[0]
        self.assertIn('id', house_data)
        self.assertIn('address', house_data)
        self.assertIn('coords', house_data)
        self.assertIn('reports', house_data)

        self.assertEqual(house_data['address'], 'ул. Тестовая, 1')
        self.assertEqual(house_data['coords'], [53.762599, 87.142835])

    def test_api_houses_reports(self):
        response = self.client.get('/api/houses/')
        data = response.json()

        house_data = data[0]
        self.assertIn('reports', house_data)
        self.assertEqual(len(house_data['reports']), 1)
        self.assertEqual(house_data['reports'][0]['year'], 2025)


class RequestCreateViewTests(TestCase):
    """Тесты для request_create_view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )

        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Test User'
        )

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )

    def test_request_create_view_without_apartment(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('request_create'))
        self.assertEqual(response.status_code, 302)

    def test_request_create_view_with_apartment(self):
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse('request_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/request_create.html')

    def test_request_create_post_valid(self):
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        self.client.force_login(self.user)

        form_data = {
            'request_type': 'repair',
            'title': 'Новая заявка',
            'description': 'Описание заявки',
            'priority': 2
        }

        response = self.client.post(reverse('request_create'), form_data)
        self.assertRedirects(response, reverse('my_requests'))
        self.assertEqual(Request.objects.count(), 1)

        request_obj = Request.objects.first()
        self.assertEqual(request_obj.title, 'Новая заявка')
        self.assertEqual(request_obj.user, self.user)
        self.assertEqual(request_obj.apartment, self.apartment)


class CommentCreateViewTests(TestCase):
    """Тесты для comment_create_view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpass123'
        )

        self.house = House.objects.create(address='ул. Тестовая, 1')
        self.apartment = Apartment.objects.create(
            house=self.house,
            number='42',
            account_number='123456789',
            owner_fio='Test User'
        )

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )

    def test_comment_create_view_without_apartment(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('comment_create'))
        self.assertEqual(response.status_code, 302)

    def test_comment_create_view_with_apartment(self):
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse('comment_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/comment_create.html')

    def test_comment_create_post_valid(self):
        self.user.apartment = self.apartment
        self.user.apartment_confirmed = True
        self.user.save()

        self.client.force_login(self.user)

        form_data = {
            'content': 'Отличная работа!',
            'rating': 5
        }

        response = self.client.post(reverse('comment_create'), form_data)
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.content, 'Отличная работа!')
        self.assertEqual(comment.user, self.user)
        self.assertFalse(comment.is_approved)