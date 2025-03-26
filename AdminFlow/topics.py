from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
import AdminFlow.course as course

@api_view(['GET'])
def subjects_for_topics(request,track_id):
    try:
    
        subjects_list=[]
        track_instance=tracks.objects.get(track_id=track_id)
        all_subjects=subjects.objects.filter(del_row=False,track_id=track_instance)
        for subject in all_subjects:
            subject_data={
                'subject_id':subject.subject_id,
                'subject_name':subject.subject_name
            }
            subjects_list.append(subject_data)
        return JsonResponse({'subjects': subjects_list})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
def get_all_topics(request,subject_id):
    try:
        topics_list=[]
        subject_instance=subjects.objects.get(subject_id=subject_id)
        all_topics=topics.objects.filter(del_row=False,subject_id=subject_instance)
        for topic in all_topics:
            topic_data={
                'topic_id':topic.topic_id,
                'topic_name': topic.topic_name,
                'topic_alt_name':topic.topic_alt_name,
                'topic_description':topic.topic_description,
                'subject_id':topic.subject_id.subject_id,
                'subject_name':topic.subject_id.subject_name
            }
            topics_list.append(topic_data)
        return JsonResponse({'topics': topics_list})
    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)
    
@api_view(['POST'])
def create_topic(request):
    if request.method=="POST":
        try:
            data=json.loads(request.body)
            topic_name=data['topic_name']
            topic_alt_name=data['topic_alt_name']
            topic_description=data['topic_description']
            subject_id=data['subject_id']
            subject_instance=subjects.objects.get(subject_id=subject_id)
            if(data['topic_id']==''):
                prefix = subject_id
                now = datetime.utcnow() + timedelta(hours=5, minutes=30)
                current_date = now.strftime("%y%m%d")
                latest_topic = topics.objects.filter(
                    topic_id__startswith=f'{prefix}{current_date}'
                ).order_by('-topic_id').first()

                if latest_topic:
                    latest_time = latest_topic.topic_id[-4:]  
                    latest_hour = int(latest_time[:2])
                    latest_minute = int(latest_time[2:])
                    start_hour = latest_hour
                    start_minute = latest_minute + 1
                    if start_minute >= 60:
                        start_hour += 1
                        start_minute = 0
                    if start_hour >= 24:
                        start_hour = 0
                else:
                    start_hour = now.hour
                    start_minute = now.minute

                created_topics = []
                for i, topic_name in enumerate([topic_name]):
                    current_minute = start_minute + i
                    current_hour = start_hour
                    if current_minute >= 60:
                        current_hour += 1
                        current_minute = current_minute % 60
                    if current_hour >= 24:
                        current_hour = current_hour % 24
                    topic_id = f'{prefix}{current_date}{current_hour:02d}{current_minute:02d}'.lower()

                topic=topics(
                topic_id=topic_id,
                topic_name=topic_name,
                topic_description=topic_description,
                topic_alt_name=topic_alt_name,
                subject_id=subject_instance,
                created_by=data['by'],
                created_at=course.get_ist_time()
            )
                topic.save()
            else:
                topic_id=data['topic_id']
                topic=topics.objects.get(topic_id=topic_id)
                topic.topic_name=topic_name
                topic.topic_description=topic_description
                topic.subject_id=subject_instance
                topic.topic_alt_name= topic_alt_name
                topic.modified_at=course.get_ist_time()
                topic.modified_by=data['by']
                topic.save()            
            return JsonResponse({'message':"Topic created / updated successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            
@api_view(['POST'])
def delete_topic(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            topic_id=data['topic_id']
            topic= topics.objects.get(topic_id=topic_id)
            topic.del_row=True
            topic.save()
            return JsonResponse({'message':'Topic deleted successfully'})
        except Exception as e:
            return JsonResponse({'error':str(e)}, status=500)