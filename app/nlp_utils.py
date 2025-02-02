import pytesseract # type: ignore
from PIL import Image
import speech_recognition as sr # type: ignore
from transformers import pipeline # type: ignore
import tempfile
import os
import json
from django.http import JsonResponse

# Initialize NLP pipelines
ner_model = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
sentiment_analyzer = pipeline("sentiment-analysis")


def analyze_text(text):
    """
    Analyze the text using NER, Summarization, and Sentiment Analysis.
    Converts float32 values to strings for JSON compatibility.
    """
    entities = ner_model(text)
    sentiment = sentiment_analyzer(text)[0]
    summary = summarizer(text, max_length=50, min_length=20, do_sample=False)[0]['summary_text']

    # Convert scores to string for JSON serialization
    for entity in entities:
        if 'score' in entity:
            entity['score'] = str(entity['score'])

    sentiment['score'] = str(sentiment['score'])

    return {
        "entities": entities,
        "summary": summary,
        "sentiment": sentiment
    }

def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(audio_file.read())
        tmp_path = tmp.name
    
    with sr.AudioFile(tmp_path) as source:
        audio = recognizer.record(source)
    
    os.unlink(tmp_path)
    return recognizer.recognize_google(audio)

def image_to_text(image_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(image_file.read())
        tmp_path = tmp.name
    
    text = pytesseract.image_to_string(Image.open(tmp_path))
    os.unlink(tmp_path)
    return text.strip() 

def safe_json_response(data):
    """
    Ensures all data is JSON serializable before sending as a response.
    This converts NumPy float32 values and any non-serializable objects.
    """
    return JsonResponse(json.loads(json.dumps(data, default=str)))