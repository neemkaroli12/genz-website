from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from django.utils import timezone
from .models import (
    Event,
    EventRegistration,
    GenzMember,
    Post,
    Follow,
    FollowRequest,
    PostLike,
    Message,
    Notification,
)


# =========================================
# HOME
# =========================================

def home(request):

    member = None

    member_id = request.session.get("genz_member_id")

    if member_id:

        try:
            member = GenzMember.objects.get(id=member_id)

        except GenzMember.DoesNotExist:
            request.session.pop("genz_member_id", None)

    return render(
        request,
        "home.html",
        {
            "member": member
        }
    )


# =========================================
# JOIN
# =========================================

def join(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        age = request.POST.get("age")
        city = request.POST.get("city")

        interests = request.POST.getlist("interests")
        looking_for = request.POST.getlist("looking_for")

        about = request.POST.get("about", "")

        profile_photo = request.FILES.get("profile_photo")

        # EMAIL ALREADY EXISTS

        if GenzMember.objects.filter(email=email).exists():

            return render(
                request,
                "join.html",
                {
                    "error": "This email is already registered. Please login."
                }
            )

        # CREATE MEMBER

        member = GenzMember.objects.create(
            name=name,
            email=email,
            password=make_password(password),
            age=int(age),
            city=city,
            profile_photo=profile_photo,
            interests=", ".join(interests),
            looking_for=", ".join(looking_for),
            about=about
        )

        # LOGIN USER

        request.session["genz_member_id"] = member.id

        return redirect("join_dashboard")

    return render(request, "join.html")


# =========================================
# LOGIN
# =========================================

def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            member = GenzMember.objects.get(email=email)

        except GenzMember.DoesNotExist:

            return render(
                request,
                "login.html",
                {
                    "error": "Email or password is incorrect."
                }
            )

        # CHECK PASSWORD

        if check_password(password, member.password):

            request.session["genz_member_id"] = member.id

            return redirect("home")

        return render(
            request,
            "login.html",
            {
                "error": "Email or password is incorrect."
            }
        )

    return render(request, "login.html")


# =========================================
# PROFILE
# =========================================

def profile(request):
    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    interests = [
        item.strip()
        for item in member.interests.split(",")
        if item.strip()
    ]

    looking_for = [
        item.strip()
        for item in member.looking_for.split(",")
        if item.strip()
    ]

    posts = Post.objects.filter(
        member=member
    ).prefetch_related("likes")

    followers_count = Follow.objects.filter(
        following=member
    ).count()

    following_count = Follow.objects.filter(
        follower=member
    ).count()

    context = {
        "member": member,
        "interests": interests,
        "looking_for": looking_for,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
    }

    return render(request, "profile.html", context)


@require_POST
def create_post(request):
    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse(
            {"success": False, "message": "Please login first"},
            status=401
        )

    member = get_object_or_404(GenzMember, id=member_id)

    content = request.POST.get("content", "").strip()
    image = request.FILES.get("image")

    if not content and not image:
        return JsonResponse({
            "success": False,
            "message": "Write something or upload an image"
        })

    post = Post.objects.create(
        member=member,
        content=content,
        image=image
    )

    return JsonResponse({
        "success": True,
        "post_id": post.id,
        "message": "Post created successfully"
    })


@require_POST
def delete_post(request, post_id):
    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    post = get_object_or_404(
        Post,
        id=post_id,
        member_id=member_id
    )

    post.delete()

    return JsonResponse({
        "success": True,
        "message": "Post deleted successfully"
    })


@require_POST
def toggle_like(request, post_id):
    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    post = get_object_or_404(Post, id=post_id)
    member = get_object_or_404(GenzMember, id=member_id)

    like = PostLike.objects.filter(
        post=post,
        member=member
    ).first()

    if like:
        like.delete()
        liked = False
    else:
        PostLike.objects.create(
            post=post,
            member=member
        )
        liked = True

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes_count": post.likes.count()
    })


