from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import re
from .models import Enrollment, Course, Lesson, Quiz, Question, UserQuizAttempt, UserProfile  # Removed UserProgress
from .forms import CustomUserCreationForm, TopicForm
from .utils import convert_youtube_url, generate_quiz_questions, parse_quiz, save_quiz_to_db
from .video_utils import process_video
from transformers import T5ForConditionalGeneration, T5Tokenizer
from django.utils.timezone import now
from .models import Choice
from .utils import award_achievements
from datetime import datetime
from .forms import LessonForm

model_name = "t5-small"  # You can use "t5-base" or "t5-large" for better performance, but requires more resources
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)  # Updated

# Home Page
def index(request):
    """Homepage view."""
    courses = Course.objects.all()
    return render(request, 'core/index.html', {'courses': courses})

def convert_youtube_url(video_url):
    """Converts YouTube URLs into embed format. Leaves other URLs unchanged."""
    if not video_url:
        return None

    # YouTube Patterns
    patterns = [
        r"watch\?v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"embed/([a-zA-Z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

    # Not YouTube? Return as-is
    return video_url


# Video Upload and Processing
def process_uploaded_video(request):
    """Handles video processing."""
    if request.method == "POST" and request.FILES.get("video"):
        video_file = request.FILES["video"]
        video_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(video_dir, exist_ok=True)
        file_path = os.path.join(video_dir, video_file.name)
        file_name = default_storage.save(file_path, ContentFile(video_file.read()))
        output_video = process_video(os.path.join(settings.MEDIA_ROOT, file_name))

        if output_video:
            return JsonResponse({"message": "Video processed successfully", "output": output_video})
        else:
            return JsonResponse({"error": "Video processing failed"}, status=500)

    return JsonResponse({"error": "No video uploaded"}, status=400)

from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    registration_successful = request.GET.get('registration_successful', False)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, "Invalid username or password.")
        else:
            form.add_error(None, "Invalid username or password.")  # fallback error
    else:
        form = AuthenticationForm()

    return render(
        request,
        'core/login.html',
        {
            'form': form,
            'registration_successful': registration_successful,
        }
    )

def register(request):
    if request.method == "POST":
        # Use CustomUserCreationForm for handling registration
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            # Save the new user
            user = form.save()
            login(request, user)  # Automatically log the user in after registration
            messages.success(request, "Registration successful!")
            return redirect("login")  # Redirect to the dashboard after registration
        
        else:
            # If form is not valid, return with errors
            messages.error(request, "There were errors in your form.")
    
    else:
        form = CustomUserCreationForm()

    return render(request, "core/register.html", {"form": form})

def profile(request):
    # Get the logged-in user
    user = request.user
    # Fetch the courses the user is enrolled in
    enrollments = Enrollment.objects.filter(user=user)
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    return render(request, 'core/profile.html', {
        'user': user,
        'enrolled_courses': enrolled_courses,
    })

@login_required
def dashboard(request):
    """User's Dashboard"""
    courses = Course.objects.all()
    enrollments = Enrollment.objects.filter(user=request.user)
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    return render(request, 'core/dashboard.html', {
        'courses': courses,
        'enrollments': enrollments,
        'enrolled_courses': enrolled_courses,
    })

def course_list(request):
    """Displays all courses"""
    courses = Course.objects.all()
    return render(request, 'core/course_list.html', {'courses': courses})

@login_required
def course_detail(request, course_id):
    """Displays Course Details"""
    course = get_object_or_404(Course, id=course_id)
    lessons = Lesson.objects.filter(course=course).order_by('order')
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'status': 'active'}
    )
    completed_lessons = enrollment.completed_lessons.values_list('id', flat=True)
    progress_percentage = (completed_lessons.count() / lessons.count()) * 100 if lessons.count() > 0 else 0
    return render(request, 'core/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'is_enrolled': True,  # Since we use get_or_create, user is enrolled
        'completed_lessons': completed_lessons,
        'progress_percentage': progress_percentage
    })

@login_required
def enroll(request, course_id):
    """Handles Course Enrollment"""
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'status': 'active'}
    )
    if created:
        messages.success(request, f'You have successfully enrolled in {course.title}.')
    return redirect('course_detail', course_id=course.id)

