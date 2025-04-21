from django.http import JsonResponse
from rest_framework.decorators import api_view
import json
from LMS_MSSQLdb_App.models import *
@api_view(['POST'])
def test_creation(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.create(
            test_id = 'Test'+str(len(test_details.objects.all())+1) ,#auto generated like test1, test2
            test_name = data.get('test_name'),
            test_description = data.get('description'), 
            test_duration = data.get('duration'),
            test_marks = data.get('marks'),
            test_created_by = data.get('created_by')
        )
        return JsonResponse({"status": "success"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error"})
@api_view(['POST'])
def get_tests_details(request):
    try:
        data = json.loads(request.body)
        if all(data.get(field) == "" for field in ['track', 'subject', 'topic', 'level', 'tags', 'marks', 'duration', 'date']):
            tests = test_details.objects.all()
        else:
            filters = {}

            if data.get('track') != "":
                filters.update({'track_id__track_name':data.get('track')})
            if data.get('subject')!= "":
                filters.update({'subject_id__subject_name':data.get('subject')})
            if data.get('topic')!= "":
                filters.update({'topic_id__in':data.get('topic')})
            if data.get('level')!= "":
                filters.update({'level':data.get('level')})
            if data.get('tags')!= "":
                filters.update({'tags__in':data.get('tags')})
            if data.get('marks')!= "":
                filters.update({'test_marks':data.get('marks')})
            if data.get('duration')!= "":
                filters.update({'test_duration':data.get('duration')})
            if data.get('date')!= "":
                filters.update({'test_date_and_time__date':data.get('date')})

            tests = test_details.objects.filter(**filters)
        test_data = []
        for test in tests:
            test_data.append({
                'test_id': test.test_id,
                'title': test.test_name,
                'description': test.test_description,
                'duration': test.test_duration,
                'marks': test.test_marks,
                'subject': test.subject_id.subject_name if test.subject_id else None,
                'date': test.test_date_and_time.date() if test.test_date_and_time else None,
                'time': test.test_date_and_time.time()  if test.test_date_and_time else None
            })
        return JsonResponse(test_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)