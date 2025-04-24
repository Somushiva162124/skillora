import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from django.core.management.base import BaseCommand
from core.models import Lesson, Quiz, Question, Choice
import yt_dlp
import os
import warnings
from difflib import SequenceMatcher

warnings.filterwarnings("ignore", category=UserWarning)


class Command(BaseCommand):
    help = "Generate quizzes for lessons using AI"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Loading models...")
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
        model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")
        self.stdout.write(self.style.SUCCESS("✅ Models loaded successfully!"))

        lessons = Lesson.objects.all()
        for lesson in lessons:
            self.stdout.write(f"\n📚 Generating quiz for: {lesson.title}")
            text = ""

            quiz, created = Quiz.objects.get_or_create(lesson=lesson)

            # Step 1: Extract text from video
            if lesson.video_url:
                self.stdout.write("🎥 Extracting text from video...")
                video_text, video_duration = self.extract_text_from_video(lesson.video_url)
                text += video_text

            # Step 2: Preprocess and clean text
            text = self.clean_text(text)

            if not text.strip():
                self.stdout.write(self.style.WARNING(f"⚠ No valid content for {lesson.title}. Skipping..."))
                continue

            # Step 3: Generate questions based on video length
            num_questions = self.calculate_question_count(video_duration)
            self.stdout.write(f"🔢 Generating {num_questions} questions...")

            text_chunks = self.split_text(text)
            questions = []
            for chunk in text_chunks:
                questions += self.generate_questions(chunk, model, tokenizer, num_questions)

            # Step 4: Add unique questions to the quiz
            for question_text in questions:
                existing_questions = Question.objects.filter(quiz=quiz).values_list("question_text", flat=True)
                if not any(self.is_similar(question_text, q) for q in existing_questions):
                    question = Question.objects.create(quiz=quiz, question_text=question_text)
                    Choice.objects.create(question=question, option_text="Correct Answer", is_correct=True)
                    Choice.objects.create(question=question, option_text="Wrong Answer 1", is_correct=False)
                    Choice.objects.create(question=question, option_text="Wrong Answer 2", is_correct=False)
                    Choice.objects.create(question=question, option_text="Wrong Answer 3", is_correct=False)

            self.stdout.write(self.style.SUCCESS(f"✅ Quiz updated for: {lesson.title}"))

    def extract_text_from_video(self, video_url):
        """Download video and extract text from it"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_video.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_path = info['requested_downloads'][0]['filepath']
            video_duration = info.get("duration", 0)  # Video length in seconds

        # For now, we're assuming text extraction is manually done
        text = self.simulate_video_text_extraction(video_path)
        os.remove(video_path)  # Cleanup
        return text, video_duration

    def simulate_video_text_extraction(self, video_path):
        """Simulate video text extraction"""
        # This should be replaced with a method that extracts video subtitles or transcribes audio
        return "This is a sample transcription of the video content."

    def calculate_question_count(self, duration):
        """Dynamically determine the number of questions based on video length"""
        if duration < 300:  # Less than 5 minutes
            return 3
        elif duration < 900:  # 5 to 15 minutes
            return 5
        else:  # More than 15 minutes
            return 7

    def generate_questions(self, text, model, tokenizer, num_questions):
        """Generate quiz questions from text"""
        input_text = f"Generate {num_questions} quiz questions: {text}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model.generate(inputs['input_ids'], max_length=64, num_beams=5, num_return_sequences=num_questions, early_stopping=True)
        return [tokenizer.decode(output, skip_special_tokens=True).strip() for output in outputs]

    def clean_text(self, text):
        """Remove repetitive phrases or filler words."""
        unwanted_phrases = ["Welcome back, aliens.", "My name is Naveen Reddy.", "Let's start with Python."]
        for phrase in unwanted_phrases:
            text = text.replace(phrase, "")
        return text.strip()

    def split_text(self, text, max_length=400):
        """Split long text into smaller parts for better question generation."""
        words = text.split()
        return [" ".join(words[i:i + max_length]) for i in range(0, len(words), max_length)]

    def is_similar(self, q1, q2, threshold=0.8):
        """Check if two questions are too similar."""
        return SequenceMatcher(None, q1, q2).ratio() > threshold
