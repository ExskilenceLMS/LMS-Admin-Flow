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
        student = students_info.objects.filter(**student_filters,del_row=False)
        response = []
        [response.append({
            'student_id':stud.student_id,    
            'full_name':stud.student_firstname+" "+stud.student_lastname,
            'student_type':stud.student_type,
            'college':stud.college,
            'branch':stud.branch,
            'phone':stud.phone,
            'student_score':stud.student_score,
            'student_catogory': stud.student_catogory,
            'student_college_rank':stud.student_college_rank,    
            'student_overall_rank':stud.student_overall_rank,    
            'student_email':stud.student_email
                          }) for stud in student]   
        Student_details = students_details.objects.using('mongodb').filter(**student_filters,del_row=False)
        [data.update({'student_id':student_data.student_question_details}) for student_data in Student_details]
        return JsonResponse({'message': 'student','data':response})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)