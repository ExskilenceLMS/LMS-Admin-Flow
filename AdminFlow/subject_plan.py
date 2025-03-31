from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import  JsonResponse
from datetime import datetime, timedelta
from AdminFlow.course import get_ist_time

@api_view(["GET"])
def get_all_course_tracks_and_subjects(request):
    try:
        course_tracks = []
        courses_list = courses.objects.filter(del_row=False)
        for course in courses_list:
            track_names = course.tracks.split(",") if course.tracks else []
            subject_data = []
            for track_name in track_names:
                
                track = tracks.objects.filter(track_name=track_name).first()  # Get the first match
                if track:  
                    subjects_for_track = subjects.objects.filter(track_id=track.id, del_row=False)
                    
                    for subject in subjects_for_track:
                        subject_data.append({
                            'subject_id': subject.subject_id, 
                            'subject_name': subject.subject_name,
                        })            
            course_tracks.append({
                'course_id': course.course_id,
                'course_name': course.course_name,
                'level': course.course_level,
                'subjects': subject_data,
            })
        
        return JsonResponse(course_tracks, safe=False, status=200)
    
    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

@api_view(["GET"])
def topics_by_subject(request,subject_id):
    try:
        subject = subjects.objects.get(subject_id=subject_id)
        topics_list = topics.objects.filter(subject_id=subject)
        topic_data = []
        for topic in topics_list:
            topic_data.append({
                'topic_id': topic.topic_id,
                'topic_name': topic.topic_name,
            })
        return JsonResponse(topic_data, safe=False, status=200)
    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

