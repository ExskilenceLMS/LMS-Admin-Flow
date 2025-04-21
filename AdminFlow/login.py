from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import  JsonResponse
from datetime import datetime, timedelta
from AdminFlow.course import get_ist_time

@api_view(['GET'])
def login(request,mail):
    try:
        user = suite_login_details.objects.get(user_email=mail, del_row=False)
        if user:
            exists=True
            access=user.access
        else:
            exists=False
            access=[]
        return JsonResponse({'Type': user.category,'exists':exists,'access':access , 'Name': user.user_first_name+" "+user.user_last_name}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(["POST"])
def add_staff(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            exist=suite_login_details.objects.filter(user_email=data["user_email"]).first()
            if exist:
                user=suite_login_details.objects.get(user_email=data['user_email'])
                user.user_first_name=data.get('user_first_name', user.user_first_name)
                user.user_last_name=data.get('user_last_name', user.user_last_name)
                user.user_email=data.get('user_email', user.user_email)
                user.phone=data.get('phone', user.phone)
                user.category=data.get('category', user.category)
                user.access=data.get('access',user.access)
                user.save()
            else:
                existing_users_count = suite_login_details.objects.count() + 1
                user_id = f'user{existing_users_count}'  
                user = suite_login_details(
                    user_id=user_id,
                    user_first_name=data['user_first_name'],
                    user_last_name=data["user_last_name"],
                    user_email=data['user_email'],
                    phone=data['phone'],
                    category=data['category'],
                    reg_date=get_ist_time(),
                    access=data['access'],
                    exp_date=get_ist_time()+timedelta(days=365)
                )
                user.save()  
            
            return JsonResponse({'message': 'User created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)