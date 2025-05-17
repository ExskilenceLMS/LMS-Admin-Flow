import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from django.db.models import F
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
def LiveUsers(request):
    try:
        now = timezone.now().__add__(timedelta(hours=5,minutes=30))
        min_now = now.__add__(timedelta(minutes=-5))
        max_now = now.__add__(timedelta(minutes=+15))
        users = student_app_usage.objects.filter(logged_out__gte=min_now,logged_out__lte=max_now,del_row=False). annotate(user_id=F('student_id__student_id'),last_updated=F('logged_out')).\
            values('user_id','student_id__student_firstname','student_id__student_lastname','logged_in','last_updated').distinct().order_by('-last_updated')
        counts =[]
        users_details = []
        for user in users:
            if user['user_id'] not in counts:
                counts.append(user['user_id'])  
                users_details.append(user)
        return JsonResponse({"Count":len(counts),"data":list(users_details)},status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message":"Failed","error":str(e)},status=400)