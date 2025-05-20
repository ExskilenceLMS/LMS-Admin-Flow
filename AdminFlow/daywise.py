from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from LMS_Project.settings import *
from datetime import datetime, timedelta
import string
import AdminFlow.course as course
from django.db.models import Count, Prefetch,Q
from azure.storage.blob import ContentSettings
import os
from azure.storage.blob import BlobServiceClient
import AdminFlow.course as course
blob_service_client = BlobServiceClient(account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/",credential=AZURE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

@api_view(['POST'])
def update_weekend_holidays(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            batch_id = data.get("batch_id")
            saturday = data.get("saturday")
            sunday = data.get("sunday")
            hours = data.get("hours") 
            if batch_id is None or saturday is None or sunday is None:
                return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)
            try:
                batch = batches.objects.get(batch_id=batch_id)
            except batches.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Batch not found"}, status=404)
            batch.saturday_holiday = saturday  
            batch.sunday_holiday = sunday  
            batch.hours_per_day = hours
            batch.save()
            return JsonResponse({"status": "ok", "message": "Weekend settings updated successfully"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@api_view(['GET'])
def get_weekend_settings(request,batch_id):
    if not batch_id:
        return JsonResponse({"status": "error", "message": "batch_id parameter is required"}, status=400)

    try:
        batch = batches.objects.get(batch_id=batch_id)
        response_data = {
            "status": "ok",
            "saturday": batch.saturday_holiday,  
            "sunday": batch.sunday_holiday ,
            "hours": batch.hours_per_day        
        }

        return JsonResponse(response_data)
    except batches.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Batch not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@api_view(['GET'])
def is_batch_in_blob(request, course, batch):
    try:
        blob_name = f"lms_daywise/{course}/{course}_{batch}.json"
        blob_client = container_client.get_blob_client(blob_name)
        if blob_client.exists():
            return JsonResponse({'exists': True, 'message': f'File "{blob_name}" exists in blob storage.'})
        else:
            return JsonResponse({'exists': False, 'message': f'File "{blob_name}" does not exist in blob storage.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def get_batch_daywise_json(request, course, batch):
    try:
        blob_name = f"lms_daywise/{course}/{course}_{batch}.json"
        blob_client = container_client.get_blob_client(blob_name)

        if blob_client.exists():
            blob_data = blob_client.download_blob().readall()
            json_data = json.loads(blob_data)

            return JsonResponse({
                'exists': True,
                'data': json_data,
                'message': f'File "{blob_name}" exists and was retrieved.'
            }, safe=False)
        else:
            return JsonResponse({
                'exists': False,
                'message': f'File "{blob_name}" does not exist in blob storage.'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_batch_subjects(request, course, batch):
    try:
        blob_name = f"lms_daywise/{course}/{course}_{batch}.json"
        blob_client = container_client.get_blob_client(blob_name)
        if blob_client.exists():
            download_stream = blob_client.download_blob()
            json_data = json.loads(download_stream.readall())
            subjects_in_json = list(json_data.keys())
            subjects_in_course = get_subjects_in_course(course)
            print(subjects_in_course)
            subjects_info = []
            for subject in subjects_in_course:
                is_included = subject['subject_name'] in subjects_in_json
                subjects_info.append({
                    "subject_id": subject['subject_id'],
                    "subject_name": subject['subject_name'],
                    "is_included": is_included
                })

            return JsonResponse({
                'exists': True,
                'message': f'File "{blob_name}" exists in blob storage.',
                'subjects': subjects_info
            })
        else:
            return JsonResponse({
                'exists': False,
                'message': f'File "{blob_name}" does not exist in blob storage.'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_subjects_in_course(course_id):
    try:
        subject_list = []
        courses_list = courses.objects.filter(del_row=False, course_id=course_id)
        subject_details = courses.objects.filter(del_row=False, course_id=course_id).values('course_id', 'Existing_Subjects')
        subject_mapping = {
            detail['course_id']: detail['Existing_Subjects'].split(',') if detail['Existing_Subjects'] else []
            for detail in subject_details
        }
        for course in courses_list:
            track_names = course.tracks.split(",") if course.tracks else []
            for track_name in track_names:
                track = tracks.objects.filter(track_name=track_name).first()
                if track:
                    subjects_for_track = subjects.objects.filter(track_id=track.id, del_row=False)

                    for subject in subjects_for_track:
                        subject_list.append({
                            'subject_id': subject.subject_id,
                            'subject_name': subject.subject_name
                        })
        return subject_list
    except Exception as e:
        print("Error:", str(e))
        return {'error': str(e)}

@api_view(['POST'])
def get_data_of_subject_of_course_plan(request):
    try:
        
        data = json.loads(request.body)
        course_id = data.get('course_id')
        subjects= data.get('subjects')

        if not course_id:
            return JsonResponse({'message': 'course_id is required'}, status=400)

        blob_path = f"lms_courses/{course_id}.json"
        blob_client = container_client.get_blob_client(blob_path)

        if not blob_client.exists():
            return JsonResponse({'message': f'Course ID {course_id} not found'}, status=404)

        blob_properties = blob_client.get_blob_properties()
        current_last_modified = blob_properties.last_modified.timestamp()

        cached_data = cache.get(course_id)
        if cached_data and cached_data['last_modified'] == current_last_modified:
            subjects_dict = cached_data['data']
        else:
            blob_content = blob_client.download_blob().readall()
            subjects_list = json.loads(blob_content)
            
            subjects_dict = {}
            for item in subjects_list:
                for key in item:
                    subjects_dict[key] = item[key]
            
            cache[course_id] = {
                'data': subjects_dict,
                'last_modified': current_last_modified
            }

        return JsonResponse(subjects_dict)

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse(
            {'message': str(e), 'details': 'Error processing request'},
            status=500
        )
   
@api_view(['POST'])
def get_course_plan_of_subjects(request):
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        subjects = data.get('subjects')  # e.g., ["sq", "py"]

        if not course_id:
            return JsonResponse({'error': 'Missing course_id in request.'}, status=400)

        blob_name = f"lms_courses/{course_id}.json"
        blob_client = container_client.get_blob_client(blob_name)

        if not blob_client.exists():
            return JsonResponse({
                'exists': False,
                'message': f'File \"{blob_name}\" does not exist in blob storage.'
            }, status=404)

        download_stream = blob_client.download_blob()
        json_data = json.loads(download_stream.readall())

        if not isinstance(json_data, list):
            return JsonResponse({'error': 'Unexpected JSON structure. Expected a list.'}, status=500)

        # Initialize the result dictionary
        result = {}

        for item in json_data:
            if not isinstance(item, dict):
                continue

            subject_key = list(item.keys())[0]

            if not subjects or subject_key in subjects:
                result[subject_key] = item[subject_key]

        if not result:
            available_subjects = [list(d.keys())[0] for d in json_data if isinstance(d, dict)]
            return JsonResponse({
                'error': 'Requested subjects not found.',
                'available_subjects': available_subjects
            }, status=404)

        return JsonResponse({'data': result}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

