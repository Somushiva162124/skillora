import os
import re
import logging
import ffmpeg
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
        # Use FFmpeg to extract audio
        ffmpeg.input(video_path).output(output_audio_path).run()
        return output_audio_path
    except Exception as e:
        logger.error(f"[ERROR] extract_audio failed: {e}")
        return None


def generate_quiz_questions(video_path, num_questions=5):
    """Full pipeline: Extract audio → Transcribe → Generate quiz → Save to DB."""
    audio_path = extract_audio(video_path)
    if not audio_path:
        return []

    # Placeholder for future transcription system (e.g., Whisper)
    raise NotImplementedError("Transcription system not integrated yet.")
    # transcript = transcribe_audio(audio_path)  # future placeholder
    # return generate_quiz_questions(transcript, num_questions)


def process_video(video_path):
    """Extracts audio from video and calculates duration."""
    try:
        # Extract audio
        audio_dir = os.path.join(os.path.dirname(video_path), "audio")
        os.makedirs(audio_dir, exist_ok=True)
        full_audio_path = os.path.join(audio_dir, "temp_audio.wav")
        ffmpeg.input(video_path).output(full_audio_path).run()

        # Get video duration
        probe = ffmpeg.probe(video_path, v='error', select_streams='v:0', show_entries='stream=duration')
        duration = float(probe['streams'][0]['duration'])

        # Return audio path and duration
        relative_audio_path = os.path.relpath(full_audio_path, settings.MEDIA_ROOT)
        return {
            "audio_path": relative_audio_path.replace("\\", "/"),
            "duration": duration
        }
    except Exception as e:
        logger.error(f"[ERROR] process_video failed: {e}")
        return None

def resize_video(input_video, output_video, width=1280, height=720):
    """Resize a video to the specified dimensions."""
    try:
        ffmpeg.input(input_video).output(output_video, vf=f'scale={width}:{height}').run()
    except Exception as e:
        logger.error(f"[ERROR] resize_video failed: {e}")


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

def transcribe_audio_with_huggingface(binary_audio_data):
    """Uses Hugging Face API to transcribe audio data (WAV)."""
    import requests

    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        logger.error("[ERROR] HUGGINGFACE_API_TOKEN not found in environment.")
        return {"error": "Token missing"}

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/wav2vec2-base-960h",
            headers=headers,
            data=binary_audio_data
        )
        return response.json()
    except Exception as e:
        logger.error(f"[ERROR] Hugging Face API call failed: {e}")
        return {"error": str(e)}

