import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details
from django.db.models import F

# Create your views here.
@api_view(['GET'])
def trainer_Admin_Login(request,mail):
    try:
        
        User  = suite_login_details.objects.get(user_email = mail)
        if User is None:
            return JsonResponse({'error': 'User not found'}, status=404)
        response = {
            'user_id': User.user_id,
            'name': User.user_first_name+' '+User.user_last_name,
            'category': User.category
        }
        return JsonResponse(response, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'User not found'}, status=500)
@api_view(['GET'])  
def get_filter_options(request):
    try:
        tracks  = list(track_model.objects.filter(del_row=False))
        subjects = list(subject_model.objects.filter(del_row=False))
        topics = list(topic_model.objects.filter(del_row=False)) 
        tests = list(test_details.objects.all())
        filter_options = {
            'tracks':  [ track.track_name for track in tracks],  
            'subjects': {
                track.track_name:[subject.subject_name for subject in subjects if subject.track_id.track_name == track.track_name] for track in tracks
            },
            'topics': {
                track.track_name:{subject.subject_name:[topic.topic_name for topic in topics if topic.subject_id.subject_name == subject.subject_name] for subject in subjects if subject.track_id.track_name == track.track_name} for track in tracks
            },
            'tags': [],
            'levels': [],
            'marks': [],
            'duration':[]

            # 'subjects': {
            #     track.track_name:[subject.subject_name for subject in subjects if subject.track_id.track_name == track.track_name] for track in tracks
            # 'topics': {
            #     subject.subject_name:[topic.topic_name for topic in topics if topic.subject_id.subject_name == subject.subject_name] for subject in subjects
            # },
            # 'tags': [
            #     test.tags for test in tests
            # ],
            # 'levels': [
            #     test.level for test in tests if test.level is not None ]
            }
        for test in tests:
            if test.tags is not None and test.tags not in filter_options.get('tags', []):
                filter_options.get('tags').append(test.tags)
            if test.level is not None and test.level not in filter_options.get('levels', []):
                filter_options.get('levels').append(test.level)
            if test.test_marks is not None and test.test_marks not in filter_options.get('marks', []):
                filter_options.get('marks').append(test.test_marks)
            if test.test_duration is not None and test.test_duration not in filter_options.get('duration', []):
                filter_options.get('duration').append(test.test_duration)
        return JsonResponse(filter_options, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)