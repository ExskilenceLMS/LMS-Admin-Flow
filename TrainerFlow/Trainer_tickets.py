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
from collections import defaultdict
from datetime import datetime
@api_view(['GET'])
# def fetch_all_tickets(request):
#     try:
#         tickets = list(issue_details.objects.using('mongodb').filter(del_row = 'False').order_by('-reported_time').values())
#         print(len(tickets))
#         return JsonResponse({'ticket_details':tickets},safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

def fetch_all_tickets(request):
    try:
        tickets = issue_details.objects.using('mongodb').filter(del_row='False').order_by('-reported_time')

        student_data = defaultdict(list)
        for ticket in tickets:
            student_data[ticket.student_id].append(ticket)

        result = []

        for student_id, issues in student_data.items():
            total_issues = len(issues)
            student_instance=students_info.objects.get(student_id=student_id)
            print(student_instance)
            resolved_issues = sum(1 for issue in issues if issue.issue_status.lower() == 'resolved')
            latest_issue = sorted(issues, key=lambda x: x.reported_time, reverse=True)[0]
            resolved_issues_list = [issue for issue in issues if issue.issue_status.lower() == 'resolved' and issue.resolved_time is not None]
            latest_resolved_issue = sorted(resolved_issues_list, key=lambda x: x.resolved_time, reverse=True)[0] if resolved_issues_list else None
            if student_instance:
                name=student_instance.student_firstname+' '+student_instance.student_lastname 
            else:
                name='Unknown'
            result.append({
                "StudentId": student_id,
                "firstName":name ,  
                "college": student_instance.college,        
                "branch": student_instance.branch,        
                "number_of_issues_reported": total_issues,
                "date_of_issue_reported": latest_issue.reported_time,
                "issue_type": latest_issue.issue_type,
                "date_of_issue_resolved": latest_resolved_issue.resolved_time if latest_resolved_issue else None,
                "status_of_latest_issue": "Resolved" if latest_issue.issue_status.lower() == "resolved" else "Pending",
                "resolution_score": f"{resolved_issues}/{total_issues}"
            })

        return JsonResponse( result, safe=False, status=200)
    
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed", "error": str(e)}, safe=False, status=400)


@api_view(['GET'])
# def fetch_student_tickets(request,student_id):
#     try:
#         tickets = list(issue_details.objects.using('mongodb').filter(student_id = student_id,del_row = 'False').order_by('-reported_time').values())
#         return JsonResponse(tickets,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
    
def fetch_student_tickets(request, student_id):
    try:
        student_instance = students_info.objects.get(student_id=student_id)
        student_name = f"{student_instance.student_firstname} {student_instance.student_lastname}"
        tickets = list(issue_details.objects.using('mongodb')
                       .filter(student_id=student_id, del_row='False')
                       .order_by('-reported_time')
                       .values())
        for ticket in tickets:
            ticket['studentname'] = student_name

        return JsonResponse(tickets, safe=False, status=200)

    except students_info.DoesNotExist:
        return JsonResponse({"message": "Student not found"}, status=404)

    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed", "error": str(e)}, status=400)

@api_view(['PUT']) 
def trainer_side_comments_for_tickets(request):
    try:
        data = json.loads(request.body)
        ticket = issue_details.objects.using('mongodb').get(sl_id = data.get('bug_id'),del_row = 'False')
        keys = sorted([int(str(tk).replace('tra','')) for tk in ticket.comments if str(tk).startswith('tra')])
        print(keys[-1]+1 if len(keys)>0 else [0] )
        ticket.comments.update({
            "tra"+str(keys[-1]+1 if len(keys)>0 else 1): {
                    "role": "trainer",
                    'Trainer_id': data.get('trainer_id'),
                    "comment": data.get('comment'),
                    "timestamp": datetime.utcnow().__add__(timedelta(hours=5,minutes=30))
                    },})
        ticket.save()
        response=ticket.comments
        return JsonResponse({'comments':response},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400) 
    

@api_view(['GET'])
def resolve_ticket(request,ticket_id):
    try:
        ticket = issue_details.objects.using('mongodb').get(sl_id=ticket_id,del_row = 'False')
        ticket.issue_status = 'Resolved'
        ticket.resolved_time = datetime.utcnow().__add__(timedelta(hours=5,minutes=30))
        ticket.save()
        return JsonResponse({'message':'Ticket resolved successfully'},safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
