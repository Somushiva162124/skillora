import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import whisper
from django.core.management.base import BaseCommand
from core.models import Lesson, Quiz, Question, Choice
import yt_dlp
import os
import warnings
import ffmpeg
from difflib import SequenceMatcher

warnings.filterwarnings("ignore", category=UserWarning)


class Command(BaseCommand):
    help = "Generate quizzes for lessons using AI"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Loading models...")
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
        model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")
        whisper_model = whisper.load_model("small", device="cpu")
        self.stdout.write(self.style.SUCCESS("✅ Models loaded successfully!"))

        lessons = Lesson.objects.all()
        for lesson in lessons:
            self.stdout.write(f"\n📚 Generating quiz for: {lesson.title}")
            text = ""

            quiz, created = Quiz.objects.get_or_create(lesson=lesson)

            # Step 1: Extract text from video/audio
            if lesson.video_url:
                self.stdout.write("🎥 Extracting text from video...")
                video_text, has_audio, video_duration = self.extract_text_from_video(lesson.video_url, whisper_model)
                text += video_text

                if has_audio:
                    self.stdout.write("🎙 Extracting additional text from audio...")
                    extracted_audio_text = self.extract_text_from_audio("temp_audio.wav", whisper_model)
                    text += " " + extracted_audio_text

                    # ✅ Save extracted audio transcription in the database
                    lesson.audio_transcription = extracted_audio_text
                    lesson.save()
                    self.stdout.write(self.style.SUCCESS("✅ Audio transcription saved!"))

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

            source = "video and audio" if lesson.video_url and has_audio else "video" if lesson.video_url else "audio"
            self.stdout.write(self.style.SUCCESS(f"✅ Quiz updated for: {lesson.title} (Source: {source})"))

    def extract_text_from_video(self, video_url, model):
        """Download video, extract audio, and transcribe text"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_video.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_path = info['requested_downloads'][0]['filepath']
            video_duration = info.get("duration", 0)  # Video length in seconds

        has_audio = self.check_audio_stream(video_path)
        if has_audio:
            self.stdout.write(self.style.SUCCESS("✅ Audio detected in video! Extracting..."))
            self.extract_audio(video_path, "temp_audio.wav")
            text = model.transcribe("temp_audio.wav")["text"]
        else:
            self.stdout.write(self.style.WARNING(f"⚠ No audio found in {video_url}. Skipping..."))
            text = ""

        os.remove(video_path)  # Cleanup
        return text, has_audio, video_duration

    def extract_audio(self, video_path, audio_path):
        """Extract audio from video using FFmpeg"""
        try:
            ffmpeg.input(video_path).output(audio_path, format='wav', acodec='pcm_s16le', ar='16000').run(overwrite_output=True, quiet=True)
        except ffmpeg.Error as e:
            self.stdout.write(self.style.ERROR(f"❌ FFmpeg error: {e}"))

    def extract_text_from_audio(self, audio_path, model):
        """Extract text from an audio file"""
        if not os.path.exists(audio_path):
            self.stdout.write(self.style.ERROR(f"❌ Audio file {audio_path} not found!"))
            return ""

        self.stdout.write(f"🔍 Processing audio file: {audio_path}")
        return model.transcribe(audio_path)["text"]

    def check_audio_stream(self, file_path):
        """Check if video contains an audio stream"""
        try:
            probe = ffmpeg.probe(file_path)
            audio_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]
            return len(audio_streams) > 0  # True if audio exists
        except ffmpeg.Error as e:
            self.stdout.write(self.style.ERROR(f"❌ FFmpeg error: {e}"))
            return False

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
