from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import HttpResponse
@api_view(['GET'])
def hello(request):
    return HttpResponse({'hello': 'world'})
