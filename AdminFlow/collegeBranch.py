from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
from LMS_Mongodb_App.models import *


@api_view(['POST'])
def add_college(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            if data['college_id']=="":  
                existing_colleges_count = college_details.objects.count() + 1
                college_id = f'college{existing_colleges_count}'  
                college = college_details(
                    college_id=college_id,
                    college_name=data['college_name'],
                    center_name=data['center_name'],
                    college_code=data['college_code']
                )
                college.save()  
            elif 'college_id' in data:
                college = college_details.objects.get(college_id=data['college_id'])
                college.college_name = data.get('college_name', college.college_name)
                college.center_name = data.get('center_name', college.center_name)
                college.college_code = data.get('college_code',college.college_code)
                college.del_row=False
                college.save()  
            return JsonResponse({'message': 'College created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def add_branch(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            if data['branch_id']=="":  
                existing_branchs_count = branch_details.objects.count() + 1
                branch_id = f'branch{existing_branchs_count}'  
                branch = branch_details(
                    branch_id=branch_id,
                    branch=data['branch'],
                    college_id=college_details.objects.get(college_id=data['college_id'])
                )
                branch.save()  
            elif 'branch_id' in data:
                branch = branch_details.objects.get(branch_id=data['branch_id'])
                branch.branch = data.get('branch', branch.branch)
                branch.college_id = data.get(college_details.objects.get(college_id=data['college_id']),branch.college_id)
                branch.del_row=False
                branch.save()  
            return JsonResponse({'message': 'Branch created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def branch_and_college(request):
    try:
        colleges = college_details.objects.all()
        college_data = []

        for college in colleges:
            branches = branch_details.objects.filter(college_id=college.college_id)
            branch_list = [{'branch_id': branch.branch_id, 'branch_name': branch.branch} for branch in branches]

            college_data.append({
                'college_id': college.college_id,
                'college_name': college.college_name,
                'center_name': college.center_name,
                'college_code': college.college_code,
                'branches': branch_list
            })

        return JsonResponse({'colleges': college_data}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_id(college_key, branch_key, category):
    print('functiono call')
    print(college_key,branch_key,category)
    try:
        id_ = str(datetime.now().year)[-2:] + category + college_key + branch_key
        ids = students_info.objects.filter(student_id__startswith=id_).order_by('-student_id').values_list('student_id', flat=True).first()
        if ids is None:
            return id_ + '001'
        sl_id = str(int(str(ids)[-3:]) + 1)
        return id_ + (3 - len(sl_id)) * '0' + sl_id

    except Exception as e:
        print(e)
        return f'not generated {e}'



