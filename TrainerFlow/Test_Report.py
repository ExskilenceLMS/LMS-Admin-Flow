from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details,courses as course_model,batches as batch_model
from LMS_MSSQLdb_App.models import students_info as student_model,students_assessments 
from django.db.models import Count
from LMS_MSSQLdb_App.models import *
@api_view(['GET'])
def filter_for_Test_Report(request):
    try:
        tracks   = list(track_model.objects.filter(del_row=False))
        courses  = list(course_model.objects.filter(del_row=False))
        subjects = list(subject_model.objects.filter(del_row=False))
        topics   = list(topic_model.objects.filter(del_row=False))
        batchs   = list(batch_model.objects.filter(del_row=False))
        LiveorCompleted = ['Live','Completed']
        Colleges = list(college_details.objects.filter(del_row=False))
        branchs  = list(branch_details.objects.filter(del_row=False))
        student_type = ['Swapnodaya','Exskilence']
        Test_type = list(test_details.objects.filter(del_row=False).values_list('test_type',flat=True).distinct())
        return JsonResponse({
            'tracks':  [ track.track_name for track in tracks],  
            'courses':{
                track.track_name:[
                    course.course_name for course in courses if course.tracks.split(",").count(track.track_name)>0
                                  ] for track in tracks
            },
            'subjects': {
                track.track_name:{
                    course.course_name:[
                        subject.subject_name for subject in subjects if subject.track_id.track_name == track.track_name
                                        ] for course in courses if course.tracks.split(",").count(track.track_name)>0
                                 } for track in tracks
             },
            'topics': {
               track.track_name:{
                        course.course_name:{
                            subject.subject_name:[
                                  topic.topic_name for topic in topics if topic.subject_id.subject_name == subject.subject_name
                                                 ] for subject in subjects if subject.track_id.track_name == track.track_name
                                            }      for course in courses if course.tracks.split(",").count(track.track_name)>0
                                } for track in tracks
                        },
            'batches':[
                batch.batch_name for batch in batchs
            ],
            'liveorCompleted':LiveorCompleted,
            'colleges':[ college.college_name for college in Colleges],
            'branches':{
                college.college_name:[
                        branch.branch for branch in branchs if branch.college_id.college_name == college.college_name
                                     ] for college in Colleges
            },
            'student_type':student_type,
            'test_type':Test_type
            
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def get_tests_Report_details(request):
    try:
        data = json.loads(request.body)
        test_details_filters = {}
        students_assessments_filters = {}

        if data.get('track','') != "":
            test_details_filters.update({'track_id__track_name':data.get('track')})
        if data.get('course','') != "":
            test_details_filters.update({'course_id__course_name':data.get('course')})
        if data.get('subject','')!= "":
            test_details_filters.update({'subject_id__subject_name':data.get('subject')})
        if data.get('topic','')!= "":
            test_details_filters.update({'topic_id__in':data.get('topic')})
        if data.get('Test_type','')!= "":
            test_details_filters.update({'test_type':data.get('test_type')})
        if data.get('tags','')!= "":
            test_details_filters.update({'tags__in':data.get('tags')})
        if data.get('date','')!= "":
            test_details_filters.update({'test_date_and_time__date':data.get('date')})

        if data.get('batch','') != "":
            students_assessments_filters.update({'student_id__batch_id__batch_name':data.get('batch')})
        if data.get('student_type','') != "":
            students_assessments_filters.update({'student_id__student_type':data.get('student_type')})
        if data.get('college','') != "":
            students_assessments_filters.update({'student_id__college':data.get('college')})
        if data.get('branch','') != "":
            students_assessments_filters.update({'student_id__branch':data.get('branch')})

        tests = test_details.objects.filter(**test_details_filters,test_date_and_time__lte=datetime.now().__add__(timedelta(hours=5,minutes=30)),del_row=False)
        test_ids = [test.test_id for test in tests]
        Invited = students_assessments.objects.filter( **students_assessments_filters,test_id__in=test_ids,del_row=False)
        test_counts ={}
        Students_objs = {}
        [test_counts.update({student.test_id.test_id :test_counts.get(student.test_id.test_id,0)+1}) for student in Invited ]
        # [Students_objs.update({student.student_id.student_id :if Students_objs.get(student.student_id.student_id,[]).append(student)}) for student in Invited ]
        # for student in Invited:
        #     if test_counts.get(student.test_id.test_id) is None:
        #         test_counts.update({student.test_id.test_id:[]})
        #     test_counts.get(student.test_id.test_id).append(student.student_id.student_id)
        #     Students_objs.update({student.student_id.student_id:student})
        test_data = []
        for test in tests:
            test_data.append({
                'test_id': test.test_id,
                'title': test.test_name,
                'description': test.test_description,
                'duration': test.test_duration,
                'marks': test.test_marks,
                'subject': test.subject_id.subject_name if test.subject_id else None,
                'date': test.test_date_and_time.date() if test.test_date_and_time else None,
                'from_time': str(test.test_date_and_time.strftime('%I:%M %p')) if test.test_date_and_time else None,
                'end_time': str(test.test_date_and_time.__add__(timedelta(minutes=int(test.test_duration))).strftime('%I:%M %p'))  if test.test_date_and_time else None,
                'track': test.track_id.track_name if test.track_id else None,
                'course': test.course_id.course_name if test.course_id else None,
                'test_type': test.test_type if test.test_type else None,
                'invited':test_counts.get(test.test_id,0),
                'test_end_time':test.test_date_and_time.__add__(timedelta(minutes=int(test.test_duration)))

            })
            if datetime.strptime(str(test.test_date_and_time).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.now().__add__(timedelta(hours=5,minutes=30)):
                
                # report =[]
                # [report.append({
                #     "student_id"    : Students_objs.get(student).student_id.student_id,
                #     "student_name"  : Students_objs.get(student).student_id.student_firstname + Students_objs.get(student).student_id.student_lastname,
                #     "college"       : Students_objs.get(student).student_id.college,
                #     "branch"        : Students_objs.get(student).student_id.branch,
                #     "category"      : Students_objs.get(student).student_id.student_type,
                #     "max_marks"   : Students_objs.get(student).assessment_max_score,
                #     "obtained_marks"  : Students_objs.get(student).assessment_score_secured,
                #     "percentage"   : Students_objs.get(student).assessment_score_secured/Students_objs.get(student).assessment_max_score*100,
                #     "rank"         : Students_objs.get(student).assessment_rank,
                # }) for student in test_counts.get(test.test_id)]
                test_data[-1].update({'status': 'Completed'})
            else:
                # report =[]
                # [report.append({
                #     "student_id"    : Students_objs.get(student).student_id.student_id,
                #     "student_name"  : Students_objs.get(student).student_id.student_firstname + Students_objs.get(student).student_id.student_lastname,
                #     "college"       : Students_objs.get(student).student_id.college,
                #     "branch"        : Students_objs.get(student).student_id.branch,
                #     "category"      : Students_objs.get(student).student_id.student_type,
                #     "test_status"   : Students_objs.get(student).assessment_status,
                #     "datetime"      :(str(test.test_date_and_time)+' to '
                #                         +str(test.test_date_and_time)
                #                         ) if Students_objs.get(student).assessment_status != 'C' else (
                #                             str(test.test_date_and_time)+' to '
                #                                     +str(test.test_date_and_time.__add__(timedelta(minutes=int(test.test_duration)))))

                # }) for student in test_counts.get(test.test_id)]
                test_data[-1].update({'status': 'Live'})
        return JsonResponse(test_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@api_view(['GET'])
def get_students_test_report(request,testID):
    try:
        Students_objs = students_assessments.objects.filter( test_id=testID,del_row=False)
        # test_details =Students_objs[0] if len(Students_objs) > 0 else None
        test_detaile = test_details.objects.get(test_id=testID,del_row=False)
        report = []
        for Student in Students_objs:
            if datetime.strptime(str(Student.test_id.test_date_and_time).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.now().__add__(timedelta(hours=5,minutes=30)):
               
                report.append({
                    "student_id"    : Student.student_id.student_id,
                    "student_name"  :Student.student_id.student_firstname +Student.student_id.student_lastname,
                    "college"       :Student.student_id.college,
                    "branch"        :Student.student_id.branch,
                    "category"      :Student.student_id.student_type,
                    "max_marks"   :Student.assessment_max_score,
                    "obtained_marks"  :Student.assessment_score_secured,
                    "percentage"   :Student.assessment_score_secured/Student.assessment_max_score*100,
                    "rank"         :Student.assessment_rank,
                })
            else:
             
                report.append({
                    "student_id"    :Student.student_id.student_id,
                    "student_name"  :Student.student_id.student_firstname +Student.student_id.student_lastname,
                    "college"       :Student.student_id.college,
                    "branch"        :Student.student_id.branch,
                    "category"      :Student.student_id.student_type,
                    "test_status"   :Student.assessment_status,
                    "datetime"      :(date_formater(test_detaile.test_date_and_time)+' to '
                                        +date_formater(test_detaile.test_date_and_time)
                                        ) if Student.assessment_status != 'C' else (
                                            date_formater(test_detaile.test_date_and_time)+' to '
                                                    +date_formater(test_detaile.test_date_and_time.__add__(timedelta(minutes=int(test_detaile.test_duration)))))

                }) 
        response  = {
            "test_name"     :test_detaile.test_name,
            "course_name"   :test_detaile.course_id.course_name,
            "batch_name"    :Students_objs[0].student_id.batch_id.batch_name if len(Students_objs) > 0 else None,
            'test_status'   :'Completed' if datetime.strptime(str(test_detaile.test_date_and_time.__add__(timedelta(minutes=int(test_detaile.test_duration)))).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.now().__add__(timedelta(hours=5,minutes=30)) else 'Live',
            'test_start_time':date_formater(test_detaile.test_date_and_time),
            'test_end_time' :date_formater(test_detaile.test_date_and_time.__add__(timedelta(minutes=int(test_detaile.test_duration)))),
            'duration'      :test_detaile.test_duration,
            "report"        :report
        }
        return JsonResponse(response,safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def date_formater(date_time):
    return str(date_time.day)+'-'+str(date_time.month)+'-'+str(date_time.year)[-2:]+' '+str(date_time.strftime('%I:%M %p'))