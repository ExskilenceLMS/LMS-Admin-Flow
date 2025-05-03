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

