from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at'
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': (
                'first_name', 'last_name', 'email',
                'profile_picture', 'banner_image', 'bio', 'location'
            )
        }),
        ('Social', {
            'fields': ('followers',)
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )

    readonly_fields = ('created_at',)  # allow editing followers
    filter_horizontal = ('followers', 'groups', 'user_permissions')
