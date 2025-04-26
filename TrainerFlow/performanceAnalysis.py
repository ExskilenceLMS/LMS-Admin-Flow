import json
from django.http import JsonResponse
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from rest_framework.decorators import api_view
from django.db.models.functions import Concat
from django.db.models import Sum, F,ExpressionWrapper, DurationField
@api_view(['GET'])
def filter_for_performanceAnalysis(request):
    try:
        Courses = courses.objects.filter(del_row=False)
        batch_list = batches.objects.filter(del_row=False)
        subject_list = course_subjects.objects.filter(del_row=False)
        data = {
            'Courses'   :[ course.course_name for course in Courses],
            'batchs'    :{
                course.course_name:[batch.batch_name for batch in batch_list if batch.course_id.course_name == course.course_name] for course in Courses
            },
            'subjects'  :{ 
                course.course_name:{
                    batch.batch_name:[subject.subject_id.subject_name for subject in subject_list if subject.course_id.course_name == batch.course_id.course_name] for batch in batch_list
                } for course in Courses
            }
        }
        return JsonResponse(data)
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
        students_app_usage = student_app_usage.objects.filter(
                    student_id__in=[stud.student_id for stud in student],
                    del_row=False
                ).annotate(
                    duration=ExpressionWrapper(F('logged_out') - F('logged_in'), output_field=DurationField())
                ).values('student_id').annotate(
                    total_study_hours=Sum('duration')
                ).order_by('student_id')
        students_app_usage = {stud.get('student_id'):stud.get('total_study_hours').total_seconds() for stud in students_app_usage}
        print(students_app_usage)
        response = []
        [response.append({
            'ID'            :stud.student_id,    
            'Name'          :stud.student_firstname+" "+stud.student_lastname,
            'Student_Type'  :stud.student_type,
            'College'       :stud.college,
            'Branch'        :stud.branch,
            'Mobile'        :stud.phone,
            'Score'         :str(stud.student_score)+'/'+str(stud.student_total_score),
            'Catogory'      :stud.student_catogory,
            'College_Rank'  :stud.student_college_rank,    
            'Overall_Rank'  :stud.student_overall_rank,    
            'Email'         :stud.student_email,
            'No_of_hours'   :students_app_usage.get(stud.student_id)
                          }) for stud in student]  , 
        Student_details = students_details.objects.using('mongodb').filter(**student_filters,del_row=False)
        [data.update({'student_id':student_data.student_question_details}) for student_data in Student_details]
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)