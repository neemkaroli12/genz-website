from django.db import models
from django.conf import settings

class GenzMember(models.Model):

    name = models.CharField(max_length=100)

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    password = models.CharField(
        max_length=128,
        blank=True
    )

    age = models.PositiveIntegerField()

    city = models.CharField(max_length=100)

    profile_photo = models.ImageField(
        upload_to="genz_profiles/",
        blank=True,
        null=True
    )

    interests = models.TextField(blank=True)

    looking_for = models.TextField(blank=True)

    about = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "GENZ Member"
        verbose_name_plural = "GENZ Members"




class Event(models.Model):

    EVENT_TYPES = [
        ("workshop", "Workshop"),
        ("meetup", "Meetup"),
        ("talk", "Talk"),
        ("career", "Career"),
        ("community", "Community"),
    ]

    MODE_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline"),
    ]

    title = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )

    description = models.TextField()

    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        default="workshop"
    )

    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default="online"
    )

    event_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField(
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=200,
        blank=True
    )

    meeting_link = models.URLField(
        blank=True
    )

    image = models.ImageField(
        upload_to="events/",
        blank=True,
        null=True
    )

    seats = models.PositiveIntegerField(
        default=50
    )

    is_featured = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["event_date", "start_time"]

    def __str__(self):
        return self.title

    @property
    def registered_count(self):
        return self.registrations.count()

    @property
    def available_seats(self):
        return max(
            self.seats - self.registered_count,
            0
        )

    @property
    def is_full(self):
        return self.available_seats <= 0


class EventRegistration(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    # FIX 3: pehle settings.AUTH_USER_MODEL (Django User) tha,
    # lekin app mein login GenzMember se hota hai
    member = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="event_registrations"
    )

    registered_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "member"],
                name="unique_event_member"
            )
        ]

    def __str__(self):
        return f"{self.member} - {self.event.title}"

class Post(models.Model):
    member = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    content = models.TextField()

    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member.name} - Post"


class Follow(models.Model):
    follower = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="following"
    )

    following = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="followers"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_member_follow"
            )
        ]

    def __str__(self):
        return f"{self.follower.name} follows {self.following.name}"

class FollowRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    sender = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="sent_follow_requests"
    )

    receiver = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="received_follow_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_follow_request"
            )
        ]

    def __str__(self):
        return f"{self.sender.name} → {self.receiver.name}"

class PostLike(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes"
    )

    member = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="liked_posts"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "member"],
                name="unique_post_like"
            )
        ]

class Message(models.Model):
    sender = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    receiver = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.name} → {self.receiver.name}"


class Notification(models.Model):
    recipient = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        GenzMember,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=30,
        default="general"
    )

    message = models.CharField(
        max_length=255
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message