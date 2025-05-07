from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from LMS_Project.settings import *
from datetime import datetime, timedelta
import string
import AdminFlow.course as course
from django.db.models import Count, Prefetch,Q
from azure.storage.blob import ContentSettings
import os
from azure.storage.blob import BlobServiceClient
import AdminFlow.course as course
blob_service_client = BlobServiceClient(account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/",credential=AZURE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

@api_view(['POST'])
def update_weekend_holidays(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            batch_id = data.get("batch_id")
            saturday = data.get("saturday")
            sunday = data.get("sunday")
            hours = data.get("hours") 
            if batch_id is None or saturday is None or sunday is None:
                return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)
            try:
                batch = batches.objects.get(batch_id=batch_id)
            except batches.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Batch not found"}, status=404)
            batch.saturday_holiday = saturday  
            batch.sunday_holiday = sunday  
            batch.hours_per_day = hours
            batch.save()
            return JsonResponse({"status": "ok", "message": "Weekend settings updated successfully"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@api_view(['GET'])
def get_weekend_settings(request,batch_id):
    if not batch_id:
        return JsonResponse({"status": "error", "message": "batch_id parameter is required"}, status=400)

    try:
        batch = batches.objects.get(batch_id=batch_id)
        response_data = {
            "status": "ok",
            "saturday": batch.saturday_holiday,  
            "sunday": batch.sunday_holiday ,
            "hours": batch.hours_per_day        
        }

        return JsonResponse(response_data)
    except batches.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Batch not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@api_view(['GET'])
def is_batch_in_blob(request, course, batch):
    try:
        blob_name = f"lms_daywise/{course}/{course}_{batch}.json"
        blob_client = container_client.get_blob_client(blob_name)
        if blob_client.exists():
            return JsonResponse({'exists': True, 'message': f'File "{blob_name}" exists in blob storage.'})
        else:
            return JsonResponse({'exists': False, 'message': f'File "{blob_name}" does not exist in blob storage.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def get_batch_daywise_json(request, course, batch):
    try:
        blob_name = f"lms_daywise/{course}/{course}_{batch}.json"
        blob_client = container_client.get_blob_client(blob_name)

        if blob_client.exists():
            blob_data = blob_client.download_blob().readall()
            json_data = json.loads(blob_data)

            return JsonResponse({
                'exists': True,
                'data': json_data,
                'message': f'File "{blob_name}" exists and was retrieved.'
            }, safe=False)
        else:
            return JsonResponse({
                'exists': False,
                'message': f'File "{blob_name}" does not exist in blob storage.'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

