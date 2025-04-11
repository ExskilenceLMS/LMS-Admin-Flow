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
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Max, F ,Sum,Min,Count
# from django.contrib.postgres.aggregates import ArrayAgg
import json
from django.db.models.functions import TruncDate
from django.core.cache import cache

# def fetch_roadmap(student_id,course_id,subject_id):
#     try:
#         student = students_info.objects.get(student_id = student_id,del_row = False)
#         course = student.course_id
#         blob_data = json.loads(get_blob(f'lms_daywise/{course.course_id}/{course.course_id}_{student.batch_id.batch_id}.json'))
#         sub = subjects.objects.get(subject_id = subject_id,del_row = False)
#         course_details = list(course_plan_details.objects.filter(course_id=course, subject_id=sub, del_row=False)
#                   .values('week')
#                   .annotate(#   day_date_count=Count('day_date'),
#                       startDate=Min('day_date'),
#                       endDate=Max('day_date'),
#                       totalHours=Sum('duration_in_hours'),
#                   )
#                   .order_by('week'))
#         studentQuestions = students_details.objects.using('mongodb').get(
#             student_id = student_id,
#             del_row = False
#             )
#         sub_data = studentQuestions.student_question_details.get(sub.subject_name,{})
#         days = []
#         other_weeks = []
#         Onsite = []
#         intern = []
#         final = []
#         daynumber=0
#         for i in course_details:
#             week_data = sub_data.get('week_'+str(i.get('week')),{})
#             if i.get('week') > 1:
#                 prev_week_data = sub_data.get('week_'+str(i.get('week')-1),{})
#             else:
#                 prev_week_data = {}
#             week_first_day = 0
#             for d in blob_data.get(sub.subject_name):
#                 if d.get('date').__contains__('T') or d.get('date').__contains__('Z') or len(d.get('date'))>10:
#                     the_date = datetime.strptime(d.get('date').replace('T',' ').split('.')[0].replace('Z',''), "%Y-%m-%d %H:%M:%S")
#                 else:
#                     the_date = datetime.strptime(d.get('date')+" 00:00:00", "%Y-%m-%d %H:%M:%S")
#                 if i.get('startDate').date() <= the_date.date() and the_date.date() <= i.get('endDate').date():
#                     if week_first_day == 0:
#                         week_first_day = int(d.get('day').split(' ')[-1])
#                         # print('week_first_day',week_first_day,"prev_week_data",prev_week_data)
#                     day_data = week_data.get('day_'+str(d.get('day').split(' ')[-1]),{})
#                     status = ''
#                     mcq_qns =len(day_data.get('mcq_questions',[]))
#                     coding_qns =  len(day_data.get('coding_questions',[]))
#                     mcq_answered = len([dd for dd in day_data.get('mcq_questions_status',{}) if day_data.get('mcq_questions_status',{}).get(dd)==2])
#                     coding_answered = len([dd for dd in day_data.get('coding_questions_status',{}) if day_data.get('coding_questions_status',{}).get(dd)==2])
                   
#                     day_status = [ day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in day_data.get('sub_topic_status',{}) ]
 
#                     if sum(day_status) == len(day_status)*2 and len(day_status) != 0:
#                         status = 'Completed'
#                     elif sum(day_status) != 0:
#                         status = 'Resume'
#                     else:
#                         prev_day_data = week_data.get('day_'+str(int(d.get('day').split(' ')[-1])-1),{})
#                         prev_day_status = [ prev_day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in prev_day_data.get('sub_topic_status',{}) ]
#                         if sum(prev_day_status) == len(prev_day_status)*2 and len(prev_day_status) != 0:
#                             status = 'Start'
#                         last_weeks_last_day_data = prev_week_data.get('day_'+str(week_first_day-1),{})
#                         last_weeks_last_day_status = [ last_weeks_last_day_data.get('sub_topic_status',{}).get(day_stat) for day_stat in last_weeks_last_day_data.get('sub_topic_status',{}) ]
#                         if (status == '' and daynumber == 0 ) or (sum(last_weeks_last_day_status) == len(last_weeks_last_day_status)*2 and len(last_weeks_last_day_status) != 0):
#                             status = 'Start'
#                     if d.get('topic') == 'Weekly Test':# or d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Internship':
#                         days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':i.get('week'),
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
 