@require_POST
def toggle_follow(request, member_id):
    current_member_id = request.session.get("genz_member_id")

    if not current_member_id:
        return JsonResponse({"success": False}, status=401)

    if int(current_member_id) == int(member_id):
        return JsonResponse({
            "success": False,
            "message": "You cannot follow yourself"
        })

    follower = get_object_or_404(GenzMember, id=current_member_id)
    following = get_object_or_404(GenzMember, id=member_id)

    follow = Follow.objects.filter(
        follower=follower,
        following=following
    ).first()

    if follow:
        follow.delete()
        is_following = False
    else:
        Follow.objects.create(
            follower=follower,
            following=following
        )
        is_following = True

    followers_count = Follow.objects.filter(
        following=following
    ).count()

    return JsonResponse({
        "success": True,
        "is_following": is_following,
        "followers_count": followers_count
    })


# =========================================
# FOLLOW REQUESTS
# =========================================

@require_POST
def send_follow_request(request, member_id):

    sender_id = request.session.get("genz_member_id")

    if not sender_id:
        return JsonResponse(
            {"success": False, "message": "Please login first"},
            status=401
        )

    sender = get_object_or_404(GenzMember, id=sender_id)
    receiver = get_object_or_404(GenzMember, id=member_id)

    if sender.id == receiver.id:
        return JsonResponse({
            "success": False,
            "message": "You cannot follow yourself"
        })

    if Follow.objects.filter(
        follower=sender,
        following=receiver
    ).exists():
        return JsonResponse({
            "success": True,
            "status": "following",
            "message": "Already following"
        })

    follow_request, created = FollowRequest.objects.get_or_create(
        sender=sender,
        receiver=receiver,
        defaults={"status": "pending"}
    )

    if not created:

        if follow_request.status == "pending":
            return JsonResponse({
                "success": True,
                "status": "pending",
                "message": "Request already sent"
            })

        if follow_request.status == "accepted":
            return JsonResponse({
                "success": True,
                "status": "following"
            })

        follow_request.status = "pending"
        follow_request.save(update_fields=["status"])

    Notification.objects.create(
        recipient=receiver,
        sender=sender,
        notification_type="follow_request",
        message=f"{sender.name} sent you a follow request"
    )

    return JsonResponse({
        "success": True,
        "status": "pending",
        "message": "Follow request sent successfully"
    })


@require_POST
def accept_follow_request(request, request_id):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    follow_request = get_object_or_404(
        FollowRequest,
        id=request_id,
        receiver_id=member_id,
        status="pending"
    )

    follow_request.status = "accepted"
    follow_request.save(update_fields=["status"])

    Follow.objects.get_or_create(
        follower=follow_request.sender,
        following=follow_request.receiver
    )

    # Receiver ki follow_request notification ko read mark karo
    Notification.objects.filter(
        recipient_id=member_id,
        sender=follow_request.sender,
        notification_type="follow_request"
    ).update(is_read=True)

    # Sender ko batao ki request accept ho gayi
    Notification.objects.create(
        recipient=follow_request.sender,
        sender=follow_request.receiver,
        notification_type="follow_accepted",
        message=f"{follow_request.receiver.name} accepted your follow request"
    )

    return JsonResponse({
        "success": True,
        "message": "Follow request accepted"
    })


@require_POST
def reject_follow_request(request, request_id):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    follow_request = get_object_or_404(
        FollowRequest,
        id=request_id,
        receiver_id=member_id,
        status="pending"
    )

    follow_request.status = "rejected"
    follow_request.save(update_fields=["status"])

    Notification.objects.filter(
        recipient_id=member_id,
        sender=follow_request.sender,
        notification_type="follow_request"
    ).update(is_read=True)

    return JsonResponse({
        "success": True,
        "message": "Follow request rejected"
    })


@require_POST
def cancel_follow_request(request, request_id):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    follow_request = get_object_or_404(
        FollowRequest,
        id=request_id,
        sender_id=member_id,
        status="pending"
    )

    # Receiver ki purani notification hata do
    Notification.objects.filter(
        recipient=follow_request.receiver,
        sender=follow_request.sender,
        notification_type="follow_request"
    ).delete()

    follow_request.delete()

    return JsonResponse({
        "success": True,
        "message": "Follow request cancelled"
    })


# =========================================
# CHANGE PHOTO
# =========================================

