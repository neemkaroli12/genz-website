"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from genzz import views


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "join/",
        views.join,
        name="join"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    path(
        "profile/change-photo/",
        views.change_photo,
        name="change_photo"
    ),

    path(
        "profile/edit/",
        views.edit_profile,
        name="edit_profile"
    ),

    path(
        "profile/delete/",
        views.delete_profile,
        name="delete_profile"
    ),

    path(
        "logout/",
        views.logout_profile,
        name="logout"
    ),
    path("education/", views.education, name="education"),
    path(
        "education/frontend/",
        views.frontend_course,
        name="frontend_course"
    ),
    path(
    "education/uiux/",
    views.uiux_course,
    name="uiux_course"
   ),
   path(
    "education/career-skills/",
    views.career_skills,
    name="career_skills"
   ),
   path("medical/", views.medical, name="medical"),
   path("events/", views.events, name="events"),
   path("challenges/", views.challenges, name="challenges"),
   path(
    "challenges/detail/",
    views.challenge_detail,
    name="challenge_detail"
    ),
    path(
        "join-dashboard/",
        views.join_dashboard,
        name="join_dashboard"
    ),
    path(
    "profile/post/create/",
    views.create_post,
    name="create_post"
    ),

    path(
        "profile/post/<int:post_id>/delete/",
        views.delete_post,
        name="delete_post"
    ),

    path(
        "profile/post/<int:post_id>/like/",
        views.toggle_like,
        name="toggle_like"
    ),

    path(
        "profile/<int:member_id>/follow/",
        views.toggle_follow,
        name="toggle_follow"
    ),
    path(
        "messages/",
        views.messages_view,
        name="messages"
    ),

    path(
        "messages/<int:member_id>/",
        views.conversation_view,
        name="conversation"
    ),

    path(
        "messages/send/",
        views.send_message,
        name="send_message"
    ),

    path(
        "notifications/",
        views.notifications_view,
        name="notifications"
    ),

    path(
        "notifications/read/<int:notification_id>/",
        views.mark_notification_read,
        name="mark_notification_read"
    ),

    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read"
    ),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )