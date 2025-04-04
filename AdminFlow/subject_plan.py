from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import  JsonResponse
from datetime import datetime, timedelta
from azure.storage.blob import ContentSettings
import os
from azure.storage.blob import BlobServiceClient
import AdminFlow.course as get_ist_time
from LMS_Project.settings import *
from django.db.models import Count, Q

blob_service_client = BlobServiceClient(account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/",credential=AZURE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

@api_view(["GET"])
def get_all_course_tracks_and_subjects(request):
    try:
        course_tracks = []
        courses_list = courses.objects.filter(del_row=False)
        
        subject_details = courses.objects.all().values('course_id', 'Existing_Subjects')
        subject_mapping = {
            detail['course_id']: detail['Existing_Subjects'].split(',') if detail['Existing_Subjects'] else []
            for detail in subject_details
        }

        for course in courses_list:
            track_names = course.tracks.split(",") if course.tracks else []
            subject_data = []

            for track_name in track_names:
                track = tracks.objects.filter(track_name=track_name).first()  
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
                'Existing_Subjects': subject_mapping.get(course.course_id, []),  
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

@api_view(['GET'])
def get_all_subtopics_data(request, topic_id):
    try:
        topic=topics.objects.get(topic_id=topic_id)
        subtopics_ls = sub_topics.objects.filter(topic_id=topic).values(
            'sub_topic_id', 
            'sub_topic_name', 
            'notes', 
            'videos', 
            'mcq', 
            'coding'
        )
        subtopics_list = list(subtopics_ls)
        return JsonResponse(subtopics_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['POST'])
def get_content_for_subtopic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subtopic_id = data.get('sub_topic_id')
            if not subtopic_id:
                return JsonResponse({'error': 'subtopic_id is required'}, status=400)
            subject_id = subtopic_id[:2]
            topic_id = subtopic_id[:-2]
            subtopic_folder = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/"
            content_folder = subtopic_folder + "content/"
            content_filename = f"{subtopic_id}.json"
            content_blob_name = content_folder + content_filename
            content_blob_client = container_client.get_blob_client(content_blob_name)
            try:
                blob_data = content_blob_client.download_blob().readall()
                content_data = json.loads(blob_data)
                return JsonResponse(content_data, status=200)
            except Exception as e:
                return JsonResponse({'data': 'No data found'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(["POST"])
def get_questions_data_by_subtopic(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            subtopic_id = data.get('sub_topic_id')
            subtopic=sub_topics.objects.get(sub_topic_id=subtopic_id)
            questions_count = (
                questions.objects.filter(sub_topic_id=subtopic)
                .values('question_type')
                .annotate(
                    level1_count=Count('question_id', filter=Q(level='Easy')),
                    level2_count=Count('question_id', filter=Q(level='Medium')),
                    level3_count=Count('question_id', filter=Q(level='Hard'))
                )
            )
            result = {
                'mcq': {
                    'level1': 0,
                    'level2': 0,
                    'level3': 0
                },
                'coding': {
                    'level1': 0,
                    'level2': 0,
                    'level3': 0
                }
            }
            for entry in questions_count:
                qn_type = entry['question_type']
                if qn_type in result:
                    result[qn_type]['level1'] = entry['level1_count']
                    result[qn_type]['level2'] = entry['level2_count']
                    result[qn_type]['level3'] = entry['level3_count']
            return JsonResponse(result, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
cache = {}
@api_view(["POST"])
def get_course_subjects(request):
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        subject_id = data.get('subject_id')
        if not course_id:
            return JsonResponse({'message': 'course_id is required'}, status=400)
        if not subject_id:
            return JsonResponse({'message': 'subject_id is required'}, status=400)
        blob_path = f"lms_subjectplans/{course_id}.json"
        blob_client = container_client.get_blob_client(blob_path)
        if not blob_client.exists():
            return JsonResponse({'topics':[]})
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

        subject_data = subjects_dict.get(subject_id)
        if not subject_data:
            return JsonResponse(
                {'message': f'Subject ID {subject_id} not found in course {course_id}'},
                status=404
            )

        return JsonResponse(subject_data)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse(
            {'message': str(e), 'details': 'Error processing request'},
            status=500
        )

@api_view(['POST'])
def save_subject_plans_details(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            course_id = data.get('course_id')
            subject_id = data.get('subject_id')
            if not courses.objects.filter(course_id=course_id).exists():
                return JsonResponse({
                    "status": "error",
                    "message": f"Course ID {course_id} does not exist in LMS_SubjectPlans"
                }, status=400)
            try:
                existing_entry = courses.objects.filter(course_id=course_id).first()
                if existing_entry:
                    if existing_entry.Existing_Subjects:
                        existing_subjects = existing_entry.Existing_Subjects.split(',')
                    else:
                        existing_subjects = []
                    new_subjects = subject_id.split(',')
                    all_subjects = list(set(existing_subjects + new_subjects))
                    existing_entry.Existing_Subjects = ','.join(all_subjects)
                    subject_plan = existing_entry
                blob_path = f"lms_subjectplans/{course_id}.json"
                try:
                    blob_client = container_client.get_blob_client(blob_path)
                    try:
                        existing_content = blob_client.download_blob().readall()
                        existing_data = json.loads(existing_content)
                    except Exception:
                        existing_data = []
                    
                    if not isinstance(existing_data, list):
                        existing_data = []
                    for single_subject in subject_id.split(','):
                        subject_exists = False
                        for i, item in enumerate(existing_data):
                            if isinstance(item, dict) and list(item.keys())[0] == single_subject:
                                existing_data[i] = {single_subject: data.get(single_subject, {})}
                                subject_exists = True
                                break
                        
                        if not subject_exists:
                            existing_data.append({single_subject: data.get(single_subject, {})})
                    json_content = json.dumps(existing_data, indent=2)
                    blob_client.upload_blob(json_content, overwrite=True)
                    subject_plan.path = blob_path
                    subject_plan.save()
                    return JsonResponse({
                        "status": "success",
                        "message": "Subject plan details saved successfully",
                        "path": blob_path
                    })
                    
                except Exception as blob_error:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Blob storage error: {str(blob_error)}",
                        "details": "Error occurred while handling blob storage operations"
                    }, status=500)
                    
            except Exception as db_error:
                return JsonResponse({
                    "status": "error",
                    "message": f"Database error: {str(db_error)}",
                    "details": "Error occurred while performing database operations"
                }, status=400)
                
    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON data in request body"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "details": "Unexpected error occurred"
        }, status=500)

@api_view(['GET'])
def get_all_courses(request):
    try:
        all_courses = courses.objects.filter(del_row=False)
        courses_list = []
        for course in all_courses:
            batch_list = batches.objects.filter(course_id=course, del_row=False)
            batch_data = []
            for batch in batch_list:
                batch_data.append({
                    'batch_id': batch.batch_id,
                    'batch_name': batch.batch_name,
                })
            course_data = {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'batches': batch_data
            }
            courses_list.append(course_data)
        return JsonResponse({'courses': courses_list})

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
  

@api_view(['POST'])
def get_all_data_of_course(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'message': 'Method not allowed'}, status=405)
        
        data = json.loads(request.body)
        course_id = data.get('course_id')

        if not course_id:
            return JsonResponse({'message': 'course_id is required'}, status=400)

        blob_path = f"lms_subjectplans/{course_id}.json"
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
def save_daywise(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'message': 'Method not allowed'}, status=405)

        data = json.loads(request.body)
        course = data.get("course_id")
        batch_id=data.get("batch_id")
        daywise = data.get('schedule')
        now = datetime.now()
        course_id = f"{course}_{batch_id}"

        print('check',course_id)

        blob_path = f"lms_daywise/{course}/{course_id}.json"

        json_data = json.dumps(daywise, ensure_ascii=False, indent=4)
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER, blob=blob_path)
        blob_client.upload_blob(json_data, overwrite=True)

        return JsonResponse({
                        "status": "success",
                        "message": "Daywise details saved successfully",
                        "path": blob_path
                    })

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse(
            {'message': str(e), 'details': 'Error processing request'},
            status=500
        )
    