def check_enrollment_status(request, course_id):
    """Checks if the user is enrolled in a course."""
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course_id=course_id).exists()
        return JsonResponse({"is_enrolled": is_enrolled})
    return JsonResponse({"error": "User not authenticated"}, status=401)

@login_required
def lesson_detail(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)

    # Sanitize content
    def remove_external_links(html):
        return re.sub(r'<a\s+(?:[^>]*?\s+)?href="https?://[^"]+"[^>]*>.*?</a>', '🔗 External Link Disabled', html)

    clean_content = remove_external_links(lesson.content)
    formatted_content = mark_safe(clean_content)

    # Convert video URL
    converted_video_url = convert_youtube_url(lesson.video_url)

    quiz = Quiz.objects.filter(lesson=lesson).first()

    return render(request, 'core/lesson_detail.html', {
        'lesson': lesson,
        'converted_video_url': converted_video_url,
        'formatted_content': formatted_content,
        'quiz': quiz,
        'course_id': course_id,
    })



@login_required
def mark_lesson_complete(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)
    enrollment, _ = Enrollment.objects.get_or_create(
        user=request.user,
        course=lesson.course,
        defaults={'status': 'active'}
    )

    if lesson not in enrollment.completed_lessons.all():
        enrollment.completed_lessons.add(lesson)
        enrollment.update_progress()

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += 10
        award_achievements(profile, source="lesson", extra_xp=10)

        messages.success(request, f'You have successfully completed the lesson "{lesson.title}".')

    return redirect('course_detail', course_id=course_id)

def quizzes(request):
    return render(request, 'core/quiz_page.html')  # Use an appropriate template

def quiz_list(request):
    # Get all the lessons
    lessons = Lesson.objects.all()  # Fetch lessons, not quizzes
    return render(request, 'core/quiz_list.html', {'lessons': lessons})

