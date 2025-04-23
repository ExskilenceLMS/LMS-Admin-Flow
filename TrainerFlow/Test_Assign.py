from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details,courses as course_model,batches as batch_model
from LMS_MSSQLdb_App.models import students_info as student_model
from LMS_Mongodb_App.models import students_assessments 
@api_view(['GET'])
def filter_for_assign_tests(request):
    try:
        tracks  = list(track_model.objects.filter(del_row=False))
        courses = list(course_model.objects.filter(del_row=False))
        subjects = list(subject_model.objects.filter(del_row=False))
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
def update_test_details(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.get(test_id = data.get('test_id'),del_row = False)
        test.test_type = data.get('test_type')
        test.track_id = track_model.objects.get(track_name = data.get('track'),del_row = False)
        test.course_id = course_model.objects.get(course_name = data.get('course'),del_row = False)
        test.subject_id = subject_model.objects.get(subject_name = data.get('subject'),del_row = False)
        test.test_date_and_time = datetime.strptime(data.get('date'), '%Y-%m-%d').__add__(timedelta(days=0, hours=int(data.get('time').split(':')[0]), minutes=int(data.get('time').split(':')[1]), seconds= int(data.get('time').split(':')[2])))
        # test.save()
        return JsonResponse({'message':'success'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['GET'])
def filter_for_sorting_students(request,track):
    try:
        courses = list(course_model.objects.filter(tracks__contains=track,del_row=False))
        batches = list(batch_model.objects.filter(course_id__tracks__contains=track,del_row=False))

        return JsonResponse({
            'courses': {
                        course.course_name:[
                            batche.batch_name for batche in batches if batche.course_id.course_name == course.course_name
                                           ] for course in courses                   
            },
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['GET'])
def get_students(request,course,batch):
    try:
        students = list(student_model.objects.filter(batch_id__batch_name=batch,course_id__course_name=course,del_row=False).values(
                                        'student_id','student_firstname','student_lastname','student_type','college','branch'))
        return JsonResponse(students,safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def assign_tests(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.get(test_id = data.get('test_id'),del_row = False)
        print("test.subject_id",test.subject_id)
        std_obj =[]
        for std in data.get('students_list',[]):
            student_test = students_assessments(
                student_id = std,
                assessment_type = test.test_type,
                subject_id = test.subject_id.subject_id,
                test_id = test.test_id,
                course_id = test.course_id,
                assessment_status ='P',
                assessment_score_secured = 0,
                assessment_max_score = test.test_marks
            )
            std_obj.append(student_test)
        assigned = students_assessments.objects.bulk_create(std_obj)
        return JsonResponse({"status": "success"})
    except Exception as e :
        print(e)
        return JsonResponse({'erroe':str(e)})