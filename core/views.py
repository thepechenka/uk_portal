from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import models

from .models import News, Request, Comment, House
from .forms import RequestForm, CommentForm
from accounts.decorators import apartment_required
from accounts.views import send_request_email_notification

import logging
logger = logging.getLogger(__name__)


def get_user_context(user):
    """Возвращает контекст с информацией о пользователе"""
    return {
        'user': user,
        'user_has_apartment': user.has_apartment() if hasattr(user, 'has_apartment') else False,
    }


class HomeView(ListView):
    template_name = 'core/home.html'
    context_object_name = 'news_list'
    paginate_by = 3

    def get_queryset(self):
        # На главной показываем все новости (для всех)
        return News.objects.filter(is_published=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная страница'
        context['approved_comments'] = Comment.objects.filter(
            is_approved=True
        ).order_by('-created_at')[:6]
        return context


@login_required
@apartment_required
def request_create_view(request):
    if request.method == 'POST':
        form = RequestForm(request.POST, user=request.user)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.user = request.user
            request_obj.apartment = request.user.apartment
            request_obj.save()

            # ОТПРАВКА УВЕДОМЛЕНИЯ НА ПОЧТУ
            try:
                send_request_email_notification(request_obj)
                logger.info(f"Уведомление о заявке #{request_obj.id} отправлено")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")

            messages.success(request, 'Заявка успешно создана!')
            return redirect('my_requests')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RequestForm(user=request.user)

    context = {
        'form': form,
        **get_user_context(request.user),
    }
    return render(request, 'account/request_create.html', context)


@login_required
@apartment_required
def comment_create_view(request):
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.is_approved = False
            comment.save()
            messages.success(request, 'Спасибо за ваш отзыв! Он будет проверен модератором.')
            return redirect('home')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CommentForm(user=request.user)

    context = {
        'form': form,
        **get_user_context(request.user),
    }
    return render(request, 'account/comment_create.html', context)


class CommentListView(ListView):
    model = Comment
    template_name = 'core/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 10

    def get_queryset(self):
        return Comment.objects.filter(is_approved=True).order_by('-created_at')


@require_GET
def api_houses(request):
    try:
        houses = House.objects.all()
        data = []

        for house in houses:
            reports = []
            for report in house.reports.all().order_by('-year'):
                reports.append({
                    'id': report.id,
                    'year': report.year,
                    'title': report.title,
                    'file_url': report.report_file.url if report.report_file else None,
                    'uploaded_at': report.uploaded_at.strftime('%d.%m.%Y')
                })

            house_data = {
                'id': house.id,
                'address': house.address,
                'built_year': house.built_year,
                'house_type': house.house_type,
                'ceiling_type': house.ceiling_type,
                'ceiling_height': house.ceiling_height,
                'floor_count': house.floor_count,
                'entrance_count': house.entrance_count,
                'apartments_count': house.apartments_count,
                'elevator_count': house.elevator_count,
                'has_gas': house.has_gas,
                'heating_type': house.heating_type,
                'has_garbage_chute': house.has_garbage_chute,
                'is_emergency': house.is_emergency,
                'is_demolition': house.is_demolition,
                'latitude': house.latitude,
                'longitude': house.longitude,
                'coords': house.coords,
                'reports': reports,
            }
            data.append(house_data)

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class NewsListView(ListView):
    model = News
    template_name = 'core/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 9

    def get_queryset(self):
        # На странице всех новостей показываем ВСЕ новости
        return News.objects.filter(is_published=True).order_by('-created_at')


def get_user_house_news(user):
    """Возвращает новости для дома пользователя"""
    if user.is_authenticated and hasattr(user, 'apartment') and user.apartment:
        user_house = user.apartment.house
        # Новости либо для всех домов, либо конкретно для его дома
        return News.objects.filter(
            is_published=True
        ).filter(
            models.Q(houses__isnull=True) |  # новости для всех домов
            models.Q(houses=user_house)       # новости для его дома
        ).distinct().order_by('-created_at')[:5]  # последние 5 новостей
    return []