def change_photo(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    if request.method == "POST":

        new_photo = request.FILES.get("profile_photo")

        if new_photo:

            if member.profile_photo:
                member.profile_photo.delete(save=False)

            member.profile_photo = new_photo

            member.save()

    return redirect("profile")


# =========================================
# EDIT PROFILE
# =========================================

def edit_profile(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    if request.method == "POST":

        member.name = request.POST.get("name")
        member.age = request.POST.get("age")
        member.city = request.POST.get("city")
        member.about = request.POST.get("about", "")

        interests = request.POST.getlist("interests")
        looking_for = request.POST.getlist("looking_for")

        member.interests = ", ".join(interests)
        member.looking_for = ", ".join(looking_for)

        new_photo = request.FILES.get("profile_photo")

        if new_photo:

            if member.profile_photo:
                member.profile_photo.delete(save=False)

            member.profile_photo = new_photo

        member.save()

        return redirect("profile")

    return render(
        request,
        "join.html",
        {
            "member": member,
            "edit_mode": True
        }
    )


# =========================================
# DELETE PROFILE
# =========================================

def delete_profile(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    if request.method == "POST":

        if member.profile_photo:
            member.profile_photo.delete(save=False)

        member.delete()

        request.session.pop("genz_member_id", None)

        return redirect("home")

    # delete_profile.html template exist nahi karta,
    # isliye GET par wapas profile par bhej do.
    return redirect("profile")


# =========================================
# LOGOUT
# =========================================

def logout_profile(request):

    request.session.pop("genz_member_id", None)

    return redirect("home")


# =========================================
# STATIC PAGES
# =========================================

def education(request):
    return render(request, "education.html")


def frontend_course(request):
    return render(request, "frontend_course.html")


def uiux_course(request):
    return render(request, "uiux_course.html")


def career_skills(request):
    return render(request, "career_skills.html")


def medical(request):
    return render(request, "medical.html")


# =========================================
# EVENTS
# =========================================

def events(request):

    today = timezone.localdate()

    events_list = Event.objects.filter(
        is_active=True,
        event_date__gte=today
    ).prefetch_related("registrations")

    featured_event = events_list.filter(
        is_featured=True
    ).first()

    member_id = request.session.get("genz_member_id")

    registered_event_ids = []

    if member_id:
        registered_event_ids = list(
            EventRegistration.objects.filter(
                member_id=member_id
            ).values_list(
                "event_id",
                flat=True
            )
        )

    return render(
        request,
        "events.html",
        {
            "events": events_list,
            "featured_event": featured_event,
            "registered_event_ids": registered_event_ids,
        }
    )


def register_event(request, event_id):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    event = get_object_or_404(
        Event,
        id=event_id,
        is_active=True
    )

    if request.method != "POST":
        return redirect("events")

    if event.event_date < timezone.localdate():
        messages.error(request, "This event has already ended.")
        return redirect("events")

    if event.is_full:
        messages.error(request, "Sorry, this event is full.")
        return redirect("events")

    registration, created = EventRegistration.objects.get_or_create(
        event=event,
        member=member
    )

    if created:
        messages.success(
            request,
            "You have successfully registered for this event!"
        )
    else:
        messages.info(
            request,
            "You are already registered for this event."
        )

    return redirect("events")


# =========================================
# CHALLENGES
# =========================================

def challenges(request):
    return render(request, "challenges.html")


def challenge_detail(request):
    return render(request, "challenge_detail.html")


# =========================================
# JOIN DASHBOARD
# =========================================

def join_dashboard(request):
    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    posts = Post.objects.filter(
        member=member
    ).order_by("-created_at")

    followers_count = Follow.objects.filter(
        following=member
    ).count()

    following_count = Follow.objects.filter(
        follower=member
    ).count()

    registered_events = EventRegistration.objects.filter(
        member=member
    ).select_related("event")

    # Incoming follow requests
    received_follow_requests = FollowRequest.objects.filter(
        receiver=member,
        status="pending"
    ).select_related("sender")

    # Already following people
    following_ids = Follow.objects.filter(
        follower=member
    ).values_list("following_id", flat=True)

    # Pending sent requests
    pending_sent_ids = FollowRequest.objects.filter(
        sender=member,
        status="pending"
    ).values_list("receiver_id", flat=True)

    # Suggested people
    people = GenzMember.objects.exclude(
        id=member.id
    ).exclude(
        id__in=following_ids
    ).exclude(
        id__in=pending_sent_ids
    ).order_by("-created_at")[:8]

    context = {
        "member": member,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
        "registered_events": registered_events,
        "received_follow_requests": received_follow_requests,
        "people": people,
    }

    return render(request, "join_dashboard.html", context)


# =========================================
# MESSAGES
# =========================================

def messages_view(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    people = GenzMember.objects.exclude(id=member.id)

    unread_messages = Message.objects.filter(
        receiver=member,
        is_read=False
    ).count()

    return render(
        request,
        "messages.html",
        {
            "member": member,
            "people": people,
            "unread_messages": unread_messages,
        }
    )


def conversation_view(request, member_id):

    current_member_id = request.session.get("genz_member_id")

    if not current_member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=current_member_id)

    other_member = get_object_or_404(GenzMember, id=member_id)

    if member.id == other_member.id:
        return redirect("messages")

    messages_list = Message.objects.filter(
        sender=member,
        receiver=other_member
    ) | Message.objects.filter(
        sender=other_member,
        receiver=member
    )

    messages_list = messages_list.order_by("created_at")

    Message.objects.filter(
        sender=other_member,
        receiver=member,
        is_read=False
    ).update(is_read=True)

    return render(
        request,
        "conversation.html",
        {
            "member": member,
            "other_member": other_member,
            "messages": messages_list,
        }
    )


@require_POST
def send_message(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Please login first"
            },
            status=401
        )

    sender = get_object_or_404(GenzMember, id=member_id)

    receiver_id = request.POST.get("receiver_id")

    content = request.POST.get("content", "").strip()

    if not receiver_id:
        return JsonResponse({
            "success": False,
            "message": "Receiver is required"
        })

    if not content:
        return JsonResponse({
            "success": False,
            "message": "Message cannot be empty"
        })

    receiver = get_object_or_404(GenzMember, id=receiver_id)

    if sender.id == receiver.id:
        return JsonResponse({
            "success": False,
            "message": "You cannot message yourself"
        })

    message = Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=content
    )

    Notification.objects.create(
        recipient=receiver,
        sender=sender,
        notification_type="message",
        message=f"{sender.name} sent you a message"
    )

    return JsonResponse({
        "success": True,
        "message": message.content,
        "message_id": message.id,
        "created_at": message.created_at.strftime("%d %b, %I:%M %p")
    })


# =========================================
# NOTIFICATIONS
# =========================================

def notifications_view(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return redirect("login")

    member = get_object_or_404(GenzMember, id=member_id)

    notifications = Notification.objects.filter(recipient=member)

    unread_count = notifications.filter(is_read=False).count()

    # pending requests: {sender_id: request_id}
    pending_requests = {
        fr.sender_id: fr.id
        for fr in FollowRequest.objects.filter(
            receiver=member,
            status="pending"
        )
    }

    notifications = list(notifications.select_related("sender"))

    for item in notifications:
        if item.notification_type == "follow_request":
            item.request_id = pending_requests.get(item.sender_id)
        else:
            item.request_id = None

    return render(
        request,
        "notifications.html",
        {
            "member": member,
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )


@require_POST
def mark_notification_read(request, notification_id):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    member = get_object_or_404(GenzMember, id=member_id)

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=member
    )

    notification.is_read = True

    notification.save(update_fields=["is_read"])

    return JsonResponse({"success": True})


@require_POST
def mark_all_notifications_read(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"success": False}, status=401)

    member = get_object_or_404(GenzMember, id=member_id)

    Notification.objects.filter(
        recipient=member,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"success": True})


def notification_count(request):

    member_id = request.session.get("genz_member_id")

    if not member_id:
        return JsonResponse({"count": 0})

    count = Notification.objects.filter(
        recipient_id=member_id,
        is_read=False
    ).count()

    return JsonResponse({"count": count})