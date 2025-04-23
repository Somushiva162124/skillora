from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Course, Lesson, CustomUser, Quiz, Question  # Import your models
import os
from django.conf import settings

class CourseModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='instructor', password='password123')  # Use CustomUser
        self.course = Course.objects.create(title='Test Course', description='Test Course Description', instructor=self.user)

    def test_course_creation(self):
        course = Course.objects.get(title='Test Course')
        self.assertEqual(course.description, 'Test Course Description')
        self.assertEqual(course.instructor.username, 'instructor')

    def test_course_str_method(self):
        course = Course.objects.get(title='Test Course')
        self.assertEqual(str(course), 'Test Course')

class LessonModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='instructor', password='password123')  # Use CustomUser
        self.course = Course.objects.create(title='Test Course', description='Test Course Description', instructor=self.user)
        self.lesson = Lesson.objects.create(course=self.course, title='Test Lesson', content='Test Lesson Content')

    def test_lesson_creation(self):
        lesson = Lesson.objects.get(title='Test Lesson')
        self.assertEqual(lesson.content, 'Test Lesson Content')
        self.assertEqual(lesson.course.title, 'Test Course')

    def test_lesson_str_method(self):
        lesson = Lesson.objects.get(title='Test Lesson')
        self.assertEqual(str(lesson), 'Test Lesson')

class VideoUploadTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='instructor', password='password123')  # Use CustomUser
        self.client.login(username='instructor', password='password123')

    def test_video_upload_view(self):
        # Prepare a sample video file to upload
        video_file = SimpleUploadedFile("test_video.mp4", b"video content", content_type="video/mp4")
        
        # Make a POST request to upload the video
        response = self.client.post(reverse('process_video'), {'video': video_file})
        
        # Check the response status and content
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Video processed successfully")
        
        # Ensure that the video is saved (adjust the video path check based on your project settings)
        video_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'test_video.mp4')
        self.assertTrue(os.path.exists(video_path))

    def tearDown(self):
        # Remove the video file after the test
        video_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'test_video.mp4')
        if os.path.exists(video_path):
            os.remove(video_path)

class QuizGenerationTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='instructor', password='password123')  # Use CustomUser
        self.course = Course.objects.create(title='Test Course', description='Test Course Description', instructor=self.user)
        self.lesson = Lesson.objects.create(course=self.course, title='Test Lesson', content='Test Lesson Content')
        self.client.login(username='instructor', password='password123')

    def test_quiz_generation_after_video_processing(self):
        # Simulate video upload and processing (use video upload test above as a reference)
        video_file = SimpleUploadedFile("test_video.mp4", b"video content", content_type="video/mp4")
        response = self.client.post(reverse('process_video'), {'video': video_file})

        # Check that the quiz was created for the lesson
        quiz = Quiz.objects.filter(lesson=self.lesson).first()
        self.assertIsNotNone(quiz, "Quiz was not generated after video processing.")

        # Further assertions can be made to check the content of the quiz generated
        questions = Question.objects.filter(quiz=quiz)
        self.assertGreater(questions.count(), 0, "No questions were generated for the quiz.")

class ViewsTest(TestCase):

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/register.html')

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/login.html')

    def test_dashboard_view(self):
        self.client.login(username='instructor', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')
    
    def setUp(self):
        # Create a test user
        self.user = get_user_model().objects.create_user(username='instructor', password='password123')

    def test_logout_view(self):
        self.client.login(username='instructor', password='password123')
        
        # Call the logout view
        response = self.client.get(reverse('logout'))  # Ensure GET method here
        
        # Test for correct redirect after logout
        self.assertRedirects(response, reverse('index'))  # Redirect to the index page
        

