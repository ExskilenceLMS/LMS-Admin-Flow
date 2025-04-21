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


@api_view(['GET'])
def dashboard_data(request):
    if request.method == 'GET':
        try:
            # Fetch all subjects and annotate them with the total count of questions
            subjects_list = subjects.objects.filter(del_row=False).annotate(
                total_questions=Count('topics__sub_topics__questions')
            ).values('subject_id', 'subject_name', 'total_questions')

            subjects_data = [
                {
                    'subject_id': subject['subject_id'],
                    'subject_name': subject['subject_name'],
                    'count': {'total': subject['total_questions']}
                }
                for subject in subjects_list
            ]

            return JsonResponse(subjects_data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['POST'])
def topics_subtopics_by_subject(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            subject_id = data.get('subject_id')
            if subject_id is None:
                return JsonResponse({'error': 'subject_id is required'}, status=400)
            try:
                subject_instance = subjects.objects.get(subject_id=subject_id)
            except subjects.DoesNotExist:
                return JsonResponse({'error': 'Subject not found'}, status=404)

            topics_list = topics.objects.filter(subject_id=subject_instance,del_row=False)

            topics_with_subtopics = []

            for topic in topics_list:
                subtopics = sub_topics.objects.filter(topic_id=topic,del_row=False)

                topics_with_subtopics.append({
                    'topic_id': topic.topic_id,
                    'topic_name': topic.topic_name,
                    'sub_topics': [
                        {
                            'subtopic_id': subtopic.sub_topic_id,
                            'subtopic_name': subtopic.sub_topic_name
                        }
                        for subtopic in subtopics
                    ]
                })

            return JsonResponse({'topics': topics_with_subtopics}, safe=False)
                        
            # subtopics_prefetch = Prefetch(
            #     'subtopic_set',  
            #     queryset=sub_topics.objects.all(), 
            #     to_attr='sub_topics' 
            # )
            # subject_instance=subjects.objects.filter(subject_id=subject_id)
            # topics_ls = topics.objects.filter(subject_id=subject_instance).prefetch_related(subtopics_prefetch)
            # print('11')
            # topics_list = [
            #     {
            #         'topic_id': topic.topic_id,
            #         'topic_name': topic.topic_name,
            #         'sub_topics': [
            #             {
            #                 'subtopic_id': subtopic.subtopic_id,
            #                 'subtopic_name': subtopic.subtopic_name
            #             }
            #             for subtopic in topic.subtopics
            #         ]
            #     }
            #     for topic in topics_ls
            # ]
            # return JsonResponse({'topics': topics_list}, safe=False)

        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Internal Server Error: {str(e)}'}, status=500)

@api_view(['GET'])
def get_count_of_questions(request, subject_id):
    if request.method == 'GET':
        try:
            subjects_list = subjects.objects.filter(subject_id=subject_id).annotate(
                total_questions=Count('topics__sub_topics__questions'),
                mcq_questions=Count('topics__sub_topics__questions', filter=Q(topics__sub_topics__questions__question_type='mcq')),
                coding_questions=Count('topics__sub_topics__questions', filter=Q(topics__sub_topics__questions__question_type='coding'))
            ).values('subject_id', 'subject_name', 'total_questions', 'mcq_questions', 'coding_questions')

            if not subjects_list.exists():
                return JsonResponse({'error': 'Subject not found'}, status=404)

            for question in subjects_list:
                Question_data = {
                    'count': {
                        'total': question['total_questions'],
                        'mcq': question['mcq_questions'],
                        'coding': question['coding_questions']
                    }
                }

            return JsonResponse(Question_data, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)   

@api_view(['POST'])
def get_questions_list(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subtopic_id = data.get('subtopic_id')
            content_type = data.get('type')
            if not subtopic_id or not content_type:
                return JsonResponse({'error': 'subtopic_id and type are required'}, status=400)
            subject_id = subtopic_id[:2]
            topic_id = subtopic_id[:-2]
            if content_type.lower() == 'mcq':
                folder_path = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/mcq/"
            elif content_type.lower() == 'coding':
                folder_path = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/coding/"
            else:
                return JsonResponse({'error': 'Invalid content type'}, status=400)
            blobs = container_client.list_blobs(name_starts_with=folder_path)
            question_filenames = [blob.name.split('/')[-1] for blob in blobs]
            return JsonResponse({'questions': question_filenames})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['POST'])
def course_Plan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subtopic_id = data.get('subtopic_id')
            level = data.get('level')
            if level=='level1' :
                level_char='e'
            elif level=='level2':
                level_char='m'
            elif level=='level3':
                level_char="h"
            else:
                level_char='e'
            content_type = data.get('type')
            current_file = data.get('currentFile')
            last_updated_by = data.get('Last_Updated_by')
            subject_id = subtopic_id[:2]
            topic_id = subtopic_id[:-2]
            subtopic_folder = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/"
            
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
            if current_file:
                try:
                    if content_type == 'coding':
                        blob_name = f"{subtopic_folder}coding/{current_file}"
                    elif content_type == 'mcq':
                        blob_name = f"{subtopic_folder}mcq/{current_file}"
                    else:
                        return JsonResponse({'error': 'Invalid content type'}, status=400)
                    blob_client = container_client.get_blob_client(blob_name)
                    if not blob_client.exists():
                        return JsonResponse({'error': f'File {current_file} not found.'}, status=404)
                    if content_type == 'coding':
                        update_data = {
                            'Last_Updated_by': last_updated_by,
                            'level': level,
                            'subject_id': subject_id,
                            'topic_id': topic_id,
                            'subtopic_id': subtopic_id,
                            'Name': data.get('Name'),
                            'QNty': data.get('QNty'),
                            'QnTy': data.get('QnTy'),
                            'MultiSelect': data.get('MultiSelect'),
                            'QnTe': data.get('QnTe'),
                            'ConceptID': data.get('ConceptID'),
                            'Tags': data.get('Tags'),
                            'Qn': data.get('Qn'),
                            'Template': data.get('Template'),
                            'Examples': data.get('Examples'),
                            'Ans': data.get('Ans'),
                            'FunctionCall': data.get('FunctionCall'),
                            'TestCases': data.get('TestCases'),
                            'Explanations': data.get('Explanations'),
                            'Hints': data.get('Hints'),
                            'currentFile': current_file,
                            'LastUpdated': data.get('LastUpdated'),
                            'Query': data.get('Query'),
                            'Table': data.get('Table')
                        }
                    else:  
                        update_data = {
                            'Last_Updated_by': last_updated_by,
                            'level': level,
                            'CreatedBy': data.get('CreatedBy'),
                            'subject_id': subject_id,
                            'topic_id': topic_id,
                            'subtopic_id': subtopic_id,
                            'question': data.get('question'),
                            'options': data.get('options'),
                            'correct_answer': data.get('correct_answer'),
                            'Tags': data.get('Tags'),
                            'Template': data.get('template'),
                            'Explanation': data.get('Explanation'),
                            'LastUpdated': data.get('LastUpdated'),
                        }
                    json_data = json.dumps(update_data, ensure_ascii=False)
                    encoded_data = json_data.encode('utf-8')
                    blob_client.upload_blob(
                        encoded_data,
                        overwrite=True,
                        content_settings=ContentSettings(
                            content_type='application/json',
                            charset='utf-8'
                        )
                    )
                    qn_id = os.path.splitext(current_file)[0]
                    question = questions.objects.get(question_id=qn_id)
                    question.last_updated_time = course.get_ist_time()
                    question.last_updated_by = last_updated_by
                    question.tags = ','.join(data.get('Tags', [])) if isinstance(data.get('Tags'), list) else data.get('Tags', '')  # Store as CSV in DB
                    question.save()
                    return JsonResponse({
                        'message': 'Question updated successfully',
                        'blob_name': blob_name
                    })
                except Exception as e:
                    print(f"Error updating blob: {str(e)}")
                    return JsonResponse({
                        'error': f'Failed to update question: {str(e)}',
                        'blob_name': blob_name if 'blob_name' in locals() else 'unknown'
                    }, status=500)

            else:
                if content_type == 'coding':
                    coding_data = {
                        'level': level,
                        'subject_id': subject_id,
                        'topic_id': topic_id,
                        'subtopic_id': subtopic_id,
                        'Name': data.get('Name'),
                        'QNty': data.get('QNty'),
                        'CreatedON': data.get('CreatedON'),
                        'QnTy': data.get('QnTy'),
                        'MultiSelect': data.get('MultiSelect'),
                        'QnTe': data.get('QnTe'),
                        'ConceptID': data.get('ConceptID'),
                        'Tags': data.get('Tags'),
                        'Qn': data.get('Qn'),
                        'Template': data.get('Template'),
                        'Examples': data.get('Examples'),
                        'Ans': data.get('Ans'),
                        'FunctionCall': data.get('FunctionCall'),
                        'TestCases': data.get('TestCases'),
                        'Explanations': data.get('Explanations'),
                        'Hints': data.get('Hints'),
                        'LastUpdated': data.get('LastUpdated'),
                        'Query': data.get('Query'),
                        'Table': data.get('Table')
                    }
                    coding_folder = f"{subtopic_folder}coding/"
                    file_pattern = f"q{subtopic_id}c{level_char}m"
                    next_coding_number = get_next_number(coding_folder, file_pattern)
                    if next_coding_number > 99:
                        return JsonResponse({'error': 'Maximum number of questions (99) for this level has been reached.'}, status=400)
                    coding_filename = f"{file_pattern}{next_coding_number:02d}.json"
                    coding_blob_name = coding_folder + coding_filename
                    blob_client = container_client.get_blob_client(coding_blob_name)
                    if blob_client.exists():
                        return JsonResponse({'error': f'File {coding_filename} already exists.'}, status=400)
                    json_data = json.dumps(coding_data, ensure_ascii=False)
                    encoded_data = json_data.encode('utf-8')
                    blob_client.upload_blob(
                        encoded_data,
                        overwrite=False,
                        content_settings=ContentSettings(
                            content_type='application/json',
                            charset='utf-8'
                        )
                    )
                    qn_id = os.path.splitext(coding_filename)[0]
                    subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
                    question = questions(
                        question_id=qn_id,
                        sub_topic_id=subtopic,
                        question_type='coding',
                        creation_time=course.get_ist_time(),
                        last_updated_time=course.get_ist_time(),
                        level=level,
                        created_by=data.get('CreatedBy'),
                        last_updated_by=last_updated_by,
                        reviewed_by='',
                        tags=','.join(data.get('Tags', [])) if isinstance(data.get('Tags'), list) else data.get('Tags', '')
                    )
                    question.save()
                    subtopic.coding = questions.objects.filter(sub_topic_id=subtopic, question_type='coding').count()
                    subtopic.save()
                elif content_type == 'mcq':
                    print('123')
                    mcq_data = {
                        'level': level,
                        'CreatedBy': data.get('CreatedBy'),
                        'subject_id': subject_id,
                        'topic_id': topic_id,
                        'subtopic_id': subtopic_id,
                        'question': data.get('question'),
                        'options': data.get('options'),
                        'correct_answer': data.get('correct_answer'),
                        'Tags': data.get('Tags'),
                        'Template': data.get('Template'),
                        'Explanation': data.get('Explanation'),
                        'LastUpdated': data.get('LastUpdated'),
                    }
                    mcq_folder = f"{subtopic_folder}mcq/"
                    file_pattern = f"q{subtopic_id}m{level_char}m"
                    next_mcq_number = get_next_number(mcq_folder, file_pattern)
                    if next_mcq_number > 99:
                        return JsonResponse({'error': 'Maximum number of questions (99) for this level has been reached.'}, status=400)
                    mcq_filename = f"{file_pattern}{next_mcq_number:02d}.json"
                    mcq_blob_name = mcq_folder + mcq_filename
                    blob_client = container_client.get_blob_client(mcq_blob_name)
                    if blob_client.exists():
                        return JsonResponse({'error': f'File {mcq_filename} already exists.'}, status=400)
                    json_data = json.dumps(mcq_data, ensure_ascii=False)
                    encoded_data = json_data.encode('utf-8')
                    blob_client.upload_blob(
                        encoded_data,
                        overwrite=False,
                        content_settings=ContentSettings(
                            content_type='application/json',
                            charset='utf-8'
                        )
                    )
                    qn_id = os.path.splitext(mcq_filename)[0]
                    subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
                    question = questions(
                        question_id=qn_id,
                        sub_topic_id=subtopic,
                        question_type='mcq',
                        level=level,
                        created_by=data.get('CreatedBy'),
                        creation_time=course.get_ist_time(),
                        last_updated_time=course.get_ist_time(),
                        last_updated_by=last_updated_by,
                        reviewed_by='',
                        tags=','.join(data.get('Tags', [])) if isinstance(data.get('Tags'), list) else data.get('Tags', '')
                    )
                    question.save()
                    subtopic.mcq = questions.objects.filter(sub_topic_id=subtopic, question_type='mcq').count()
                    subtopic.save()
                return JsonResponse({
                    'message': 'Question created successfully',
                    'blob_name': coding_blob_name if content_type == 'coding' else mcq_blob_name
                })
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['POST'])
def get_specific_question(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question_filename = data.get('question_filename')

            if not question_filename:
                return JsonResponse({'error': 'question_filename is required'}, status=400)

            subtopic_id = question_filename[1:15]  
            topic_id = question_filename[1:13]  
            subject_id = question_filename[1:3] 
            content_type = question_filename[15] 

            if content_type.lower() == 'c':
                folder_path = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/coding/"
            elif content_type.lower() == 'm':
                folder_path = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/mcq/"
            else:
                return JsonResponse({'error': 'Invalid content type in filename'}, status=400)

            question_blob_name = folder_path + question_filename
            question_blob_client = container_client.get_blob_client(question_blob_name)

            question_data = download_blob(question_blob_client)
            if question_data:
                return JsonResponse(question_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def download_blob(blob_client):
    try:
        blob_content = blob_client.download_blob().readall()
        return json.loads(blob_content)
    except Exception as e:
        return None

@api_view(['POST'])
def get_content_for_subtopic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subtopic_id = data.get('subtopic_id')
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

@api_view(['POST'])
def content(request):
    if request.method == 'POST':
        subtopic_id = request.POST.get('subtopic_id')
        content_type = request.POST.get('type')
        if not subtopic_id or not content_type:
            return JsonResponse({'error': 'All fields are required!'}, status=400)
        subject_id = subtopic_id[:2]
        topic_id = subtopic_id[:-2]
        subtopic_folder = f"subjects/{subject_id}/{topic_id}/{subtopic_id}/"
        content_folder = subtopic_folder + "content/"
        asset_folder = subtopic_folder + "content/asset/"
        content_filename = f"{subtopic_id}.json"
        content_blob_name = content_folder + content_filename
        content_blob_client = container_client.get_blob_client(content_blob_name)
        try:
            existing_content = json.loads(content_blob_client.download_blob().readall())
        except:
            existing_content = {'files': {}, 'videos': {}}
        existing_assets = set()
        try:
            blobs = container_client.list_blobs(name_starts_with=asset_folder)
            for blob in blobs:
                existing_assets.add(blob.name)
        except:
            pass
        content_data = {
            'files': {},
            'videos': {}
        }
        present_files = {}
        file_count = 1
        for key in request.POST:
            if key.startswith('files[') and key.endswith('][text]'):
                file_index = key.split('[')[1].split(']')[0]
                file_key = f'files[{file_index}][file]'
                path_key = f'files[{file_index}][path]'  
                text = request.POST.get(f'files[{file_index}][text]')
                time = request.POST.get(f'files[{file_index}][time]')
                level = request.POST.get(f'files[{file_index}][level]')
                old_path = request.POST.get(path_key)  
                if file_key in request.FILES:
                    present_files[file_index] = {
                        'file': request.FILES[file_key],
                        'text': text,
                        'time': time,
                        'level': level,
                        'is_new': True,
                        'old_path': old_path 
                    }
                elif old_path:  
                    present_files[file_index] = {
                        'path': old_path,
                        'text': text,
                        'time': time,
                        'level': level,
                        'is_new': False
                    }
                elif file_index in existing_content.get('files', {}):
                    present_files[file_index] = {
                        'path': existing_content['files'][file_index]['path'],
                        'text': text,
                        'time': time,
                        'level': level,
                        'is_new': False
                    }
        kept_assets = set()
        assets_to_delete = set()
        for original_index in sorted(present_files.keys()):
            file_entry = present_files[original_index]
            new_file_key = f'file{file_count}'

            if file_entry.get('is_new', False):
                if file_entry.get('old_path'):
                    old_filename = file_entry['old_path'].split('/')[-1]
                    old_asset = asset_folder + old_filename
                    assets_to_delete.add(old_asset)
                file_obj = file_entry['file']
                file_extension = os.path.splitext(file_obj.name)[1]
                asset_filename = f"{subtopic_id}{file_count:02}{file_extension}"
                asset_blob_name = asset_folder + asset_filename
                asset_blob_client = container_client.get_blob_client(asset_blob_name)
                file_path = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{asset_blob_name}"

                asset_blob_client.upload_blob(file_obj, overwrite=True)
                kept_assets.add(asset_blob_name)

                content_data['files'][new_file_key] = {
                    'path': file_path,
                    'text': file_entry['text'],
                    'time': file_entry['time'],
                    'level': file_entry['level']
                }
            else:
                old_path = file_entry['path']
                old_filename = old_path.split('/')[-1]
                new_filename = f"{subtopic_id}{file_count:02}{os.path.splitext(old_filename)[1]}"
                new_blob_name = asset_folder + new_filename
                new_path = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{new_blob_name}"

                if old_filename != new_filename:
                    try:
                        old_blob_name = asset_folder + old_filename
                        source_blob = container_client.get_blob_client(old_blob_name)
                        target_blob = container_client.get_blob_client(new_blob_name)
                        target_blob.start_copy_from_url(source_blob.url)
                        assets_to_delete.add(old_blob_name)
                    except Exception as e:
                        print(f"Error renaming blob: {str(e)}")
                kept_assets.add(new_blob_name)
                content_data['files'][new_file_key] = {
                    'path': new_path,
                    'text': file_entry['text'],
                    'time': file_entry['time'],
                    'level': file_entry['level']
                }

            file_count += 1
        temp_videos = []
        for key, value in request.POST.items():
            if key.startswith('videos[') and key.endswith('][path]'):
                video_index = key.split('[')[1].split(']')[0]
                path = value
                text = request.POST.get(f'videos[{video_index}][text]')
                time = request.POST.get(f'videos[{video_index}][time]')
                level = request.POST.get(f'videos[{video_index}][level]')
                if path and text and time and level:
                    temp_videos.append({
                        'path': path,
                        'text': text,
                        'time': time,
                        'level': level,
                    })
        for i, video in enumerate(temp_videos, 1):
            content_data['videos'][f'video{i}'] = video
        for asset_path in existing_assets:
            if asset_path not in kept_assets or asset_path in assets_to_delete:
                try:
                    blob_client = container_client.get_blob_client(asset_path)
                    blob_client.delete_blob()
                except Exception as e:
                    print(f"Error deleting blob {asset_path}: {str(e)}")
        content_blob_client.upload_blob(json.dumps(content_data), overwrite=True)
        subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
        subtopic.notes = len(content_data['files'])
        subtopic.videos = len(content_data['videos'])
        subtopic.save()

        return JsonResponse({'message': 'Content updated successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


