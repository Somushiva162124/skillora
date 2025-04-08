from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # Homepage & Dashboard
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Authentication (Login, Logout, Registration)
    path('login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path("dashboard/", login_required(views.dashboard), name="dashboard"),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('gamification/', views.gamification_view, name='gamification'),
    path('course/<int:course_id>/enroll/', views.enroll, name='enroll'),
    path('course/<int:course_id>/enrollment-status/', views.check_enrollment_status, name='check_enrollment_status'),

    # Lessons
    path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path("process-video/", views.process_uploaded_video, name="process_video"),
    path('course/<int:course_id>/lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_complete'),
    path('lessons/create/', views.create_lesson, name='create_lesson'),
    # in urls.py
    path('lesson/<int:lesson_id>/pdf/', views.view_pdf, name='view_pdf'),


    # Quizzes
    path('quizzes/list/', views.quiz_list, name='quiz_list'),  # List of all quizzes (no ID needed)
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/', views.quiz_view, name='quiz_view'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/', views.quiz_view, name='quiz_page'),
    path('quiz/result/<int:score>/<int:total>/<int:course_id>/<int:lesson_id>/', views.quiz_result, name='quiz_result'),
    path('quiz/<int:quiz_id>/', views.quiz_display, name='quiz_page'),

    # Bulk Quiz Generation
    path('generate_quizzes/', views.generate_quizzes_for_all_lessons, name='generate_quizzes'),
]
