from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details,courses as course_model,batches as batch_model
from LMS_MSSQLdb_App.models import students_info as student_model,students_assessments 
from django.db.models import Count
from LMS_MSSQLdb_App.models import *
@api_view(['GET'])
def filter_for_Test_Report(request):
    try:
        tracks   = list(track_model.objects.filter(del_row=False))
        courses  = list(course_model.objects.filter(del_row=False))
        subjects = list(subject_model.objects.filter(del_row=False))
        topics   = list(topic_model.objects.filter(del_row=False))
        batchs   = list(batch_model.objects.filter(del_row=False))
        LiveorCompleted = ['Live','Completed']
        Colleges = list(college_details.objects.filter(del_row=False))
        branchs  = list(branch_details.objects.filter(del_row=False))
        student_type = ['Swapnodaya','Exskilence']
        Test_type = list(test_details.objects.filter(del_row=False).values_list('test_type',flat=True).distinct())
        return JsonResponse({
            'courses': {
               track.track_name:{
                        course.course_name:[
                            subject.subject_name for subject in subjects if subject.track_id.track_name == track.track_name
                                           ] for course in courses if course.tracks.split(",").count(track.track_name)>0
                                } for track in tracks
            },
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def get_tests_Report_details(request):
    try:
        data = json.loads(request.body)
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

        tests = test_details.objects.filter(**filters,test_date_and_time__lte=datetime.now(),del_row=False)
        test_ids = [test.test_id for test in tests]
        Invited = students_assessments.objects.filter(test_id__in=test_ids,del_row='False'
                                                                       ).values('test_id').annotate(count=Count('test_id'))
        Invited = {test.get('test_id'):test.get('count') for test in Invited}
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
                'from_time': test.test_date_and_time.time()  if test.test_date_and_time else None,
                'end_time': test.test_date_and_time.__add__(timedelta(minutes=int(test.test_duration))).time()  if test.test_date_and_time else None,
                'track': test.track_id.track_name if test.track_id else None,
                'course': test.course_id.course_name if test.course_id else None,
                'test_type': test.test_type if test.test_type else None,
                'invited':Invited.get(test.test_id,0),

            })
        return JsonResponse(test_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)