from datetime import datetime, timedelta
from django.http import JsonResponse
from rest_framework.decorators import api_view
import json
from LMS_MSSQLdb_App.models import *
from .Blobstorage import *
@api_view(['POST'])
def test_creation(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.create(
            test_id = 'Test'+str(int(test_details.objects.all().order_by('-test_id').first().test_id.replace('Test',''))+1) ,#auto generated like test1, test2
            test_name = data.get('test_name'),
            test_description = data.get('description'), 
            test_duration = data.get('duration'),
            test_marks = data.get('marks'),
            test_created_by = data.get('created_by'),
            test_created_date_time = datetime.utcnow().__add__(timedelta(hours=5,minutes=30)),
        )
        return JsonResponse({"status": "success",
                             'test_id': test.test_id})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error","message":str(e)})
@api_view(['PUT'])
def test_update(request):
    try:
        data = json.loads(request.body)
        test = test_details.objects.get(test_id = data.get('test_id'),del_row = False)
        test.test_name = data.get('test_name')          if data.get('test_name','') != '' else test.test_name
        test.test_description = data.get('description') if data.get('description','') != '' else test.test_description
        test.test_duration = data.get('duration')       if data.get('duration','') != '' else test.test_duration
        test.test_marks = data.get('marks')             if data.get('marks','') != '' else test.test_marks
        test.test_created_by = data.get('created_by')   if data.get('created_by','') != '' else test.test_created_by
        test.save()
        return JsonResponse({"status": "success",
                             'test_id': test.test_id})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "error","message":str(e)})
@api_view(['GET'])  
def get_test_details(request,test_id):
    try:
        test = test_details.objects.get(test_id=test_id)
        return JsonResponse({
                             'test'         : test.test_name,
                             'description'  : test.test_description,
                             'duration'     : test.test_duration,
                             'marks'        : test.test_marks,})
    except Exception as e:
         # print(e)
        return JsonResponse({"status": "error","message":str(e)})
@api_view(['POST'])
def get_test_Questions(request):
    try:
        data = json.loads(request.body)
        filters = {}

        if data.get('track','') != "":
            filters.update({'sub_topic_id__topic_id__subject_id__track_id__track_name':data.get('track')})
        if data.get('subject','')!= "":
            filters.update({'sub_topic_id__topic_id__subject_id__subject_name':data.get('subject')})
        if data.get('topic','')!= "":
            filters.update({'sub_topic_id__topic_id':data.get('topic')})
        if data.get('level','')!= "":
            filters.update({'level':data.get('level')})
        if data.get('tags','')!= "":
            filters.update({'tags__in':data.get('tags')})
        # if data.get('marks')!= "":
        #     filters.update({'test_marks':data.get('marks')})
        # if data.get('duration')!= "":
        #     filters.update({'test_duration':data.get('duration')})
        # if data.get('date')!= "":
        #     filters.update({'test_date_and_time__date':data.get('date')})

        Qns = questions.objects.filter(**filters,del_row=False).values('question_id',
            'question_type', 
            'level',
            )
        sub_topic = sub_topics.objects.filter(del_row=False)
        subject_list = {sb.topic_id.subject_id.subject_id:sb.topic_id.subject_id.subject_name for sb in sub_topic }
        sub_topics_list =  {sb.sub_topic_id:sb.sub_topic_name for sb in sub_topic }#{sb.get('sub_topic_id'):sb.get('sub_topic_name') for sb in sub_topic }
        Qn_data = []
        container_client = get_blob_container_client()
        rules = json.loads(container_client.get_blob_client('lms_rules/rules.json').download_blob().readall())
        for Qn in Qns :
            Qn = Qn.get('question_id') 
            type = 'coding' if Qn[-5] == 'c' else 'mcq'
            path = f'subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type}/{Qn}.json'
            cacheres = cache.get(path)
            if cacheres:
                cache.set(path,cacheres)
                blob_data = cacheres
            else:
                blob_client = container_client.get_blob_client(path)
                blob_data = json.loads(blob_client.download_blob().readall())
                cache.set(path,blob_data)
            level = blob_data.get('Level','') if blob_data.get('Level') else blob_data.get('level','')
            jsondata ={
                             "qn_id"            : Qn,
                             "qn_name"          : (blob_data.get('Name') +' in '+subject_list.get(Qn[1:3],'')) if blob_data.get('Name') else (sub_topics_list.get(Qn[1:15],'') + ' in '+subject_list.get(Qn[1:3],'')),
                             "question_type"    : 'Coding' if Qn[-5] == 'c' else 'MCQ',
                             "level"            : level,
                             "question"         : blob_data.get('Qn') if blob_data.get('Qn') else blob_data.get('question'),
                             "score"            : 0,
                             "time"             : 0
                            }
            for rule in rules.get(type.lower(),[]):
                if rule.get('level','').lower() == level.lower():
                    jsondata.update({"score"    : rule.get('score'),
                                     "time"     : rule.get('time')})            
            Qn_data.append( (jsondata))
        container_client.close()
        return JsonResponse(Qn_data,safe=False)
    except Exception as e:
        # print(e)
        return JsonResponse({"status": "error","message":str(e)})
@api_view(['POST'])  
def set_test_sections(request):
    try:
        data = json.loads(request.body)
        try:
            test = test_details.objects.get(test_id=data.get('test_id'),del_row=False)
        except:
            return JsonResponse({"status"   : "error",
                                 "message"  : "Test not found"})
        Qns_list = []
        [Qns_list.extend(sec.get('qn_list',[])) for sec in data.get('sections')]
        Qns = questions.objects.filter(question_id__in=Qns_list,del_row=False)
        Qns_details_list = {qn.question_id:qn for qn in Qns}
        test_section = []
        for section in data.get('sections',[]):
            qn_list = section.get('qn_list',[])
            for qn in qn_list:
                ts = test_sections(
                    test_id=test,
                    section_number=int(section.get('section_name','Section0').replace('Section','')),
                    section_name=section.get('section_type'),
                    topic_id = Qns_details_list.get(qn).sub_topic_id.topic_id,
                    sub_topic_id = Qns_details_list.get(qn).sub_topic_id,
                    question_id=Qns_details_list.get(qn),
                )
                test.tags.extend(Qns_details_list.get(qn).tags)
                test.topic_id.append(Qns_details_list.get(qn).sub_topic_id.sub_topic_name)
                test_section.append(ts)
        test_section = test_sections.objects.bulk_create(test_section)
        test.tags = list(set(test.tags))
        test.save()
        return JsonResponse({"status": "success"})
    except Exception as e:
        # print(e)
        if str(e).__contains__("Cannot insert duplicate key row in object"):
            return JsonResponse({"status"   : "error",
                                 "message"  : "Cannot insert duplicate key row in object"})
        return JsonResponse({"status": "error","message":str(e)})
# def transfer_tags():
#     try:
#         QNs = questions.objects.all()
#         for Qn in QNs:
#             if Qn.tags != None and Qn.tags != '':
#                 for tag in Qn.tags.split(','):
#                     Qn.tags2.append(tag)
#                 Qn.save()
#         return JsonResponse({"status": "success"})
             
#     except Exception as e:
#          # print(e)
#         return JsonResponse({"status": "error"})    
