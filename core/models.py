from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from django.core.exceptions import ValidationError
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings

# Custom User Model
class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

# Course Model
class Course(models.Model):
    CATEGORY_CHOICES = [
        ('programming', 'Programming'),
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('business', 'Business'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255, unique=True)
    description = CKEditor5Field()
    key_points = CKEditor5Field()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    instructor = models.ForeignKey(CustomUser, related_name='courses', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

    def get_key_points(self):
        return [point.strip() for point in self.key_points.split(";") if point.strip()] if self.key_points else []

# Lesson Model
class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = CKEditor5Field()
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    pdf = models.FileField(upload_to='pdfs/', null=True, blank=True)  # <-- Add this line
    audio_transcription = models.TextField(blank=True, null=True)
    audio_file = models.FileField(upload_to="audio/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    duration = models.DurationField(default=timedelta(minutes=0), null=True, blank=True)
    thumbnail_image = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
User = get_user_model()
    
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userprofile')
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    badges = models.JSONField(default=list, blank=True)
    last_active = models.DateField(null=True, blank=True)
    streak = models.IntegerField(default=0)
    rank = models.CharField(max_length=50, default="Beginner")

    def update_streak_and_xp(self):
        today = timezone.now().date()
        if self.last_active == today:
            return  # Already logged today
        elif self.last_active == today - timedelta(days=1):
            self.streak += 1
        else:
            self.streak = 1  # reset streak

        bonus_xp = 10 * self.streak
        self.xp += bonus_xp
        self.last_active = today
        self.save()
        return bonus_xp  # optional return

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Quiz Model
class Quiz(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auto_generate = models.BooleanField(default=False)
    lesson = models.ForeignKey(Lesson, related_name='quizzes', on_delete=models.CASCADE)

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

# Question Model
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    source = models.CharField(max_length=50, choices=[('manual', 'Manual'), ('auto', 'Auto')], default='auto')
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quiz.lesson.title} - {self.question_text}"

# Choice Model
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.option_text

# Enrollment Model
class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(CustomUser, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    progress = models.FloatField(default=0.0)
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    current_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_in_enrollments')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_enrollment')
        ]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title} ({self.status})"

    def update_progress(self):
        total_lessons = self.course.lessons.count()
        completed = self.completed_lessons.count()
        if total_lessons > 0:
            self.progress = (completed / total_lessons) * 100
            if self.progress >= 100:
                self.status = 'completed'
            self.save()
            
class UserProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progress')
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    progress = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, choices=Enrollment.STATUS_CHOICES, default='active')
    last_updated = models.DateTimeField(auto_now=True)

    def update_progress(self):
        total_lessons = self.course.lessons.count()
        completed = self.completed_lessons.count()
        if total_lessons > 0:
            self.progress = (completed / total_lessons) * 100
            if self.progress >= 100:
                self.status = 'completed'
            self.save()

    def __str__(self):
        return f"{self.user.username} - {self.course.title} progress"


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)  # Ensure score is being calculated correctly
    passed = models.BooleanField(default=False)
    attempt_date = models.DateTimeField(auto_now_add=True)
    time_taken = models.DurationField(null=True, blank=True)  # Track the time taken for the quiz attempt
    points_earned = models.IntegerField(default=0)  # For gamification purposes

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'quiz'], name='unique_user_quiz_attempt')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.lesson.title} - Score: {self.score}% - Points: {self.points_earned}"

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievement_icons/')  # Optional for icons
    
    def formatted_name(self):
        return self.name.replace("_", " ").title() 

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.formatted_name()}"