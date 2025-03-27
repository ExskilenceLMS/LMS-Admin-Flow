from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
import AdminFlow.course as course

@api_view(['POST'])
def delete_sub_topic(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            sub_topic_id=data['sub_topic_id']
            sub_topic=sub_topics.objects.get(sub_topic_id=sub_topic_id)
            sub_topic.del_row=True
            sub_topic.save()
            return JsonResponse({'message':'Sub Topic deleted successfully'})
        except Exception as e:
            return JsonResponse({"error":str(e)},status=500)
        
@api_view(['GET'])
def get_all_subTopics(request,topic_id):
    if request.method == "GET":
        try:
            sub_topics_list=[]
            topic_instance=topics.objects.get(topic_id=topic_id)
            all_topics=sub_topics.objects.filter(del_row=False,topic_id=topic_instance)
            for sub_topic in all_topics:
                sub_topic_data={
                    'topic_id':sub_topic.topic_id.topic_id,
                    'topic_name':sub_topic.topic_id.topic_name,
                    'sub_topic_id': sub_topic.sub_topic_id,
                    'sub_topic_name': sub_topic.sub_topic_name,
                    'sub_topic_description': sub_topic.sub_topic_description,
                    'sub_topic_alt_name': sub_topic.sub_topic_alt_name 
                }
                sub_topics_list.append(sub_topic_data)
            return JsonResponse({'sub_topics': sub_topics_list})
        except Exception as e:
            return JsonResponse({"error": str(e)},status=500)

@api_view(['GET'])
def get_topics_for_subject(request,subject_id):
    if request.method == "GET":
        try:
            topics_list=[]
            subject_instance=subjects.objects.get(subject_id=subject_id)
            all_topics=topics.objects.filter(del_row=False,subject_id=subject_instance)
            for topic in all_topics:
                topic_data={
                'topic_id':topic.topic_id,
                'topic_name': topic.topic_name
                }
                topics_list.append(topic_data)
            return JsonResponse({'topics': topics_list})
        except Exception as e:
            return JsonResponse({"error": str(e)},status=500)
        
@api_view(['POST'])
def create_subTopic(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            topic_id=data['topic_id']
            sub_topic_name=data["sub_topic_name"]
            sub_topic_description=data['sub_topic_description']
            sub_topic_alt_name=data['sub_topic_alt_name']
            topic_instance=topics.objects.get(topic_id=topic_id)
            if (data['sub_topic_id']==""):
                topic_id_prefix=topic_id
                last_subtopic= sub_topics.objects.filter(sub_topic_id__startswith=topic_id_prefix).order_by('-sub_topic_id').first()
                if last_subtopic:
                    last_number=int(last_subtopic.sub_topic_id[-2:])
                    start_number=last_number+1
                else:
                    start_number=1
                if start_number > 99:
                    return JsonResponse(
                        {'error': 'Cannot create more subtopics. Maximum limit of 99 subtopics would be exceeded.'},
                        status=400
                    )
                sub_topic_id=f'{topic_id_prefix}{start_number:02d}'
                subtopic=sub_topics(
                    sub_topic_id=sub_topic_id,
                    sub_topic_name=sub_topic_name,
                    sub_topic_description=sub_topic_description,
                    sub_topic_alt_name=sub_topic_alt_name,
                    topic_id=topic_instance,
                    created_by=data['by'],
                    created_at=course.get_ist_time(),
                    modified_at = course.get_ist_time()
                )
                print("3")
                subtopic.save()

            else:
                sub_topic_id=data['sub_topic_id']
                sub_topic=sub_topics.objects.get(sub_topic_id=sub_topic_id)
                sub_topic.sub_topic_name = sub_topic_name
                sub_topic.sub_topic_description= sub_topic_description
                sub_topic.sub_topic_alt_name = sub_topic_alt_name
                sub_topic.modified_by = data['by']
                sub_topic.modified_at = course.get_ist_time()
                sub_topic.topic_id=topic_instance
                sub_topic.save()
                
            return JsonResponse({'message':'Sub Topic created / updated successfully'})
        except Exception as e:
            print('exce',e)
            return JsonResponse({"error":str(e)},status=500)