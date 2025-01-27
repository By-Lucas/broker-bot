from django.contrib import admin

from logs.models import SystemLogger


@admin.register(SystemLogger)
class SystemLogAbstractAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'message', 'user', "created_date")
    search_fields = ('message', 'user__email')
    list_filter = ('level', "created_date")