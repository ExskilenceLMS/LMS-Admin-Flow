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
def fetch_rules(request):
    path='lms_rules/rules.json'
    try:
        blob_client = container_client.get_blob_client(path)
        download_stream = blob_client.download_blob()
        json_data = download_stream.readall()
        return HttpResponse((json_data), content_type='application/json')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def update_rules(request):
    try:
        data = json.loads(request.body)
        path='lms_rules/rules.json'
        blob_client = container_client.get_blob_client(path)
        blob_client.upload_blob(json.dumps(data), overwrite=True)
        return JsonResponse({'message': 'Rules updated successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    