#                             'status':""
#                               })
#                     elif d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Final Test':
#                         Onsite.append({#'day':daynumber+1,
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     elif d.get('topic') == 'Internship':
#                         intern.append({'day':'',
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     elif d.get('topic') == 'Final Test':
#                         final.append({'day':'',
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     else:
#                         days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':i.get('week'),
#                             'topics':d.get('topic'),
#                             'practiceMCQ': { 'questions': str(mcq_answered)
#                                             +'/'+str(mcq_qns),
#                                              'score': day_data.get('mcq_score','0/0') },
#                             'practiceCoding': { 'questions': str(coding_answered)
#                                             +'/'+str(coding_qns),
#                                              'score': day_data.get('coding_score','0/0') },
#                             'status':status if str(d.get('topic')).lower() != 'Festivals'.lower() and str(d.get('topic')).lower() != 'Preparation Day'.lower() and str(d.get('topic')).lower() != 'Semester Exam'.lower()  and  str(d.get('topic')).lower() != 'Internship'.lower() else ''
#                               })
#                     daynumber+=1    
#             i.update({'days': days})
#             days = []
#         other_weeks.extend([{
#             'week':len(course_details)+1,
#             'startDate': Onsite[0].get('date') if Onsite!=[] else '',
#             'endDate': Onsite[-1].get('date') if Onsite!=[] else '',
#             'days':Onsite,
#             'topics':'Onsite Workshop'
#         },
#         {
#             'week':len(course_details)+2,
#             'startDate': final[0].get('date') if final!=[] else '',
#             'endDate': final[-1].get('date') if final!=[] else '',
#             'days':final,
#             'topics':'Final Test'
#         },
#         {
#             'week':len(course_details)+3,
#             'startDate': intern[0].get('date') if intern!=[] else '',
#             'endDate': intern[-1].get('date') if intern!=[] else '',
#             'days':intern,
#             'topics':'Internship Challenge'
#         }]
#         )
#         course_details.extend(other_weeks)
#         response = {
#             "weeks":course_details,
#         }
#         return JsonResponse(response,safe=False,status=200)
                   
#         # return fetch_roadmap_old(request,student_id,course_id,subject_id)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)
 

def get_day_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

def format_date_with_suffix(date_obj):
    try:
        day = date_obj.day
        suffix = get_day_suffix(day)
        month_year = date_obj.strftime("%b %y")  # Only safe format here
        return f"{day}{suffix} {month_year}"
    except Exception as e:
        print("Date formatting error:", e)
        return str(date_obj)

def fetch_roadmap(course_id, subject_id, batch_id):
    try:
        course = courses.objects.get(del_row=False, course_id=course_id)
        batch = batches.objects.get(del_row=False, batch_id=batch_id)
        subject = subjects.objects.get(del_row=False, subject_id=subject_id)

        # Fetch all relevant DB entries
        db_entries = course_plan_details.objects.filter(
            course_id=course,
            subject_id=subject,
            batch_id=batch,
            del_row=False
        ).order_by('week', 'day')

        # Read daywise JSON blob
        path = f'lms_daywise/{course.course_id}/{course.course_id}_{batch.batch_id}.json'
        blob_client = container_client.get_blob_client(path)
        download_stream = blob_client.download_blob()
        json_data = json.loads(download_stream.readall())

        subject_key = subject.subject_name.replace(" ", "")
        daywise_data = json_data.get(subject_key, [])

        # Index blob data by date for fast lookup
        blob_by_date = {d["date"]: d for d in daywise_data}

        week_map = {}

        for entry in db_entries:
            week = entry.week
            date_key = entry.day_date.strftime("%Y-%m-%d")
            blob_day = blob_by_date.get(date_key, {})

            if week not in week_map:
                week_map[week] = {
                    "week": week,
                    "startDate": entry.day_date,
                    "endDate": entry.day_date,
                    "totalHours": 0,
                    "days": []
                }

            week_data = week_map[week]

            # Update start/end dates
            week_data["startDate"] = min(week_data["startDate"], entry.day_date)
            week_data["endDate"] = max(week_data["endDate"], entry.day_date)
            week_data["totalHours"] += entry.duration_in_hours or 0

            # Format date
            formatted_date = format_date_with_suffix(entry.day_date)

            # Collect MCQ and coding summary
            def get_total_questions(data):
                if not isinstance(data, dict):
                    return "0/0"
                total = sum(sum(v.values()) for v in data.values())
                return f"{total}/{total}"

            day_data = {
                "day": entry.day,
                "date": formatted_date,
                "week": entry.week,
                "topics": blob_day.get("topic", entry.content_type),
                "practiceMCQ": {
                    "questions": get_total_questions(blob_day.get("mcq"))
                },
                "practiceCoding": {
                    "questions": get_total_questions(blob_day.get("coding"))
                },
            }

            week_data["days"].append(day_data)

        # Format the final result
        weeks = sorted(week_map.values(), key=lambda w: w["week"])
        for w in weeks:
            w["startDate"] = w["startDate"].isoformat() + "Z"
            w["endDate"] = w["endDate"].isoformat() + "Z"
        print(weeks)
        return weeks

    except Exception as e:
        print("Error:", e)
        return JsonResponse({"error": str(e)}, status=500)


