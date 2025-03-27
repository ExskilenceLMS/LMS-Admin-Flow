from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import  JsonResponse
from datetime import datetime, timedelta
from .course import get_ist_time
@api_view(['GET'])
def login(request,mail):
    try:
        admin = admins.objects.get(admin_email=mail, del_row=False)
        if admin:
            exists=True
        else:
            exists=False
        return JsonResponse({'Type': admin.category,'exists':exists }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(["POST"])
def add_admin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            exist=admins.objects.filter(admin_email=data["admin_email"]).first()
            if exist:
                admin=admins.objects.get(admin_email=data['admin_email'])
                admin.admin_first_name=data.get('admin_first_name', admin.admin_first_name)
                admin.admin_last_name=data.get('admin_last_name', admin.admin_last_name)
                admin.admin_email=data.get('admin_email', admin.admin_email)
                admin.phone=data.get('phone', admin.phone)
                admin.category=data.get('category', admin.category)
                admin.save()
            else:
                existing_admins_count = admins.objects.count() + 1
                admin_id = f'admin{existing_admins_count}'  
                admin = admins(
                    admin_id=admin_id,
                    admin_first_name=data['admin_first_name'],
                    admin_last_name=data["admin_last_name"],
                    admin_email=data['admin_email'],
                    phone=data['phone'],
                    category=data['category'],
                    reg_date=get_ist_time(),
                    exp_date=get_ist_time() + timedelta(days=365),
                )
                admin.save()  
            
            return JsonResponse({'message': 'Admin created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)