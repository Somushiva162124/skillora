import os
import re
import logging
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from django.conf import settings
from django.contrib import messages
from transformers import T5ForConditionalGeneration, T5Tokenizer
from .models import Question, Quiz, Choice, UserProfile

# Logger setup
logger = logging.getLogger(__name__)

# Load pre-trained T5 model and tokenizer
model_name = "t5-small"
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)


def convert_youtube_url(url):
    """Extracts video ID from a YouTube URL and returns an embeddable link."""
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    return None


def extract_audio(video_path, output_audio_path="temp_audio.wav"):
    """Extracts audio from a video and converts it to WAV format."""
    try:
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(output_audio_path)
        audio = AudioSegment.from_file(output_audio_path)
        audio.export(output_audio_path, format="wav")
        return output_audio_path
    except Exception as e:
        logger.error(f"[ERROR] extract_audio failed: {e}")
        return None


def generate_quiz_questions(lesson_content, num_questions=5):
    """Generates quiz questions using the T5 model."""
    try:
        input_text = "Generate questions from this text: " + lesson_content
        inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
        outputs = model.generate(inputs['input_ids'], max_length=200, num_beams=4, num_return_sequences=num_questions, early_stopping=True)
        questions = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        structured_questions = []
        for question in questions:
            structured_questions.append({
                "text": question,
                "choices": [
                    {"text": "Correct Answer", "is_correct": True},
                    {"text": "Incorrect Option 1", "is_correct": False},
                    {"text": "Incorrect Option 2", "is_correct": False},
                    {"text": "Incorrect Option 3", "is_correct": False}
                ]
            })
        return structured_questions
    except Exception as e:
        logger.error(f"[ERROR] generate_quiz_questions failed: {e}")
        return []


def process_video(video_path):
    """Extracts audio from video and calculates duration."""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        audio_dir = os.path.join(os.path.dirname(video_path), "audio")
        os.makedirs(audio_dir, exist_ok=True)
        full_audio_path = os.path.join(audio_dir, "temp_audio.wav")
        clip.audio.write_audiofile(full_audio_path)
        relative_audio_path = os.path.relpath(full_audio_path, settings.MEDIA_ROOT)
        return {
            "audio_path": relative_audio_path.replace("\\", "/"),
            "duration": duration
        }
    except Exception as e:
        logger.error(f"[ERROR] process_video failed: {e}")
        return None


def parse_quiz(quiz):
    """Parses quiz object into a structured dictionary format."""
    parsed_data = {
        "quiz_title": quiz.title,
        "questions": []
    }
    for question in quiz.questions.all():
        question_data = {
            "question_text": question.text,
            "choices": []
        }
        for choice in question.choices.all():
            question_data["choices"].append({
                "text": choice.text,
                "is_correct": choice.is_correct
            })
        parsed_data["questions"].append(question_data)
    return parsed_data


def save_quiz_to_db(lesson, questions_data):
    """Saves generated quiz questions to the database."""
    try:
        quiz = Quiz.objects.create(lesson=lesson, title=f"Quiz for {lesson.title}")
        for question_data in questions_data:
            question = Question.objects.create(quiz=quiz, text=question_data["text"])
            for choice_data in question_data["choices"]:
                Choice.objects.create(question=question, text=choice_data["text"], is_correct=choice_data["is_correct"])
    except Exception as e:
        logger.error(f"[ERROR] save_quiz_to_db failed: {e}")


def generate_quiz_from_video(video_path, num_questions=5):
    """Full pipeline: Extract audio → Transcribe → Generate quiz → Save to DB."""
    audio_path = extract_audio(video_path)
    if not audio_path:
        return []

    # Replace this placeholder when Whisper or transcription model is integrated
    raise NotImplementedError("Transcription system not integrated yet.")
    # transcript = transcribe_audio(audio_path)  # future placeholder
    # return generate_quiz_questions(transcript, num_questions)


def award_achievements(user_profile, source="", extra_xp=0, request=None):
    """Awards achievements and XP to users."""
    awarded = []

    # Add XP if provided
    if extra_xp:
        user_profile.xp += extra_xp

    # XP Milestones
    milestones = [100, 200, 300, 500, 1000]
    for milestone in milestones:
        badge = f"xp_{milestone}"
        if user_profile.xp >= milestone and badge not in user_profile.badges:
            user_profile.badges.append(badge)
            awarded.append(f"🎯 XP Milestone Unlocked: {milestone} XP!")

    # Source-based Achievements
    if source == "lesson" and "first_lesson_completed" not in user_profile.badges:
        user_profile.badges.append("first_lesson_completed")
        awarded.append("🏆 Achievement: First Lesson Completed!")

    if source == "quiz" and "first_quiz_passed" not in user_profile.badges:
        user_profile.badges.append("first_quiz_passed")
        awarded.append("🏅 Achievement: First Quiz Passed!")

    # Rank Updates
    new_rank = get_rank(user_profile.xp)
    if user_profile.rank != new_rank:
        user_profile.rank = new_rank
        awarded.append(f"🚀 Rank Upgraded to: {new_rank}!")

    user_profile.save()

    # Display messages
    if request:
        for note in awarded:
            messages.success(request, note)
        if extra_xp:
            messages.success(request, f"✅ You earned {extra_xp} XP!")

    return awarded


def get_rank(xp):
    """Returns rank name based on XP level."""
    if xp >= 1000:
        return "Legend"
    elif xp >= 750:
        return "Master"
    elif xp >= 500:
        return "Pro"
    elif xp >= 250:
        return "Intermediate"
    elif xp >= 100:
        return "Novice"
    return "Beginner"
