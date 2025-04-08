from moviepy.editor import VideoFileClip
from transformers import T5ForConditionalGeneration, T5Tokenizer
from pydub import AudioSegment
from .models import Question, Quiz, Choice
import re
from django.contrib import messages

# Load pre-trained T5 model and tokenizer for question generation
model_name = "t5-small"
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)

def convert_youtube_url(url):
    """Extracts video ID from a YouTube URL and returns an embeddable link."""
    
    # Regex pattern to extract video ID
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    
    match = re.search(pattern, url)
    
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"  # Embeddable URL format
    
    return None  # Invalid YouTube URL

def extract_audio(video_path, output_audio_path="temp_audio.wav"):
    """Extracts audio from a video and converts it to WAV format."""
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_audio_path)
    
    # Convert to WAV if not in the correct format
    audio = AudioSegment.from_file(output_audio_path)
    audio.export(output_audio_path, format="wav")
    
    print(f"Audio extracted: {output_audio_path}")
    return output_audio_path

def generate_quiz_questions(lesson_content, num_questions=5):
    """Generates quiz questions using the T5 model."""
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
            choice_data = {
                "text": choice.text,
                "is_correct": choice.is_correct
            }
            question_data["choices"].append(choice_data)
        
        parsed_data["questions"].append(question_data)
    
    return parsed_data

def save_quiz_to_db(lesson, questions_data):
    """Saves generated quiz questions to the database."""
    quiz = Quiz.objects.create(lesson=lesson, title=f"Quiz for {lesson.title}")
    for question_data in questions_data:
        question = Question.objects.create(quiz=quiz, text=question_data["text"])
        for choice_data in question_data["choices"]:
            Choice.objects.create(question=question, text=choice_data["text"], is_correct=choice_data["is_correct"])
    print("Quiz saved to DB.")

def generate_quiz_from_video(video_path, num_questions=5):
    """Full pipeline: Extract audio → Transcribe → Generate quiz → Save to DB."""
    audio_path = extract_audio(video_path)
    transcript = ""  # Placeholder, since Whisper has been removed
    questions = generate_quiz_questions(transcript, num_questions)
    return questions

from django.contrib import messages

from .models import UserProfile  # if needed for checks

def award_achievements(user_profile, source="", extra_xp=0, request=None):
    awarded = []

    # Add XP if provided
    if extra_xp:
        user_profile.xp += extra_xp

    # ✅ XP Milestones
    milestones = [100, 200, 300, 500, 1000]
    for milestone in milestones:
        badge = f"xp_{milestone}"
        if user_profile.xp >= milestone and badge not in user_profile.badges:
            user_profile.badges.append(badge)
            awarded.append(f"🎯 XP Milestone Unlocked: {milestone} XP!")

    # ✅ Source-based Badges
    if source == "lesson" and "first_lesson_completed" not in user_profile.badges:
        user_profile.badges.append("first_lesson_completed")
        awarded.append("🏆 Achievement: First Lesson Completed!")

    if source == "quiz" and "first_quiz_passed" not in user_profile.badges:
        user_profile.badges.append("first_quiz_passed")
        awarded.append("🏅 Achievement: First Quiz Passed!")

    # ✅ Rank Update
    new_rank = get_rank(user_profile.xp)
    if user_profile.rank != new_rank:
        user_profile.rank = new_rank
        awarded.append(f"🚀 Rank Upgraded to: {new_rank}!")

    user_profile.save()

    # ✅ Show messages if request available
    if request is not None:
        for note in awarded:
            messages.success(request, note)
        if extra_xp:
            messages.success(request, f"✅ You earned {extra_xp} XP!")

    return awarded

def get_rank(xp):
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
