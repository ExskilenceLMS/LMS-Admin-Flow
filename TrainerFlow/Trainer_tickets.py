import calendar
from itertools import count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max, F ,Sum,Min,Count
# from django.contrib.postgres.aggregates import ArrayAgg
import json
from django.db.models.functions import TruncDate
from django.core.cache import cache

@api_view(['GET'])
def fetch_all_tickets(request):
    try:
        tickets = list(issue_details.objects.using('mongodb').filter(del_row = 'False').order_by('-reported_time').values())
        print(len(tickets))
        return JsonResponse({'ticket_details':tickets},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
@api_view(['GET'])
def fetch_student_tickets(request,student_id):
    try:
        tickets = list(issue_details.objects.using('mongodb').filter(student_id = student_id,del_row = 'False').order_by('-reported_time').values())
        return JsonResponse({'ticket_details':tickets},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
@api_view(['PUT']) 
def trainer_side_comments_for_tickets(request):
    try:
        data = json.loads(request.body)
        ticket = issue_details.objects.using('mongodb').get(sl_id = data.get('t_id'),del_row = 'False')
        keys = sorted([int(str(tk).replace('tra','')) for tk in ticket.comments if str(tk).startswith('tra')])
        print(keys[-1]+1 if len(keys)>0 else [0] )
        ticket.comments.update({
            "tra"+str(keys[-1]+1 if len(keys)>0 else 1): {
                    "role": "trainer",
                    'Trainer_id': data.get('trainer_id'),
                    "comment": data.get('comment'),
                    "timestamp": timezone.now() + timedelta(hours=5, minutes=30)
                    },})
        ticket.save()
        responnse=ticket.comments
        return JsonResponse({'message':responnse},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)