from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorProfile, PatientProfile, Appointment, Notification
# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list view
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone')
    ordering = ('role', 'username')

    # Fields to display when editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )


# DoctorProfile Admin
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number')
    list_filter = ('specialization',)
    search_fields = ('user__username', 'user__email', 'license_number')

    def get_queryset(self, request):
        # Ensure only doctor profiles appear here
        return super().get_queryset(request).filter(user__role='doctor')


# PatientProfile Admin
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'user__email')

    def get_queryset(self, request):
        # Ensure only patient profiles appear here
        return super().get_queryset(request).filter(user__role='patient')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'patient', 'date', 'time', 'status', 'token']
    list_filter = ['doctor', 'status', 'date']
    search_fields = ['doctor__username', 'patient__username', 'doctor__doctor_profile__specialization']
    ordering = ['date', 'time', 'token']



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'event_type', 'sent_at']
    list_filter = ['event_type', 'sent_at']
    search_fields = ['recipient__username', 'subject']

