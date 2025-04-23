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
        # Optional: Making 'bio' field optional if needed
        self.fields['bio'].required = False

# Course Form
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'key_points', 'instructor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit 'instructor' field choices to only users with staff/admin privileges
        self.fields['instructor'].queryset = CustomUser.objects.filter(is_staff=True)
        if not self.fields['instructor'].queryset.exists():
            # Optionally, display a message if no staff are available
            self.fields['instructor'].empty_label = "No instructors available"

# Lesson Form
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'video_url', 'order', 'duration', 'thumbnail_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the 'course' field is filled based on the current course being created/updated
        self.fields['course'].queryset = Course.objects.all()

        # Optionally, filter by instructor (if required)
        if self.instance and self.instance.course:
            self.fields['course'].queryset = Course.objects.filter(instructor=self.instance.course.instructor)

# Enrollment Form
class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['course']  # User is auto-set in the view
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),  # Improved styling for the select widget
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure the user can only enroll in available courses (e.g., 'active' courses)
        self.fields['course'].queryset = Course.objects.filter(status='active')

        # Optional: Limit enrollment to active courses and courses where the user is not already enrolled
        self.fields['course'].queryset = self.fields['course'].queryset.exclude(
            enrollments__user=self.instance.user
        )

# New Topic Form for Quiz Generation (If needed for quiz purposes)
class TopicForm(forms.Form):
    topic = forms.CharField(label='Enter Topic for Quiz', max_length=100)

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'video_url', 'video_file', 'duration', 'pdf']
