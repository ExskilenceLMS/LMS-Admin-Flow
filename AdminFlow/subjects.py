from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import string
import AdminFlow.course as course

@api_view(['POST'])
def create_subject(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            track_instance=tracks.objects.get(track_id=data['track'])    
            if (data['subject_id']!=''):
                subject = subjects.objects.get(subject_id=data['subject_id'])
                subject.subject_name = data.get('subject_name', subject.subject_name)
                subject.track_id = track_instance
                subject.subject_description = data.get("subject_description", subject.subject_description)
                subject.subject_alt_name=data.get('subject_alt_name',subject.subject_alt_name)
                subject.modified_by = data.get("by", subject.modified_by)
                subject.modified_at = course.get_ist_time()
                subject.save()
            else:
                subject_name = data['subject_name']
                base_id = subject_name[:2].lower()
                new_id = base_id
                while subjects.objects.filter(subject_id=new_id).exists():
                    for char1 in string.ascii_lowercase[string.ascii_lowercase.index(base_id[0]):]:
                        for char2 in string.ascii_lowercase[string.ascii_lowercase.index(base_id[1]):]:
                            new_id = char1 + char2
                            if not subjects.objects.filter(subject_id=new_id).exists():
                                break
                        if not subjects.objects.filter(subject_id=new_id).exists():
                            break 
                subject = subjects(
                    subject_id=new_id,
                    subject_name=subject_name,
                    track_id= track_instance,
                    subject_alt_name=data.get('subject_alt_name', ''),
                    subject_description=data.get('subject_description', ''),
                    created_by=data['by'],
                    created_at=course.get_ist_time()
                )
                subject.save()

            return JsonResponse({'message': "Subject created/updated successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
def get_all_subjects(request):
    try:
        all_subjects= subjects.objects.filter(del_row=False)
        subjects_list=[]
        for subject in all_subjects:
            subject_data={
                'subject_id': subject.subject_id,
                'subject_name':subject.subject_name,
                'track':subject.track_id.track_id,
                'subject_alt_name':subject.subject_alt_name,
                'subject_description':subject.subject_description
            }
            subjects_list.append(subject_data)
        return JsonResponse({'subjects': subjects_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@api_view(['POST'])
def delete_subject(request):
    try:
        data=json.loads(request.body)
        subject=subjects.objects.get(subject_id=data['subject_id'])
        subject.del_row=True
        subject.save()
        return JsonResponse({'message':'Subject deleted successfully'})
    except Exception as e:
        return JsonResponse({"error":str(e)}, status=500)

