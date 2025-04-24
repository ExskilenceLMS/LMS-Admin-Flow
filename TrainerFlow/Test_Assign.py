from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details,courses as course_model,batches as batch_model
from LMS_MSSQLdb_App.models import students_info as student_model, students_assessments 
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
def get_tests_details(request):
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

        tests = test_details.objects.filter(**filters,del_row=False)
        test_data = []
        for test in tests:
            date_value = test.test_date_and_time if test.test_date_and_time else datetime.now()
            date_value = date_value.replace(tzinfo=None)
            if date_value <= datetime.now()  :
                test_data.append({
                'test_id': test.test_id,
                'title': test.test_name,
                'description': test.test_description,
                'duration': test.test_duration,
                'marks': test.test_marks,
                'subject': test.subject_id.subject_name if test.subject_id else None,
                'date': test.test_date_and_time.date() if test.test_date_and_time else None,
                'time': test.test_date_and_time.time()  if test.test_date_and_time else None,
                'track': test.track_id.track_name if test.track_id else None,
                'course': test.course_id.course_name if test.course_id else None,
                'test_type': test.test_type if test.test_type else None

                })
        return JsonResponse(test_data, safe=False)
    except Exception as e:
        print(e)
        return JsonResponse({"error": str(e)}, status=500)
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
        test.save()
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
def get_students(request,course,batch,testID):
    try:
        students = list(student_model.objects.filter(batch_id__batch_name=batch,course_id__course_name=course,del_row=False).values(
                                        'student_id','student_firstname','student_lastname','student_type','college','branch'))
        assigned_students = list(students_assessments.objects.filter(test_id=testID,del_row=False).values('student_id'))
        response ={
            'students':students,
            'assigned_students_ids':[i.get('student_id') for i in assigned_students]
        }
        return JsonResponse(response,safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def assign_tests(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.get(test_id = data.get('test_id'),del_row = False)
        assigned_students = data.get('assigned_students_ids',[])
        old_Std = students_assessments.objects.filter(test_id=test.test_id) 
        all_stds =student_model.objects.filter(del_row=False)
        all_stds = {std.student_id:std for std in all_stds}
        del_std =[]
        update_oldStudents =[]
        std_obj =[]
        for std in data.get('students_list',[]):
            if std in assigned_students:
                assigned_students.remove(std)
                continue
            if std in [i.student_id.student_id for i in old_Std]:
                 for i in old_Std:
                    if i.student_id.student_id == std:
                        i.del_row = False
                        del_std.append(i)
                 continue
            student_test = students_assessments(
                student_id = all_stds.get(std),
                assessment_type = test.test_type,
                subject_id = test.subject_id,
                test_id = test,
                course_id = test.course_id,
                assessment_status ='P',
                assessment_score_secured = 0,
                assessment_max_score = test.test_marks
            )
            std_obj.append(student_test)
        if data.get('students_list',[]) == []:
            for std in old_Std:
                std.del_row = True
                del_std.append(std)
        if len(std_obj) != 0:
            assigned = students_assessments.objects.bulk_create(std_obj)
        if len(assigned_students) != 0:
            for std in old_Std:
                if std.student_id.student_id in assigned_students:
                    std.del_row = True
                del_std.append(std)
        if len(del_std) != 0:
            # students_assessments.objects.using('mongodb').bulk_update(del_std,fields=['del_row'])
            for std in del_std:
                std.save()
        return JsonResponse({"status": "success"})
    except Exception as e :
        print(e)
        return JsonResponse({'error':str(e)})