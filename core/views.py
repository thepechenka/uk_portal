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

# Добавь в начало файла с другими импортами
from django.http import HttpResponse
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


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


from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Request


@login_required
def brigade_dashboard(request):
    if not hasattr(request.user, 'brigade_chief') and not request.user.brigade_member.exists():
        return redirect('home')

    brigade = request.user.brigade_chief if hasattr(request.user,
                                                    'brigade_chief') else request.user.brigade_member.first()

    # Доступные заявки (статус new, без назначенной бригады)
    available_orders = Request.objects.filter(status='new', assigned_team__isnull=True)

    # Текущая заявка бригады (статус in_progress)
    current_order = Request.objects.filter(assigned_team=brigade, status='in_progress').first()

    # Выполненные заявки (статус done)
    completed_orders = Request.objects.filter(assigned_team=brigade, status='done').order_by('-completed_at')

    return render(request, 'core/brigade/dashboard.html', {
        'brigade': brigade,
        'available_orders': available_orders,
        'current_order': current_order,
        'completed_orders': completed_orders,
    })


@login_required
def take_workorder(request, order_id):
    brigade = request.user.brigade_chief if hasattr(request.user,
                                                    'brigade_chief') else request.user.brigade_member.first()

    # Проверка: есть ли у бригады активная заявка
    active_order = Request.objects.filter(assigned_team=brigade, status='in_progress').first()
    if active_order:
        messages.error(request, 'Сначала завершите текущую заявку!')
        return redirect('brigade_dashboard')

    order = get_object_or_404(Request, id=order_id, status='new', assigned_team__isnull=True)

    order.assigned_team = brigade
    order.status = 'in_progress'
    order.work_started_at = timezone.now()
    order.save()

    return redirect('brigade_dashboard')

@login_required
def complete_workorder(request, order_id):
    brigade = request.user.brigade_chief if hasattr(request.user,
                                                    'brigade_chief') else request.user.brigade_member.first()
    order = get_object_or_404(Request, id=order_id, assigned_team=brigade, status='in_progress')

    if request.method == 'POST':
        order.resources_used = request.POST.get('materials_used', '')
        order.hours_worked = request.POST.get('hours_worked', '')
        order.work_notes = request.POST.get('notes', '')
        order.status = 'done'
        order.completed_at = timezone.now()
        order.save()
        return redirect('brigade_dashboard')

    # Добавь brigade в контекст
    return render(request, 'core/brigade/complete.html', {
        'order': order,
        'brigade': brigade  # <--- ДОБАВЬ ЭТУ СТРОКУ
    })


@login_required
def export_order_report(request, order_id):
    """Экспорт отчёта по заявке в HTML (печать через браузер)"""
    if not hasattr(request.user, 'brigade_chief') and not request.user.brigade_member.exists():
        return redirect('home')

    order = get_object_or_404(Request, id=order_id, status='done')

    # HTML отчёт, красиво, с кириллицей
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Акт выполненных работ №{order.id}</title>
        <style>
            body {{
                font-family: 'Times New Roman', Times, serif;
                margin: 40px;
                font-size: 14px;
            }}
            h1 {{
                text-align: center;
                font-size: 18px;
                margin-bottom: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #000;
                padding: 8px;
                vertical-align: top;
            }}
            th {{
                background-color: #f0f0f0;
                text-align: left;
                width: 30%;
            }}
            .signature {{
                margin-top: 50px;
            }}
            .signature td {{
                border: none;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>АКТ ВЫПОЛНЕННЫХ РАБОТ №{order.id}</h1>

        <table>
            <tr><th>Наименование работ</th><td>{order.title}</td></tr>
            <tr><th>Описание</th><td>{order.description or '-'}</td></tr>
            <tr><th>Тип заявки</th><td>{order.get_request_type_display()}</td></tr>
            <tr><th>Статус</th><td>{order.get_status_display()}</td></tr>
            <tr><th>Приоритет</th><td>{order.get_priority_display()}</td></tr>
            <tr><th>Заявитель</th><td>{order.user.full_name}</td></tr>
            <tr><th>Квартира</th><td>{order.apartment.house.address}, кв. {order.apartment.number}</td></tr>
            <tr><th>Дата создания</th><td>{order.created_at.strftime('%d.%m.%Y %H:%M')}</td></tr>
            <tr><th>Начало работ</th><td>{order.work_started_at.strftime('%d.%m.%Y %H:%M') if order.work_started_at else '-'}</td></tr>
            <tr><th>Дата завершения</th><td>{order.completed_at.strftime('%d.%m.%Y %H:%M') if order.completed_at else '-'}</td></tr>
            <tr><th>Бригада</th><td>{order.assigned_team.name if order.assigned_team else '-'}</td></tr>
            <tr><th>Бригадир</th><td>{order.assigned_team.chief.full_name if order.assigned_team else '-'}</td></tr>
            <tr><th>Использованные материалы</th><td>{order.resources_used or '-'}</td></tr>
            <tr><th>Затрачено часов</th><td>{order.hours_worked or '-'}</td></tr>
            <tr><th>Примечания</th><td>{order.work_notes or '-'}</td></tr>
        </table>

        <table class="signature">
            <tr>
                <td style="width: 50%;">Бригадир: _______________</td>
                <td style="width: 50%;">Заявитель: _______________</td>
            </tr>
            <tr>
                <td>{order.assigned_team.chief.full_name if order.assigned_team else '-'}</td>
                <td>{order.user.full_name}</td>
            </tr>
        </table>

        <div class="footer">
            {order.completed_at.strftime('%d.%m.%Y') if order.completed_at else ''}
        </div>

        <script>
            window.print();
        </script>
    </body>
    </html>
    '''

    return HttpResponse(html)