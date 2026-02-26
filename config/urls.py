from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import profile_view, my_requests_view, register_view, register_success_view, verify_email_view, resend_verification_email_view
from accounts.views import CustomPasswordResetView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),

    path('', include('core.urls')),

    # Кастомные account
    path('accounts/register/', register_view, name='register'),
    path('accounts/register/success/', register_success_view, name='register_success'),
    path('accounts/verify/<str:verification_code>/', verify_email_view, name='verify_email'),
    path('accounts/resend-verification/', resend_verification_email_view, name='resend_verification'),
    path('accounts/profile/', profile_view, name='profile'),
    path('accounts/my-requests/', my_requests_view, name='my_requests'),

    # Allauth URLs
    path('accounts/', include('allauth.urls')),
]

# Для медиа-файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)