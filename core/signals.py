from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lesson, Quiz, Question, Choice, UserProfile
from django.core.files.base import ContentFile
from io import BytesIO
from xhtml2pdf import pisa
from django.contrib.auth import get_user_model
import logging
import re

User = get_user_model()
logger = logging.getLogger(__name__)


def clean_html(raw_html):
    clean_text = re.sub(r'<.*?>', '', raw_html)
    clean_text = re.sub(r'&[a-z]+;', ' ', clean_text)
    return clean_text.strip()


@receiver(post_save, sender=Lesson)
def create_quiz_and_pdf_for_lesson(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"Generating quiz and PDF for lesson: {instance.title}")

    cleaned_content = clean_html(instance.content)
    if len(cleaned_content.split()) < 10:
        logger.warning(f"Lesson '{instance.title}' has too little content. Skipping quiz and PDF generation.")
        return

    # ---------- LAZY IMPORT TRANSFORMERS ----------
    try:
        import torch
        from transformers import T5ForConditionalGeneration, T5Tokenizer

        model_name = "t5-small"
        tokenizer = T5Tokenizer.from_pretrained(model_name, legacy=False)
        model = T5ForConditionalGeneration.from_pretrained(model_name)

        input_text = f"generate question: {cleaned_content}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

        with torch.no_grad():
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
        logger.error(f"Error generating quiz for lesson: {instance.title}, Error: {str(e)}")

    # ---------- PDF GENERATION ----------
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
