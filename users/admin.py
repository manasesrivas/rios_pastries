from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombres', 'apellidos', 'estado')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True).filter(
                estado=User.Estado.ACTIVO,
            )
        return queryset

    def has_view_permission(self, request, obj=None):
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        obj.estado = User.Estado.ELIMINADO
        obj.is_active = False
        obj.save(update_fields=['estado', 'is_active'])

    def delete_queryset(self, request, queryset):
        queryset.update(estado=User.Estado.ELIMINADO, is_active=False)

    def save_model(self, request, obj, form, change):
        previous_state = None
        if change:
            previous_state = User.objects.filter(pk=obj.pk).values_list(
                'estado',
                flat=True,
            ).first()

        if obj.estado == User.Estado.ELIMINADO:
            obj.is_active = False
        elif previous_state == User.Estado.ELIMINADO:
            obj.is_active = True

        super().save_model(request, obj, form, change)