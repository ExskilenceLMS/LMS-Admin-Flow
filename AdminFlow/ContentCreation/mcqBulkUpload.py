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
# def bulk_mcq_upload(request):
#     success_count = 0
#     error_count = 0
#     failed_questions = []
#     try:
#         if request.method == 'POST':
#             data = json.loads(request.body)
#             sub_topic = data.get("subtopic_id")
#             created_by = data.get("CreatedBy")
#             actual_data = data.get("data", [])
#             for d in actual_data:
#                 required_keys = ["Sl no", "Question", "Option1", "Option2", "Option3","Option3"]
#                 missing_keys = [key for key in required_keys if key not in d]
#                 if missing_keys:
#                     error_count += 1
#                     failed_questions.append(d["Sl no"])
#                     continue 
#                 single_mcq = {
#                     "Sl no": d["Sl no"],
#                     "Question": d["Question"],
#                     "options": [d["Option1"], d["Option2"], d["Option3"],d["Option4"]],
#                     "Explanation": d.get("Explanation", ""),
#                     "Level": d.get("Level","level1"),
#                     "Template": d.get("Template",1),
#                     "CreatedBy": created_by,
#                     "subtopic_id": sub_topic,
#                 }
#                 try:
#                     subtopic_id = single_mcq.get('subtopic_id')
#                     created_by = single_mcq.get("CreatedBy")
#                     subject_id = subtopic_id[:2]
#                     topic_id = subtopic_id[:-2]
#                     level = single_mcq.get('Level', 'level1')
#                     mcq_data = {
#                         'level': level,
#                         "subject_id": subject_id,
#                         "topic_id": topic_id,
#                         "subtopic_id": subtopic_id,
#                         'CreatedBy': created_by,
#                         'question': single_mcq.get('Question', ""),
#                         'options': single_mcq.get('options', []),
#                         'correct_answer': single_mcq.get('options')[0],
#                         'Tags': single_mcq.get('Tags', []),
#                         'Template': single_mcq.get('Template', 1),
#                         'Explanation': single_mcq.get('Explanation', ""),
#                     }
#                     subtopic_folder = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/"
#                     mcq_folder = f"{subtopic_folder}mcq/"
#                     level_char = 'e' if level == 'level1' else 'm' if level == 'level2' else 'h'
#                     file_pattern = f"q{subtopic_id}m{level_char}m"
                    
#                     def get_next_number(folder_path, file_pattern):
#                         existing_files = list(container_client.list_blobs(name_starts_with=folder_path))
#                         existing_numbers = set()
#                         for blob in existing_files:
#                             filename = blob.name.split('/')[-1]
#                             if file_pattern in filename:
#                                 try:
#                                     number = int(filename.split('m')[-1].split('.')[0])
#                                     existing_numbers.add(number)
#                                 except ValueError:
#                                     continue
#                         if not existing_numbers:
#                             return 1
#                         for i in range(1, max(existing_numbers) + 2):
#                             if i not in existing_numbers:
#                                 return i
#                         return max(existing_numbers) + 1

#                     next_mcq_number = get_next_number(mcq_folder, file_pattern)
#                     if next_mcq_number > 99:
#                         return JsonResponse({'error': 'Maximum number of questions (99) for this level has been reached.'}, status=400)

#                     mcq_filename = f"{file_pattern}{next_mcq_number:02d}.json"
#                     mcq_blob_name = mcq_folder + mcq_filename

#                     blob_client = container_client.get_blob_client(mcq_blob_name)
#                     if blob_client.exists():
#                         return JsonResponse({'error': f'File {mcq_filename} already exists.'}, status=400)

#                     json_data = json.dumps(mcq_data, ensure_ascii=False)
#                     encoded_data = json_data.encode('utf-8')
#                     blob_client.upload_blob(
#                         encoded_data,
#                         overwrite=False,
#                         content_settings=ContentSettings(
#                             content_type='application/json',
#                             charset='utf-8'
#                         )
#                     )

#                     subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
#                     qn_id = os.path.splitext(mcq_filename)[0]
#                     question = questions(
#                         question_id=qn_id,
#                         sub_topic_id=subtopic,
#                         question_type='mcq',
#                         level=level,
#                         created_by=created_by,
#                         creation_time=course.get_ist_time(),
#                         last_updated_time=course.get_ist_time(),
#                         reviewed_by='',
#                         tags=single_mcq.get('Tags', [])
#                     )
#                     question.save()

#                     subtopic.mcq = questions.objects.filter(sub_topic_id=subtopic, question_type='mcq').count()
#                     subtopic.save()

#                     success_count += 1

#                 except Exception as e:
#                     error_count += 1
#                     failed_questions.append(d["Sl no"])
#                     print(f"Error with question {d['Sl no']}: {str(e)}")
#                     continue 
                
