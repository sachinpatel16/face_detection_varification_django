import base64
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, Attendance
from PIL import Image
from io import BytesIO
import io
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import numpy as np
import face_recognition
import json
import cv2
import os
import hashlib
import sqlite3
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from datetime import datetime

from app.nlp_utils import analyze_text, audio_to_text, image_to_text, safe_json_response

# Create your views here.
def home(request):
    return render(request, 'home.html')
# import face_recognition

# Registration View
@csrf_exempt
def register(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get('username')
        photo_data = request.POST.get('photo')  # For base64-encoded image
        photo_file = None  # Placeholder for photo file

        if not username or not photo_data:
            return HttpResponseBadRequest("Missing required fields.")

        try:
            # Handle base64 photo data
            format, imgstr = photo_data.split(';base64,')
            ext = format.split('/')[-1]
            photo_file = ContentFile(base64.b64decode(imgstr), name=f"{username}.{ext}")
        except Exception as e:
            return HttpResponseBadRequest("Invalid photo data.")

        try:
            # Attempt to create the user and save both photo and encoded data
            user = UserProfile.objects.create(
                username=username,
                photo=photo_file,
                encode_photos=photo_data
            )
            message = "User registered successfully!"
        except IntegrityError:
            # If the username already exists
            message = "User already exists."

    return render(request, 'reg.html', {'message': message})
# Login View
def login(request):
    message = ''
    if request.method == "POST":
        username = request.POST.get('username')
        photo_data = request.POST.get('photo')

        try:
            user_profile = UserProfile.objects.get(username=username)

            if photo_data:
                # Decode the base64 image data from the captured photo
                image_data = base64.b64decode(photo_data.split(',')[1])
                uploaded_image = Image.open(BytesIO(image_data))
                
                # Convert the uploaded image to a format that face_recognition can work with
                uploaded_image = uploaded_image.convert('RGB')
                uploaded_image_array = face_recognition.load_image_file(BytesIO(image_data))

                # Get the face encoding of the uploaded photo
                uploaded_face_encoding = face_recognition.face_encodings(uploaded_image_array)

                if uploaded_face_encoding:
                    # If the uploaded image has a face encoding, compare it with the stored image
                    if user_profile.photo:
                        stored_image = user_profile.photo
                        stored_image.seek(0)

                        # Convert the stored image to a format that face_recognition can work with
                        stored_image_array = face_recognition.load_image_file(stored_image)
                        
                        # Get the face encoding of the stored photo
                        stored_face_encoding = face_recognition.face_encodings(stored_image_array)

                        if stored_face_encoding:
                            # Compare the face encodings
                            results = face_recognition.compare_faces([stored_face_encoding[0]], uploaded_face_encoding[0])

                            if results[0]:
                                message = f"{username}, Login successful"
                            else:
                                message = "Photo does not match"
                        else:
                            message = "Stored image does not contain a face"
                    else:
                        message = "No stored photo to compare"
                else:
                    message = "No face detected in the captured photo"
            else:
                message = "No photo captured"
        except UserProfile.DoesNotExist:
            message = "Username does not exist"

    return render(request, 'login.html', {'message': message})

def mark_attendance(request):
    # Load known faces and encodings from the database
    known_faces = []
    known_ids = []

    for user in UserProfile.objects.all():
        photo_path = user.photo  # Assuming photo is stored as a file
        image = face_recognition.load_image_file(photo_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_faces.append(encodings[0])  # Take the first encoding
            known_ids.append(user.id)

    # Start webcam for recognition
    video = cv2.VideoCapture(0)

    try:
        while True:
            ret, frame = video.read()
            if not ret:
                break

            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(known_faces, face_encoding)
                if True in matches:
                    match_index = matches.index(True)
                    user_id = known_ids[match_index]

                    # Mark attendance
                    Attendance.objects.get_or_create(
                        user_id=user_id,
                        timestamp=datetime.now()
                    )

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"User: {user_id}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow("Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        video.release()
        cv2.destroyAllWindows()

@login_required
@csrf_exempt
def chat(request):
    if request.method == 'POST':
        input_type = request.POST.get('type')
        result = {}

        try:
            if input_type == 'text':
                text = request.POST.get('text')
                result = analyze_text(text)
            
            elif input_type == 'audio' and request.FILES.get('audio'):
                audio_file = request.FILES['audio']
                text = audio_to_text(audio_file)
                result = analyze_text(text)
                result['original_text'] = text
            
            elif input_type == 'image' and request.FILES.get('image'):
                image_file = request.FILES['image']
                text = image_to_text(image_file)
                if text:  # Ensure text is not empty
                    result = analyze_text(text)
                    result['original_text'] = text
                else:
                    result = {"error": "No text found in image."}
            
            elif input_type == 'speech':
                text = request.POST.get('text')
                result = analyze_text(text)
            
            return safe_json_response({'success': True, 'result': result})
        
        except Exception as e:
            return safe_json_response({'success': False, 'error': str(e)})

    return render(request, 'chat.html')