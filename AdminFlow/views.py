from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import HttpResponse,JsonResponse
from datetime import datetime, timedelta

ONTIME = datetime.utcnow().__add__(timedelta(hours=5,minutes=30))
@api_view(['GET'])  
def home(request):
    return JsonResponse({"message": "Successfully Deployed LMS Admin Flow on Azure at "+ str()},safe=False,status=200)