#             return JsonResponse({
#                 'message': 'Bulk MCQ upload complete',
#                 'success_count': success_count,
#                 'error_count': error_count,
#                 'failed_questions': failed_questions
#             })

#         return JsonResponse({'error': 'Invalid request method'}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': f'Internal Server Error: {str(e)}'}, status=500)

def bulk_mcq_upload(request):
    success_count = 0
    error_count = 0
    failed_questions = []
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            created_by = data.get("CreatedBy")
            actual_data = data.get("data", [])
            for d in actual_data:
                required_keys = ["Sl no", "Question", "Option1", "Option2", "Option3", "Option4", "subtopic_id"]
                missing_keys = [key for key in required_keys if key not in d]
                if missing_keys:
                    error_count += 1
                    failed_questions.append(d["Sl no"])
                    continue

                subtopic_id = d["subtopic_id"]
                single_mcq = {
                    "Sl no": d["Sl no"],
                    "Question": d["Question"],
                    "options": [d["Option1"], d["Option2"], d["Option3"], d["Option4"]],
                    "Explanation": d.get("Explanation", ""),
                    "Level": d.get("Level", "level1"),
                    "Template": d.get("Template", 1),
                    "CreatedBy": created_by,
                    "subtopic_id": subtopic_id,
                }
                try:
                    subtopic_id = single_mcq.get('subtopic_id')
                    created_by = single_mcq.get("CreatedBy")
                    subject_id = subtopic_id[:2]
                    topic_id = subtopic_id[:-2]
                    level = single_mcq.get('Level', 'level1')
                    mcq_data = {
                        'level': level,
                        "subject_id": subject_id,
                        "topic_id": topic_id,
                        "subtopic_id": subtopic_id,
                        'CreatedBy': created_by,
                        'question': single_mcq.get('Question', ""),
                        'options': single_mcq.get('options', []),
                        'correct_answer': single_mcq.get('options')[0],
                        'Tags': single_mcq.get('Tags', []),
                        'Template': single_mcq.get('Template', 1),
                        'Explanation': single_mcq.get('Explanation', ""),
                    }
                    subtopic_folder = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/"
                    mcq_folder = f"{subtopic_folder}mcq/"
                    level_char = 'e' if level == 'level1' else 'm' if level == 'level2' else 'h'
                    file_pattern = f"q{subtopic_id}m{level_char}m"

                    def get_next_number(folder_path, file_pattern):
                        existing_files = list(container_client.list_blobs(name_starts_with=folder_path))
                        existing_numbers = set()
                        for blob in existing_files:
                            filename = blob.name.split('/')[-1]
                            if file_pattern in filename:
                                try:
                                    number = int(filename.split('m')[-1].split('.')[0])
                                    existing_numbers.add(number)
                                except ValueError:
                                    continue
                        if not existing_numbers:
                            return 1
                        for i in range(1, max(existing_numbers) + 2):
                            if i not in existing_numbers:
                                return i
                        return max(existing_numbers) + 1

                    next_mcq_number = get_next_number(mcq_folder, file_pattern)
                    if next_mcq_number > 99:
                        return JsonResponse({'error': 'Maximum number of questions (99) for this level has been reached.'}, status=400)

                    mcq_filename = f"{file_pattern}{next_mcq_number:02d}.json"
                    mcq_blob_name = mcq_folder + mcq_filename

                    blob_client = container_client.get_blob_client(mcq_blob_name)
                    if blob_client.exists():
                        return JsonResponse({'error': f'File {mcq_filename} already exists.'}, status=400)

                    # Dump JSON data with indentation and include newline characters
                    json_data = json.dumps(mcq_data, ensure_ascii=False, indent=4)
                    encoded_data = json_data.encode('utf-8')
                    blob_client.upload_blob(
                        encoded_data,
                        overwrite=False,
                        content_settings=ContentSettings(
                            content_type='application/json',
                            charset='utf-8'
                        )
                    )

                    subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
                    qn_id = os.path.splitext(mcq_filename)[0]
                    question = questions(
                        question_id=qn_id,
                        sub_topic_id=subtopic,
                        question_type='mcq',
                        level=level,
                        created_by=created_by,
                        creation_time=course.get_ist_time(),
                        last_updated_time=course.get_ist_time(),
                        reviewed_by='',
                        tags=single_mcq.get('Tags', [])
                    )
                    question.save()

                    subtopic.mcq = questions.objects.filter(sub_topic_id=subtopic, question_type='mcq').count()
                    subtopic.save()

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    failed_questions.append(d["Sl no"])
                    print(f"Error with question {d['Sl no']}: {str(e)}")
                    continue

            return JsonResponse({
                'message': 'Bulk MCQ upload complete',
                'success_count': success_count,
                'error_count': error_count,
                'failed_questions': failed_questions
            })

        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Internal Server Error: {str(e)}'}, status=500)