# def fetch_roadmap(course_id,subject_id,batch_id):
#     try:
#         course=courses.objects.get(del_row=False,course_id=course_id)
#         batch=batches.objects.get(del_row=False,batch_id=batch_id)
#         subject=subjects.objects.get(del_row=False,subject_id=subject_id)

#         print(course,batch,subject)
#         # datas=course_plan_details.objects.filter(del_row=False,course_id=course,batch_id=batch,subject_id=subject)

#         course_details = list(course_plan_details.objects.filter(course_id=course, subject_id=subject,batch_id=batch, del_row=False)
#                   .values('week')
#                   .annotate(#   day_date_count=Count('day_date'),
#                       startDate=Min('day_date'),
#                       endDate=Max('day_date'),
#                       totalHours=Sum('duration_in_hours'),
#                   )
#                   .order_by('week'))
#         # print(datas)
#         # for data in datas:
#         #     print('11')
#         #     json={
#         #         'week':data.week,
#         #         'day':data.day,
#         #         'date':data.day_date,
#         #         'duration':data.duration_in_hours,
#         #         'content':data.content_type
#         #     }
#         #     print(json)

#         print(course_details)
#     except Exception as e:
#         print(e)

# fetch_roadmap('course11','sr','batch6')

# # @api_view(['GET'])
# def fetch_roadmap_old(request,student_id,course_id,subject_id):
#     try:
#         student = students_info.objects.get(student_id = student_id,del_row = False)
#         course = student.course_id
#         # blob_data = json.loads(get_blob(f'LMS_DayWise/Course0001.json')) #json.loads(get_blob(f'lms_daywise/{course.course_id}/{course_id}.json'))
#         blob_data = json.loads(get_blob(f'lms_daywise/{course.course_id}/{course.course_id}_{student.batch_id.batch_id}.json'))
#         # course = courses.objects.get(course_id=course_id)
#         sub = subjects.objects.get(subject_id = subject_id,del_row = False)
#         course_details = list(course_plan_details.objects.filter(course_id=course, subject_id=sub, del_row=False)
#                   .values('week')
#                   .annotate(#   day_date_count=Count('day_date'),
#                       startDate=Min('day_date'),
#                       endDate=Max('day_date'),
#                       totalHours=Sum('duration_in_hours'),
#                   )
#                   .order_by('week'))
#         studentQuestions = students_details.objects.using('mongodb').get(
#             student_id = student_id,del_row = 'False'
#         )
#         sub_data = studentQuestions.student_question_details.get(sub.subject_name,{})
#         days = []
#         other_weeks = []
#         Onsite = []
#         intern = []
#         final = []
#         daynumber=0
#         for i in course_details:
#             week_data = sub_data.get('week_'+str(i.get('week')),{})
#             if i.get('week') > 1:
#                 prev_week_data = sub_data.get('week_'+str(i.get('week')-1),{})
#             else:
#                 prev_week_data = {}
#             week_first_day = 0
#             for d in blob_data.get(sub.subject_name):
#                 if d.get('date').__contains__('T') or d.get('date').__contains__('Z') or len(d.get('date'))>10:
#                     the_date = datetime.strptime(d.get('date').replace('T',' ').split('.')[0].replace('Z',''), "%Y-%m-%d %H:%M:%S")
#                 else:
#                     the_date = datetime.strptime(d.get('date')+" 00:00:00", "%Y-%m-%d %H:%M:%S")
#                 if i.get('startDate').date() <= the_date.date() and the_date.date() <= i.get('endDate').date():
#                     if week_first_day == 0:
#                         week_first_day = int(d.get('day').split(' ')[-1])
#                         # print('week_first_day',week_first_day,"prev_week_data",prev_week_data)
#                     day_data = week_data.get('day_'+str(d.get('day').split(' ')[-1]),{})
#                     status = ''
#                     mcq_qns =len(day_data.get('mcq_questions',[]))
#                     coding_qns =  len(day_data.get('coding_questions',[]))
#                     mcq_answered = len([dd for dd in day_data.get('mcq_questions_status',{}) if day_data.get('mcq_questions_status',{}).get(dd)==2])
#                     coding_answered = len([dd for dd in day_data.get('coding_questions_status',{}) if day_data.get('coding_questions_status',{}).get(dd)==2])
#                     if (day_data.get('mcq_questions') is None and coding_qns == coding_answered and coding_qns > 0
#                         ) or (day_data.get('coding_questions') is None and mcq_qns == mcq_answered and mcq_qns > 0
#                               )or(mcq_qns == mcq_answered and coding_qns == coding_answered and mcq_qns > 0 and coding_qns > 0):
#                         status = 'Completed'
#                     elif mcq_answered > 0 or coding_answered > 0 or day_data != {} :
#                         status = 'Resume'
#                     else:
#                         prev_day_data = week_data.get('day_'+str(int(d.get('day').split(' ')[-1])-1),{})
#                         prev_mcq_qns =len(prev_day_data.get('mcq_questions',[]))
#                         prev_coding_qns =  len(prev_day_data.get('coding_questions',[]))
#                         prev_mcq_answered = len([dd for dd in prev_day_data.get('mcq_questions_status',{}) if prev_day_data.get('mcq_questions_status',{}).get(dd)==2])
#                         prev_coding_answered = len([dd for dd in prev_day_data.get('coding_questions_status',{}) if prev_day_data.get('coding_questions_status',{}).get(dd)==2])
#                         if prev_mcq_qns == prev_mcq_answered and prev_coding_qns == prev_coding_answered and prev_mcq_qns > 0 and prev_coding_qns > 0:
#                             status = 'Start'
#                         last_weeks_last_day_data = prev_week_data.get('day_'+str(week_first_day-1),{})
#                         last_weeks_mcq_qns =len(last_weeks_last_day_data.get('mcq_questions',[]))
#                         last_weeks_coding_qns =  len(last_weeks_last_day_data.get('coding_questions',[]))
#                         last_weeks_mcq_answered = len([dd for dd in last_weeks_last_day_data.get('mcq_questions_status',{}) if last_weeks_last_day_data.get('mcq_questions_status',{}).get(dd)==2])
#                         last_weeks_coding_answered = len([dd for dd in last_weeks_last_day_data.get('coding_questions_status',{}) if last_weeks_last_day_data.get('coding_questions_status',{}).get(dd)==2])
#                         if (status == '' and daynumber == 0 ) or (last_weeks_mcq_qns == last_weeks_mcq_answered and last_weeks_coding_qns == last_weeks_coding_answered and last_weeks_mcq_qns > 0 and last_weeks_coding_qns > 0):
#                             status = 'Start'
#                     if d.get('topic') == 'Weekly Test':# or d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Internship':
#                         days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':i.get('week'),
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
 
