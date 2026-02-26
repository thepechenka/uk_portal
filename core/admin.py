from django.contrib import admin
from .models import House, Apartment, Request, Comment, News, HouseReport


class HouseReportInline(admin.TabularInline):

    model = HouseReport
    extra = 1
    fields = ('year', 'report_file', 'title', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('address', 'built_year', 'house_type', 'floor_count', 'apartments_count', 'reports_count')
    list_filter = ('house_type', 'heating_type', 'is_emergency', 'is_demolition')
    search_fields = ('address',)

    inlines = [HouseReportInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('address', 'built_year', 'house_type')
        }),
        ('Характеристики', {
            'fields': ('ceiling_type', 'ceiling_height', 'floor_count', 'entrance_count', 'apartments_count',
                       'elevator_count')
        }),
        ('Коммуникации и состояние', {
            'fields': ('has_gas', 'heating_type', 'has_garbage_chute', 'is_emergency', 'is_demolition')
        }),
        ('Координаты для карты', {
            'fields': ('latitude', 'longitude'),
            'description': 'Укажите координаты дома. Можно получить на Яндекс.Картах, кликнув правой кнопкой по дому и выбрав "Что здесь?"'
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def reports_count(self, obj):
        return obj.reports.count()
    reports_count.short_description = 'Отчеты'


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'house', 'owner_fio', 'account_number')


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'apartment', 'status')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_content', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    list_editable = ('is_approved',)
    actions = ['approve_comments', 'reject_comments']
    search_fields = ('content', 'user__email')

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Отзыв'

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} отзывов одобрено')

    def reject_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} отзывов отклонено')


@admin.register(HouseReport)
class HouseReportAdmin(admin.ModelAdmin):
    list_display = ('house', 'year', 'title', 'uploaded_at')
    list_filter = ('year', 'house')
    search_fields = ('house__address', 'title')
    readonly_fields = ('uploaded_at',)