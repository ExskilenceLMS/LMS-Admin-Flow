from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view
from LMS_MSSQLdb_App.models import tracks as track_model,subjects as subject_model,topics as topic_model,suite_login_details,test_details,courses as course_model,batches as batch_model
from LMS_MSSQLdb_App.models import students_info as student_model,students_assessments
from LMS_Mongodb_App.models import *
from django.db.models import Count
from LMS_MSSQLdb_App.models import *
from django.core.cache import cache
import calendar
from .Blobstorage import *

@api_view(['GET'])
def filter_for_Test_Report(request):
    try:
        tracks   = list(track_model.objects.filter(del_row=False))
        courses  = list(course_model.objects.filter(del_row=False))
        subjects = list(subject_model.objects.filter(del_row=False))
        topics   = list(topic_model.objects.filter(del_row=False))
        batches   = list(batch_model.objects.filter(del_row=False))
        LiveorCompleted = ['Live','Completed']
        Colleges = list(college_details.objects.filter(del_row=False))
        branchs  = list(branch_details.objects.filter(del_row=False))
        student_type = ['Swapnodaya','Exskilence']
        Test_type = list(test_details.objects.filter(del_row=False).values_list('test_type',flat=True).distinct())
        batches_list = []
        [batches_list.append(i.batch_name) for i in batches if i.batch_name not in batches_list]
        return JsonResponse({
            'tracks'        :  [ track.track_name for track in tracks],  
            'courses'       :{
                track.track_name:[
                    course.course_name for course in courses if course.tracks.split(",").count(track.track_name)>0
                                  ] for track in tracks
            },
            'subjects'      : {
                track.track_name:{
                    course.course_name:[
                        subject.subject_name for subject in subjects if subject.track_id.track_name == track.track_name
                                        ] for course in courses if course.tracks.split(",").count(track.track_name)>0
                                 } for track in tracks
             },
            'topics'        : {
               track.track_name:{
                        course.course_name:{
                            subject.subject_name:[
                                  topic.topic_name for topic in topics if topic.subject_id.subject_name == subject.subject_name
                                                 ] for subject in subjects if subject.track_id.track_name == track.track_name
                                            }      for course in courses if course.tracks.split(",").count(track.track_name)>0
                                } for track in tracks
                        },
            'batches'       :batches_list,
            'liveorCompleted':LiveorCompleted,
            'colleges'      :[ college.college_name for college in Colleges],
            'branches'      :{
                college.college_name:[
                        branch.branch for branch in branchs if branch.college_id.college_name == college.college_name
                                     ] for college in Colleges
            },
            'student_type'  :student_type,
            'test_type'     :[i for i in Test_type if i != '']
            
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

        tests = test_details.objects.filter(**test_details_filters,test_date_and_time__lte=datetime.utcnow().__add__(timedelta(hours=5,minutes=30)),del_row=False).order_by('-test_date_and_time')
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
                'test_id'       : test.test_id,
                'title'         : test.test_name,
                'description'   : test.test_description,
                'duration'      : test.test_duration,
                'marks'         : test.test_marks,
                'subject'       : test.subject_id.subject_name if test.subject_id else None,
                'date'          : test.test_date_and_time.date() if test.test_date_and_time else None,
                'from_time'     : str(test.test_date_and_time.strftime('%I:%M %p')) if test.test_date_and_time else None,
                'end_time'      : str(test.test_date_and_time.__add__(timedelta(minutes=float(test.test_duration))).strftime('%I:%M %p'))  if test.test_date_and_time else None,
                'track'         : test.track_id.track_name if test.track_id else None,
                'course'        : test.course_id.course_name if test.course_id else None,
                'test_type'     : test.test_type if test.test_type else None,
                'invited'       :test_counts.get(test.test_id,0),
                'test_end_time' :test.test_date_and_time.__add__(timedelta(minutes=float(test.test_duration)))

            })
            if datetime.strptime(str(test.test_date_and_time.__add__(timedelta(minutes=float(test.test_duration)))).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.utcnow().__add__(timedelta(hours=5,minutes=30)):
                
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
            # print(datetime.strptime(str(test_detaile.test_date_and_time).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S"))
            # print(datetime.utcnow().__add__(timedelta(hours=5,minutes=30)))
            if datetime.strptime(str(test_detaile.test_date_and_time).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.utcnow().__add__(timedelta(hours=5,minutes=30)):
                if datetime.strptime(str(test_detaile.test_date_and_time).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S").__add__(timedelta(minutes=float(test_detaile.test_duration))) < datetime.utcnow().__add__(timedelta(hours=5,minutes=30)):
                    report.append({
                        "ID"            :Student.student_id.student_id,
                        "Student"       :Student.student_id.student_firstname +Student.student_id.student_lastname,
                        "College"       :Student.student_id.college,
                        "Branch"        :Student.student_id.branch,
                        "Category"      :Student.student_id.student_type,
                        "Max_marks"     :Student.assessment_max_score,
                        "Obtained_marks":Student.assessment_score_secured,
                        "Percentage"    :Student.assessment_score_secured/Student.assessment_max_score*100,
                        "Rank"          :Student.assessment_rank,
                    })
                else:
                    report.append({
                        "ID"            :Student.student_id.student_id,
                        "Student"       :Student.student_id.student_firstname +Student.student_id.student_lastname,
                        "College"       :Student.student_id.college,
                        "Branch"        :Student.student_id.branch,
                        "Category"      :Student.student_id.student_type,
                        "Test_status"   :Student.assessment_status,
                        "Date_Time"      :(date_formater(test_detaile.test_date_and_time)+' to '
                                            +date_formater(test_detaile.test_date_and_time)
                                            ) if Student.assessment_status != 'C' else (
                                                date_formater(test_detaile.test_date_and_time)+' to '
                                                        +date_formater(test_detaile.test_date_and_time.__add__(timedelta(minutes=float(test_detaile.test_duration)))))

                }) 
        response  = {
            "test_name"     :test_detaile.test_name,
            "course_name"   :test_detaile.course_id.course_name,
            "batch_name"    :Students_objs[0].student_id.batch_id.batch_name if len(Students_objs) > 0 else None,
            'test_status'   :'Completed' if datetime.strptime(str(test_detaile.test_date_and_time.__add__(timedelta(minutes=float(test_detaile.test_duration)))).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S") < datetime.utcnow().__add__(timedelta(hours=5,minutes=30)) else 'Live',
            'test_start_time':date_formater(test_detaile.test_date_and_time),
            'test_end_time' :date_formater(test_detaile.test_date_and_time.__add__(timedelta(minutes=float(test_detaile.test_duration)))),
            'time_left'     :round((datetime.strptime(str(test_detaile.test_date_and_time.__add__(timedelta(minutes=float(test_detaile.test_duration)))).split('+')[0].split('.')[0], "%Y-%m-%d %H:%M:%S")-datetime.utcnow().__add__(timedelta(hours=5,minutes=30))).total_seconds()),
            'duration'      :test_detaile.test_duration,
            "report"        :report
        }
        if response.get('time_left') < 0:
            response.pop('time_left')
        return JsonResponse(response,safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def date_formater(date_time):
    return str(date_time.day)+'-'+str(date_time.month)+'-'+str(date_time.year)[-2:]+' '+str(date_time.strftime('%I:%M %p'))

def format_time_with_zone(date):
    if date == None:
        return None
    date = datetime.strptime(str(date).split('.')[0].split('+')[0], "%Y-%m-%d %H:%M:%S")
    return (f"{calendar.month_abbr[int(date.strftime("%m"))]} {int(date.strftime("%d"))} {date.strftime('%Y')} {date.strftime('%H:%M:%S')} IST")

@api_view(['GET'])
def student_test_report(request,student_id,test_id):
    try: 
        student_assessment = students_assessments.objects.get(student_id = student_id,test_id = test_id,del_row = False)
        test_questions_list = list(test_sections.objects.filter(test_id = test_id,del_row = False))
        test_questions = [i.question_id.question_id for i in test_questions_list]
        # print(test_questions)
        answers_status = student_test_questions_details.objects.filter(student_id = student_id,test_id = test_id,question_id__in = test_questions,del_row = False).values('question_id','score_secured','max_score','question_status')
        coding_answers = student_practice_coding_answers.objects.using('mongodb').filter(student_id = student_id,question_id__in = test_questions,question_done_at = test_id,del_row = False).values('question_id','score','entered_ans','testcase_results')
        mcq_answers = student_practiceMCQ_answers.objects.using('mongodb').filter(student_id = student_id,question_id__in = test_questions,question_done_at = test_id,del_row = False).values('question_id','score','entered_ans')
        coding_answers = {i.get('question_id'):i for i in coding_answers}#{i.question_id:i for i in coding_answers}
        mcq_answers = { i.get('question_id'):i for i in mcq_answers}#{i.question_id:i for i in mcq_answers}
        topics_list ={i.question_id.question_id:i.question_id.sub_topic_id.topic_id.topic_name for i in test_questions_list}
        # print(topics_list)
        test_time_taken = round(student_assessment.student_duration/60) 
        Total_time_given = round((student_assessment.assessment_completion_time-student_assessment.test_id.test_date_and_time).total_seconds()/60)\
                            if student_assessment.assessment_type != 'Weekly Test' else float(student_assessment.test_id.test_duration)
        test_summary ={}
        test_summary.update({
            # 'time_taken_for_completion':round((student_assessment.student_test_start_time - student_assessment.student_test_completion_time ).total_seconds()/60,2),
            'time_taken_for_completion':str(test_time_taken)+' min' if test_time_taken < 60 else str(int(test_time_taken/60))+' hrs '+str(test_time_taken%60)+' min',
            'total_time'            :str(Total_time_given)+' min' if Total_time_given < 60 else str(int(Total_time_given/60))+' hrs '+str(Total_time_given%60)+' min',
            'score_secured'         :sum([score.get('score_secured') for score in answers_status]),
            'max_score'             :student_assessment.assessment_max_score,
            'percentage'            :round((student_assessment.assessment_score_secured/student_assessment.assessment_max_score)*100,2),
            'status'                :student_assessment.assessment_status,
            'attempted_questions'   :len(answers_status),
            'total_questions'       :len(test_questions),
            'test_start_time'       :format_time_with_zone (student_assessment.student_test_start_time) ,
            'test_end_time'         :format_time_with_zone (student_assessment.student_test_completion_time) 
        })
        if student_assessment.assessment_type == 'Final Test':
            test_summary.update({
                'overall_rank'  :student_assessment.student_id.student_overall_rank,
                'college_rank'  :student_assessment.student_id.student_college_rank,
            })
        test_topics_wise_scores ={}
        mcq=[]
        coding=[]
        container_client = get_blob_container_client()
        for ans in answers_status:
            Qn = ans.get('question_id') 
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            blob_data.update({'score_secured':ans.get('score_secured'),
                              'max_score':int(ans.get('max_score')),
                            #   'status':ans.get('question_status'),
                              'status':'Correct' if float(ans.get('score_secured'))==float(ans.get('max_score')) else 'Partial Correct' if float(ans.get('score_secured'))>0 else 'Wrong',
                              'topic':topics_list.get(ans.get('question_id'))
                              })
            if Qn[-5] == 'm':
                blob_data.update({
                    'user_answer':mcq_answers.get(ans.get('question_id'),{}).get('entered_ans',''),
                })
                mcq.append(blob_data)
            else:

                testcases =coding_answers.get(ans.get('question_id'),{}).get('testcase_results','')
                testcases_result =str(len([tc for tc in testcases if str(tc).startswith('TestCase') and testcases.get(tc) == 'Passed']))+'/'+str(len([tc for tc in testcases if str(tc).startswith('TestCase')]))
                blob_data.update({
                    'user_answer':coding_answers.get(ans.get('question_id'),{}).get('entered_ans',''),
                    'testcases' : testcases_result
                })
                coding.append(blob_data)
            test_topics_wise_scores.update({topics_list.get(ans.get('question_id')):
                                            f'{float(test_topics_wise_scores.get(topics_list.get(ans.get('question_id')),'0/0').split("/")[0])+float(ans.get("score_secured"))}/{float(test_topics_wise_scores.get(topics_list.get(ans.get('question_id')),'0/0').split("/")[1])+float(ans.get("max_score"))}'
                                            })
        not_attemted_Qns =[Qn for Qn in test_questions if Qn not in [answered.get('question_id')  for answered in answers_status]]
        rulesdata = container_client.get_blob_client('lms_rules/rules.json')
        rules = json.loads(rulesdata.download_blob().readall())
        for Qn in not_attemted_Qns:
            path = f"subjects/{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{'mcq' if Qn[-5]=='m' else 'coding'}/{Qn}.json"
            if cache.get(path) == None:
                blobdata = container_client.get_blob_client(path)
                blob_data = json.loads(blobdata.download_blob().readall())
                blob_data.update({'Qn_name':Qn})
                cache.set(path,blob_data)
            else:
                blob_data = cache.get(path)
                cache.set(path,blob_data)
            outoff = 0
            blob_rules_data = rules.get('mcq' if Qn[-5]=='m' else 'coding') 
            if Qn[-4]=='e':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level1'][0]
            elif Qn[-4]=='m':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level2'][0]
            elif Qn[-4]=='h':
                outoff = [i.get('score') for i in blob_rules_data if i.get('level').lower() == 'level3'][0]
            outoff = int(outoff)
            blob_data.update({'score_secured':0,
                              'max_score':outoff,
                            #   'status':ans.get('question_status'),
                              'status':'Not Attempted',
                              'topic':topics_list.get(Qn)
                              })
            if Qn[-5] == 'm':
                blob_data.update({
                    'user_answer':'',
                })
                mcq.append(blob_data)
            else:
                blob_data.update({
                    'user_answer':'',
                    'testcases' : '0/'+str(len(blob_data.get('TestCases')))
                })
                coding.append(blob_data)
        test_topics ={

        }
        for ans_score in test_topics_wise_scores:
            if float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[0])/float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[1]) >= 0.7:
                # print(ans_score)
                if test_topics.get('good',[]) == []:
                    test_topics.update({'good': [ans_score]})
                else:
                    test_topics.get('good').append(ans_score)
            elif float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[0])/float(test_topics_wise_scores.get(ans_score,'0/0').split("/")[1]) >= 0.4:
                print(ans_score)
                if test_topics.get('average',[]) == []:
                    test_topics.update({'average': [ans_score]})
                else:
                    test_topics.get('average').append(ans_score)
            else:
                print(ans_score)
                if test_topics.get('poor',[]) == []:
                    test_topics.update({'poor': [ans_score]})
                else:
                    test_topics.get('poor').append(ans_score)
                

        response ={
            'test_summary'  :test_summary,
            'topics_wise_scores':test_topics_wise_scores,
            'topics'        :test_topics,
            'answers'       :{
                'mcq'       :mcq,
                'coding'    :coding
            }
        }
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"message": "Failed","error":str(e)},safe=False,status=400)