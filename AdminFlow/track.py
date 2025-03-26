from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import string
import AdminFlow.course as course

@api_view(['POST'])
def create_track(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            if data['track_id']=="":  
                existing_tracks_count = tracks.objects.count() + 1
                track_id = f'track{existing_tracks_count}'  
                track = tracks(
                    track_id=track_id,
                    track_name=data['track_name'],
                    created_by=data['by'],
                    created_at=course.get_ist_time()
                )
                track.save()  
            elif 'track_id' in data:
                track = tracks.objects.get(track_id=data['track_id'])
                track.track_name = data.get('track_name', track.track_name)
                track.modified_by = data.get('by', track.modified_by)
                track.modified_at = course.get_ist_time()
                track.save()  
            return JsonResponse({'message': 'Track created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
   
# @api_view(['GET'])
# def get_all_tracks(request):
#     if request.method == "GET":
#         try:
#             tracks_data = tracks.objects.filter(del_row=False)
#             data=[]
            
#             for track in tracks_data:
#                 print(track.track_name)
#                 track_name=track.track_name
#                 all_courses = courses.objects.filter(tracks__icontains=str(track_name))
#                 for course in all_courses:
#                     d={
#                         "course_id":course.course_id,
#                         "course_name":course.course_name,
#                         "track_id":track.track_id,
#                         "track_name": track.track_name,
#                         "track_name_searchable": track.track_name_searchable,
#                         "track_description": track.track_description,
#                         }
#                     data.append(d)
#             return JsonResponse({'tracks': data})
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
        
from django.db.models import Q
@api_view(['GET'])
def get_all_tracks(request):
    if request.method == "GET":
        try:
            tracks_data = tracks.objects.filter(del_row=False)
            if not tracks_data.exists():
                return JsonResponse({'tracks': []})  
            
            tracks_names = [track.track_name for track in tracks_data]
            query = Q()
            for track_name in tracks_names:
                query |= Q(tracks__icontains=track_name)
            
            Courses = courses.objects.filter(query, del_row=False)
            
            data = []
            
            for track in tracks_data:
                found = False
                for course in Courses:
                    if track.track_name in course.tracks.split(","):
                        found = True
                        print('hey',course.course_id)
                        batch_count = batches.objects.filter(course_id=course, del_row=False).count()
                        data.append({
                            "track_id": track.track_id,
                            "track_name": track.track_name,
                            "track_name_searchable": track.track_name_searchable,
                            "track_description": track.track_description,
                            "course_id": course.course_id,
                            "batch_count": batch_count,
                            "course_name": course.course_name,
                        })
                
                if not found:
                    data.append({
                        "track_id": track.track_id,
                        "track_name": track.track_name,
                        "track_name_searchable": track.track_name_searchable,
                        "track_description": track.track_description,
                        "course_id": None,
                        "course_name": None
                    })
            
            return JsonResponse({'tracks': data})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
