from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import CustomUser, Course, Lesson, Enrollment, Quiz, Question, Choice
from .models import Achievement, UserAchievement
from .models import Lesson

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'bio')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {'fields': ('bio',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {'fields': ('bio',)}),
    )

# Course Admin
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'created_at')
    search_fields = ('title', 'category', 'instructor__username')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)
    raw_id_fields = ('instructor',)

# Lesson Admin Form (with CKEditor)
class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'
        widgets = {
            'content': CKEditor5Widget(config_name='default'),
        }

# Lesson Admin
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ('title', 'course', 'order', 'created_at', 'video_url',)
    fields = ('title', 'content', 'video_url','pdf')  # PDF is missing here
    search_fields = ('title', 'course__title', 'description')
    list_filter = ('course',)
    ordering = ('course', 'order')
    raw_id_fields = ('course',)

# Enrollment Admin
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'enrolled_at', 'progress')
    search_fields = ('user__username', 'course__title')
    list_filter = ('status', 'enrolled_at')
    ordering = ('-enrolled_at',)
    raw_id_fields = ('user', 'course')

# Inline Choice Admin for Question Admin
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3  # Show 3 empty choices by default

# Inline Question Admin for Quiz Admin
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 2  # Show 2 empty questions by default

# Quiz Admin
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'created_at')
    search_fields = ('title', 'lesson__title')
    list_filter = ('lesson', 'created_at')
    inlines = [QuestionInline]  # Show questions inline for quizzes
    raw_id_fields = ('lesson',)

# Question Admin
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text', 'order')
    search_fields = ('question_text', 'quiz__title')
    list_filter = ('quiz',)
    ordering = ('quiz', 'order')
    raw_id_fields = ('quiz',)
    inlines = [ChoiceInline]  # Show choices inline for questions

# Choice Admin
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_text', 'is_correct', 'order')
    search_fields = ('option_text', 'question__question_text')
    list_filter = ('is_correct',)
    ordering = ('question', 'order')
    raw_id_fields = ('question',)

# Register models with customized admins
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
