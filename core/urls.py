from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),

    path('api/houses/', views.api_houses, name='api_houses'),

    path('request/create/', views.request_create_view, name='request_create'),
    path('comment/create/', views.comment_create_view, name='comment_create'),

    path('houses/', TemplateView.as_view(template_name='core/houses.html'), name='houses'),
    path('services/', TemplateView.as_view(template_name='core/services.html'), name='services'),
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='core/contact.html'), name='contact'),

    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('brigade/', views.brigade_dashboard, name='brigade_dashboard'),
    path('brigade/take/<int:order_id>/', views.take_workorder, name='take_workorder'),
    path('brigade/complete/<int:order_id>/', views.complete_workorder, name='complete_workorder'),
    path('brigade/export/<int:order_id>/', views.export_order_report, name='export_order_report')
]