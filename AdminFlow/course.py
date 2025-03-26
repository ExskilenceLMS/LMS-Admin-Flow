from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import  JsonResponse
from datetime import datetime, timedelta
import ast

def get_ist_time():
        
        return  datetime.utcnow().__add__(timedelta(hours=15, minutes=30))

@api_view(['POST'])
def create_course(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            tracks_list = data["tracks"]
            track_names=""
            for track in tracks_list:
                track_names+=str(tracks.objects.get(track_id=track).track_name)+","
            if data['course_id']=="":  
                existing_courses_count = courses.objects.count() + 1
                course_id = f'course{existing_courses_count}'  
                course = courses(
                    course_id=course_id,
                    course_name=data['course_name'],
                    course_description=data['course_description'],
                    course_level=data['course_level'],
                    created_by=data['by'],
                    tracks=track_names[0:-1] if track_names[-1]=="," else track_names,
                    created_at=get_ist_time()
                )
                course.save()  
            elif 'course_id' in data:
                course = courses.objects.get(course_id=data['course_id'])
                course.course_name = data.get('course_name', course.course_name)
                course.course_description = data.get('course_description', course.course_description)
                course.course_level = data.get('course_level', course.course_level)
                if track_names == "":
                    course.tracks = ""
                else:
                    course.tracks = ','.join(track_names[0:-1].split(",") if track_names[-1]=="," else track_names.split(","))
                course.modified_by = data.get('by', course.modified_by)
                course.modified_at = get_ist_time()

                course.save()  
            return JsonResponse({'message': 'Course created/updated successfully'})

        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=500)
        
@api_view(['GET'])
def get_all_courses(request):
    try:
        all_courses = courses.objects.filter(del_row=False)  
        courses_list = []
        
        for course in all_courses:
            batch_count = batches.objects.filter(course_id=course, del_row=False).count()
            students_count = students_info.objects.filter(course_id=course, del_row=False).count()
            names=course.tracks.split(",") if course.tracks else []
            track_list = names
            track_ids = [
                tracks.objects.get(track_name=track).track_id 
                for track in track_list
            ]
            course_data = {
                'course_id': course.course_id,
                'tracks': track_ids,
                'track_names':course.tracks,
                'course_name': course.course_name,
                'course_description': course.course_description,
                'course_level': course.course_level,
                'batch_count': batch_count,
                "students_count": students_count
            }
            courses_list.append(course_data)

        return JsonResponse({'courses': courses_list})

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['POST'])
def delete_course(request):
    try:
        data = json.loads(request.body)
        course = courses.objects.get(course_id=data['course_id'])
        course.del_row = True
        course.save()  
        return JsonResponse({'message': 'Course deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def get_all_tracks_for_courses(request):
    try:
        all_tracks = tracks.objects.filter(del_row=False)  
        tracks_list = []
        for track in all_tracks:
            track_data = {
                'track_id': track.track_id,
                'track_name': track.track_name,
            }
            tracks_list.append(track_data)
        return JsonResponse({'tracks': tracks_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


