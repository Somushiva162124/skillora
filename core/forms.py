from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Course, Lesson, Enrollment

# Custom User Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Making 'bio' field optional
        self.fields['bio'].required = False

# Course Form
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'key_points', 'instructor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict 'instructor' field to only staff users
        self.fields['instructor'].queryset = CustomUser.objects.filter(is_staff=True)
        if self.fields['instructor'].queryset.exists() == False:
            self.fields['instructor'].empty_label = "No instructors available"

# Lesson Form (single definition)
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'video_url', 'order', 'duration', 'thumbnail_image', 'video_file', 'pdf']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict 'course' field to only courses created by the current instructor (if applicable)
        if hasattr(self, 'user') and self.user.is_staff:
            self.fields['course'].queryset = Course.objects.filter(instructor=self.user)
        else:
            self.fields['course'].queryset = Course.objects.all()

# Enrollment Form
class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the 'course' field to active courses
        self.fields['course'].queryset = Course.objects.filter(status=True)

        if self.instance and self.instance.user:
            # Exclude courses that the user is already enrolled in
            self.fields['course'].queryset = self.fields['course'].queryset.exclude(
                enrollments__user=self.instance.user
            )

# Topic Form (for Quiz generation)
class TopicForm(forms.Form):
    topic = forms.CharField(label='Enter Topic for Quiz', max_length=100)
