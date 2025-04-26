from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
from LMS_Mongodb_App.models import *
from AdminFlow.collegeBranch import generate_id
    
@api_view(['POST'])
def get_students_for_session(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            batch_id=data['batch_id']
            batch_instance = batches.objects.get(batch_id=batch_id)
            course_id=data['course_id']
            course_instance = courses.objects.get(course_id=course_id)
            all_students = students_info.objects.filter(del_row=False, batch_id=batch_instance, course_id =course_instance   )  
            students_list = []
            for student in all_students:
                student_data =  {
                    "student_id": student.student_id,
                    "student_firstname": student.student_firstname,
                    "student_lastname": student.student_lastname,
                    "student_email": student.student_email,
                    "phone": student.phone,
                    "college": student.college,
                    "branch": student.branch,
            }
                students_list.append(student_data)
            return JsonResponse({'students': students_list,'max':batch_instance.max_no_of_students})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
