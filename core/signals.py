from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lesson, Quiz, Question, Choice, UserProfile
from django.core.files.base import ContentFile
from io import BytesIO
from xhtml2pdf import pisa
from django.contrib.auth import get_user_model
import logging
import re
import os
import uuid
import subprocess
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
import torchaudio
import torch
from pydub import AudioSegment

User = get_user_model()
logger = logging.getLogger(__name__)

def clean_html(raw_html):
    clean_text = re.sub(r'<.*?>', '', raw_html)
    clean_text = re.sub(r'&[a-z]+;', ' ', clean_text)
    return clean_text.strip()

@receiver(post_save, sender=Lesson)
def process_lesson(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"Started processing lesson: {instance.title}")

    # ----------- VIDEO / AUDIO EXTRACTION ------------ 
    try:
        video_path = ""
        if instance.video_file:
            video_path = instance.video_file.path
        elif instance.video_url:
            from pytube import YouTube
            yt = YouTube(instance.video_url)
            filename = f"{uuid.uuid4()}.mp4"
            video_path = yt.streams.filter(only_video=True).first().download(output_path="media/videos", filename=filename)

        if video_path:
            os.makedirs("media/audio", exist_ok=True)
            audio_filename = f"{uuid.uuid4()}.aac"
            audio_output = os.path.join("media/audio", audio_filename)

            subprocess.run(['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'aac', audio_output], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            instance.audio_file.name = os.path.relpath(audio_output, 'media')
            instance.save(update_fields=['audio_file'])
            logger.info(f"Audio extracted and saved for lesson: {instance.title}")
    except Exception as e:
        logger.error(f"Audio extraction failed for lesson: {instance.title}. Error: {e}")

    # ----------- TRANSCRIPTION USING Wav2Vec2 (FREE Transformers Model) ----------- 
    try:
        # Convert audio to WAV format (16kHz mono, required for Wav2Vec2)
        audio_path = instance.audio_file.path
        wav_path = audio_path.replace(".aac", ".wav")
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")

        # Load model + tokenizer
        tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
        model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

        # Load audio
        speech_array, sampling_rate = torchaudio.load(wav_path)

        # Tokenize and predict
        input_values = tokenizer(speech_array[0], return_tensors="pt", padding="longest").input_values
        with torch.no_grad():
            logits = model(input_values).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription_text = tokenizer.batch_decode(predicted_ids)[0]

        instance.audio_transcription = transcription_text
        instance.transcript = transcription_text
        instance.save(update_fields=["audio_transcription", "transcript"])

        logger.info(f"✅ Free transcription (Wav2Vec2) done for: {instance.title}")
    except Exception as e:
        logger.error(f"Transcription failed for {instance.title}: {str(e)}")

    # ----------- QUIZ GENERATION ------------ 
    cleaned_content = clean_html(instance.content)
    if len(cleaned_content.split()) < 10:
        logger.warning(f"Lesson '{instance.title}' has too little content. Skipping quiz and PDF generation.")
        return

    try:
        tokenizer = T5Tokenizer.from_pretrained("t5-small", legacy=False)
        model = T5ForConditionalGeneration.from_pretrained("t5-small")

        input_text = f"generate question: {cleaned_content}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(inputs['input_ids'], max_length=64, num_beams=5, num_return_sequences=3, early_stopping=True)

        questions = [tokenizer.decode(output, skip_special_tokens=True).strip() for output in outputs]
        valid_questions = [q for q in questions if len(q) > 10]

        if valid_questions:
            quiz = Quiz.objects.create(lesson=instance, title=f"Quiz for {instance.title}")
            for question_text in valid_questions:
                question = Question.objects.create(quiz=quiz, text=question_text)
                Choice.objects.create(question=question, text="Correct Answer", is_correct=True)
                Choice.objects.create(question=question, text="Wrong Answer 1", is_correct=False)
                Choice.objects.create(question=question, text="Wrong Answer 2", is_correct=False)
                Choice.objects.create(question=question, text="Wrong Answer 3", is_correct=False)
            logger.info(f"Quiz successfully created for: {instance.title}")
        else:
            logger.warning(f"No valid questions generated for {instance.title}. Skipping quiz creation.")
    except Exception as e:
        logger.error(f"Quiz generation failed for lesson: {instance.title}. Error: {e}")

    # ----------- PDF GENERATION ------------ 
    try:
        html = f"""
        <html>
        <head><meta charset="UTF-8"></head>
        <body>
            <h1>{instance.title}</h1>
            <p>{instance.content}</p>
        </body>
        </html>
        """
        pdf_file = BytesIO()
        pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_file)
        instance.pdf.save(f"{instance.title.replace(' ', '_')}.pdf", ContentFile(pdf_file.getvalue()))
        logger.info(f"PDF successfully generated for: {instance.title}")
    except Exception as e:
        logger.error(f"PDF generation failed for lesson '{instance.title}': {str(e)}")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