def quiz_display(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    quizzes = Quiz.objects.filter(lesson=lesson)

    questions = []
    for quiz in quizzes:
        quiz_questions = Question.objects.filter(quiz=quiz)
        for question in quiz_questions:
            choices = question.choices.all() 
            questions.append({
                "question": question.question_text,  # Using the correct field name
                "options": choices# No options since your model doesn't have them
            })

    return render(request, 'quiz_display.html', {'lesson': lesson, 'questions': questions})

@login_required
def quiz_view(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)
    quiz, created = Quiz.objects.get_or_create(lesson=lesson)

    if created:
        lesson_text = lesson.content.strip() if lesson.content else None
        if not lesson_text:
            return JsonResponse({"error": "No lesson content available for quiz generation"}, status=400)

        input_text = (
            "Generate a multiple-choice question (MCQ) from the following text. "
            "Provide a clear question followed by four answer choices. "
            "Mark the correct answer using '(Correct)'.\n\n"
            "Lesson Content: " + lesson_text[:500]
        )

        inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
        outputs = model.generate(inputs['input_ids'], max_length=300, num_beams=5, num_return_sequences=3, early_stopping=True)
        generated_questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

        if not generated_questions:
            return JsonResponse({"error": "Quiz generation failed"}, status=500)

        for question_text in generated_questions:
            lines = question_text.split("\n")
            if len(lines) < 5:
                continue
            question = Question.objects.create(quiz=quiz, question_text=lines[0])
            for option in lines[1:]:
                is_correct = "(Correct)" in option
                option_text = option.replace("(Correct)", "").strip()
                Choice.objects.create(question=question, option_text=option_text, is_correct=is_correct)

        messages.success(request, "Quiz created successfully!")

    questions = Question.objects.filter(quiz=quiz).prefetch_related('choices')
    if not questions.exists():
        return JsonResponse({"error": "No questions available"}, status=400)

    attempt, _ = UserQuizAttempt.objects.get_or_create(user=request.user, quiz=quiz)

    if request.method == 'POST':
        correct_answers = 0
        for q in questions:
            selected_answer = request.POST.get(f'question_{q.id}')
            correct_option = q.choices.filter(is_correct=True).first()
            if selected_answer and correct_option and str(selected_answer) == str(correct_option.id):
                correct_answers += 1

        total = questions.count()
        score = correct_answers
        percentage = (score / total) * 100
        passed = percentage >= 50
        points_earned = score

        if score > 0:
            # XP update and achievements
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            user_profile.xp += score * 20  # XP boost
            messages.success(request, f"✅ You earned {score * 20} XP!")
            award_achievements(user_profile, source="quiz", extra_xp=score * 20)

            # First Quiz Passed Badge
            if passed and "first_quiz_passed" not in user_profile.badges:
                user_profile.badges.append("first_quiz_passed")
                messages.success(request, '🏅 Achievement Unlocked: First Quiz Passed!')

            # XP Milestone Badge
            milestone_levels = [100, 200, 300, 500, 1000]
            for milestone in milestone_levels:
                badge_name = f"xp_{milestone}"
                if user_profile.xp >= milestone and badge_name not in user_profile.badges:
                    user_profile.badges.append(badge_name)
                    messages.success(request, f'🎯 Achievement Unlocked: {milestone} XP Reached!')

            user_profile.save()
        else:
            messages.warning(request, "😕 You didn't earn any XP. Try again to unlock achievements!")

        # Update quiz attempt
        attempt.score = percentage
        attempt.passed = passed
        attempt.points_earned = points_earned
        attempt.save()

        # Mark lesson complete if passed
        if passed:
            enrollment, _ = Enrollment.objects.get_or_create(
                user=request.user,
                course=lesson.course,
                defaults={'status': 'active'}
            )
            if lesson not in enrollment.completed_lessons.all():
                enrollment.completed_lessons.add(lesson)
                enrollment.update_progress()

        return redirect('quiz_result', score=score, total=total, course_id=course_id, lesson_id=lesson_id)

    return render(request, 'core/quiz_page.html', {
        'quiz': quiz,
        'questions': questions,
        'lesson': lesson,
        'course_id': course_id,
        'lesson_id': lesson_id,
    })


def quiz_result(request, score, total, course_id, lesson_id):
    percentage = round((score / total) * 100)

    if percentage >= 80:
        feedback = "Excellent work! 🎉"
    elif percentage >= 50:
        feedback = "Good job, but keep practicing!"
    else:
        feedback = "Don’t give up! Try again 💪"

    context = {
        'score': score,
        'total': total,
        'percentage': percentage,
        'feedback': feedback,
        'course_id': course_id,
        'lesson_id': lesson_id
    }

    return render(request, 'core/quiz_result.html', context)


def generate_quizzes_for_all_lessons(request):
    """Generates quizzes for all lessons and saves them to the database."""
    lessons = Lesson.objects.all()
    if not lessons:
        return JsonResponse({"message": "No lessons found."}, status=404)

    for lesson in lessons:
        questions_data = generate_quiz_questions(lesson.content, num_questions=5)
        save_quiz_to_db(lesson, questions_data)

    return JsonResponse({"message": "Quizzes generated successfully."})

def quiz_page(request):
    quizzes = Quiz.objects.prefetch_related("questions__choices").all()
    return render(request, "quiz_page.html", {"quizzes": quizzes})
   
def profile(request):
    user = request.user
    enrolled_courses = Course.objects.filter(enrollments__user=user)  # Assuming Enrollment model

    return render(request, 'core/profile.html', {'user': user, 'enrolled_courses': enrolled_courses})

@login_required
def gamification_view(request):
    profile = request.user.userprofile
    
    # ✅ Optional: Update streak & XP if user is active today
    profile.update_streak_and_xp()
    
    # XP, Level & Progress
    xp = profile.xp
    level = profile.level
    progress = (xp % 100)  # assuming 100 XP per level

    context = {
        'xp': xp,
        'level': level,
        'progress': progress,
        'badges': profile.badges,
        'streak': profile.streak,
        'rank': profile.rank,
    }
    return render(request, 'core/gamification.html', context)

def create_lesson(request):
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lesson_list')  # or wherever you want
    else:
        form = LessonForm()
    return render(request, 'core/create_lesson.html', {'form': form})

def view_pdf(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'core/view_pdf.html', {'lesson': lesson})


@login_required
def logout_view(request):
    """Logs Out User"""
    logout(request)
    return redirect('index')


