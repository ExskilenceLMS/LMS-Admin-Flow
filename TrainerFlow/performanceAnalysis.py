import json
from django.http import JsonResponse
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from rest_framework.decorators import api_view
from django.db.models.functions import Concat
from django.db.models import Value

@api_view(['GET'])
def filter_for_performanceAnalysis(request):
    try:
        Courses = courses.objects.filter(del_row=False)
        batch_list = batches.objects.filter(del_row=False)
        data = {
            'Courses':[ course.course_name for course in Courses],
            'batchs':{
                course.course_name:[batch.batch_name for batch in batch_list if batch.course_id.course_name == course.course_name] for course in Courses
            }
        }
        return JsonResponse({'message': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def performanceAnalysis(request):
    try:
        data = json.loads(request.body)
        data = {}
        student_filters = {}
        subject_filters = {} 
        if data.get('course','') != "":
            student_filters.update({'course_id__course_name':data.get('course')})
        if data.get('batch','') != "":
            student_filters.update({'batch_id__batch_name':data.get('batch')})
        if data.get('subject','') != "":
            subject_filters.update({'subject_id__subject_name':data.get('subject')})
        student = list(students_info.objects.filter(**student_filters,del_row=False
                                                    ).annotate(full_name=Concat('student_firstname', Value(' '), 'student_lastname')
                                                               ).values(
            'student_id',
            'full_name',
            'student_type',
            'college',
            'branch',
            'phone',
            'student_score',
            'student_catogory',
            'student_college_rank',
            'student_overall_rank',
            'student_email',
        ))
        return JsonResponse({'message': student})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)