#                             'status':""
#                               })
#                     elif d.get('topic') == 'Onsite Workshop' or d.get('topic') == 'Final Test':
#                         Onsite.append({#'day':daynumber+1,
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     elif d.get('topic') == 'Internship':
#                         intern.append({'day':'',
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     elif d.get('topic') == 'Final Test':
#                         final.append({'day':'',
#                             'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':len(course_details)+other_weeks.__len__()+1,
#                             'topics':d.get('topic'),
#                             'score' :'0/0',
#                             'days':[],
#                             'status':''
#                               })
#                     else:
#                         days.append({'day':daynumber+1,'day_key':d.get('day').split(' ')[-1],
#                             "date":getdays(the_date),#+" "+the_date.strftime("%Y")[2:],
#                             'week':i.get('week'),
#                             'topics':d.get('topic'),
#                             'practiceMCQ': { 'questions': str(mcq_answered)
#                                             +'/'+str(mcq_qns),
#                                              'score': day_data.get('mcq_score','0/0') },
#                             'practiceCoding': { 'questions': str(coding_answered)
#                                             +'/'+str(coding_qns),
#                                              'score': day_data.get('coding_score','0/0') },
#                             'status':status if str(d.get('topic')).lower() != 'Festivals'.lower() and str(d.get('topic')).lower() != 'Preparation Day'.lower() and str(d.get('topic')).lower() != 'Semester Exam'.lower()  and  str(d.get('topic')).lower() != 'Internship'.lower() else ''
#                               })
#                     daynumber+=1    
#             i.update({'days': days})
#             days = []
#         other_weeks.extend([{
#             'week':len(course_details)+1,
#             'startDate': Onsite[0].get('date') if Onsite!=[] else '',
#             'endDate': Onsite[-1].get('date') if Onsite!=[] else '',
#             'days':Onsite,
#             'topics':'Onsite Workshop'
#         },
#         {
#             'week':len(course_details)+2,
#             'startDate': final[0].get('date') if final!=[] else '',
#             'endDate': final[-1].get('date') if final!=[] else '',
#             'days':final,
#             'topics':'Final Test'
#         },
#         {
#             'week':len(course_details)+3,
#             'startDate': intern[0].get('date') if intern!=[] else '',
#             'endDate': intern[-1].get('date') if intern!=[] else '',
#             'days':intern,
#             'topics':'Internship Challenge'
#         }]
#         )
#         course_details.extend(other_weeks)
#         response = {
#             "weeks":course_details,
#         }
#         return JsonResponse(response,safe=False,status=200)
#     except Exception as e:
#         print(e)
#         return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)

