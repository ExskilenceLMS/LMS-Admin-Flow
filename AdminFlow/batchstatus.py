from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
from LMS_Project.settings import *
from azure.storage.blob import BlobServiceClient

blob_service_client = BlobServiceClient(account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/",credential=AZURE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

@api_view(['GET'])
def get_subject_for_batch(request, course, batch):
    try:
        path = f'lms_daywise/{course}/{course}_{batch}.json'
        print(path)
        blob_client = container_client.get_blob_client(path)
        download_stream = blob_client.download_blob()
        json_data = download_stream.readall()
        parsed_data = json.loads(json_data)
        print(parsed_data.keys())
        all_subjects=list(parsed_data.keys())
        return JsonResponse({'subjects': all_subjects})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_batch_daywise(request, course, batch,subject):
    try:
        path = f'lms_daywise/{course}/{course}_{batch}.json'
        blob_client = container_client.get_blob_client(path)
        download_stream = blob_client.download_blob()
        json_data = download_stream.readall()
        parsed_data = json.loads(json_data)
        subject_id=subjects.objects.filter(subject_name=subject,del_row=False).first()
        print(subject_id.subject_id)
        data = fetch_roadmap(course,subject_id.subject_id,batch)
        print('sdfcgvbnm,kjgfc',data)
        return JsonResponse({'weeks':data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


import calendar
from itertools import count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
import json
from django.db.models.functions import TruncDate
from django.core.cache import cache

def get_day_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

def format_date_with_suffix(date_obj):
    try:
        day = date_obj.day
        suffix = get_day_suffix(day)
        month_year = date_obj.strftime("%b %y")  
        return f"{day}{suffix} {month_year}"
    except Exception as e:
        print("Date formatting error:", e)
        return str(date_obj)

def fetch_roadmap(course_id, subject_id, batch_id):
    try:
        course = courses.objects.get(del_row=False, course_id=course_id)
        batch = batches.objects.get(del_row=False, batch_id=batch_id)
        subject = subjects.objects.get(del_row=False, subject_id=subject_id)
        db_entries = course_plan_details.objects.filter(
            course_id=course,
            subject_id=subject,
            batch_id=batch,
            del_row=False
        ).order_by('week', 'day')
        path = f'lms_daywise/{course.course_id}/{course.course_id}_{batch.batch_id}.json'
        blob_client = container_client.get_blob_client(path)
        download_stream = blob_client.download_blob()
        json_data = json.loads(download_stream.readall())
        subject_key = subject.subject_name.replace(" ", "")
        daywise_data = json_data.get(subject_key, [])
        blob_by_date = {d["date"]: d for d in daywise_data}

        week_map = {}

        for entry in db_entries:
            week = entry.week
            date_key = entry.day_date.strftime("%Y-%m-%d")
            blob_day = blob_by_date.get(date_key, {})

            if week not in week_map:
                week_map[week] = {
                    "weekNumber": week,
                    "startDate": entry.day_date,
                    "endDate": entry.day_date,
                    "totalHours": 0,
                    "days": []
                }

            week_data = week_map[week]
            week_data["startDate"] = min(week_data["startDate"], entry.day_date)
            week_data["endDate"] = max(week_data["endDate"], entry.day_date)
            week_data["totalHours"] += entry.duration_in_hours or 0
            formatted_date = format_date_with_suffix(entry.day_date)
            def get_total_questions(data):
                if not isinstance(data, dict):
                    return "0/0"
                total = sum(sum(v.values()) for v in data.values())
                return f"{total}"

            day_data = {
                "day": entry.day,
                "date": formatted_date,
                "topics": blob_day.get("topic", entry.content_type),
                "practiceMCQ": {
                    "questions": get_total_questions(blob_day.get("mcq"))
                },
                "practiceCoding": {
                    "questions": get_total_questions(blob_day.get("coding"))
                },
            }
            week_data["days"].append(day_data)
        weeks = sorted(week_map.values(), key=lambda w: w["weekNumber"])
        for w in weeks:
            w["startDate"] = format(w['startDate'], "%d-%m-%Y")
            w["endDate"] =  format(w['endDate'], "%d-%m-%Y")
        return weeks
    except Exception as e:
        print("Error:", e)
        return JsonResponse({"error": str(e)}, status=500)
