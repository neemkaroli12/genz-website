from django.contrib import admin
from .models import GenzMember, Event, EventRegistration


@admin.register(GenzMember)
class GenzMemberAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "age",
        "city",
        "created_at",
    )

    list_filter = (
        "city",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "city",
        "interests",
        "looking_for",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )



@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "event_type",
        "mode",
        "event_date",
        "start_time",
        "seats",
        "registered_count",
        "is_featured",
        "is_active",
    )

    list_filter = (
        "event_type",
        "mode",
        "is_featured",
        "is_active",
        "event_date",
    )

    search_fields = (
        "title",
        "description",
        "location",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }

    list_editable = (
        "is_featured",
        "is_active",
    )


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):

    list_display = (
        "event",
        "member",
        "registered_at",
    )

    list_filter = (
        "event",
        "registered_at",
    )

    search_fields = (
        "event__title",
        "member__username",
    )

    readonly_fields = (
        "registered_at",
    )