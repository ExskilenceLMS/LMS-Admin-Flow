import json
from django.http import JsonResponse
from LMS_MSSQLdb_App.models import *
from LMS_Mongodb_App.models import *
from rest_framework.decorators import api_view
from django.db.models.functions import Concat
from django.db.models import Max, F ,Sum,Min,Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, F,ExpressionWrapper, DurationField,Avg
@api_view(['GET'])
def filter_for_performanceAnalysis(request):
    try:
        Courses = courses.objects.filter(del_row=False)
        batch_list = batches.objects.filter(del_row=False)
        subject_list = course_subjects.objects.filter(del_row=False)
        data = {
            'Courses'   :[ course.course_name for course in Courses],
            'batchs'    :{
                course.course_name:[batch.batch_name for batch in batch_list if batch.course_id.course_name == course.course_name] for course in Courses
            },
            'subjects'  :{ 
                course.course_name:{    batch.batch_name:list(set(
                                        subject.subject_id.subject_name
                                        for subject in subject_list
                                        if subject.course_id.course_name == batch.course_id.course_name
                                    )) for batch in batch_list if batch.course_id.course_name == course.course_name
                } for course in Courses
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def performanceAnalysis(request):
    try:
        data = json.loads(request.body)
        # data = {}
        student_filters = {}
        subject_filters = {} 
        if data.get('course','') != "":
            student_filters.update({'course_id__course_name':data.get('course')})
        if data.get('batch','') != "":
            student_filters.update({'batch_id__batch_name':data.get('batch')})
        if data.get('subject','') != "":
            subject_filters.update({'subject_id__subject_name':data.get('subject')})
        student = students_info.objects.filter(**student_filters,del_row=False)
        students_app_usage = student_app_usage.objects.filter(
                    student_id__in=[stud.student_id for stud in student],
                    del_row=False
                ).annotate(
                    duration=ExpressionWrapper(F('logged_out') - F('logged_in'), output_field=DurationField())
                ).values('student_id').annotate(
                    total_study_hours=Sum('duration')
                ).order_by('student_id')
        # print(students_app_usage)
        students_app_usage = {stud.get('student_id'):stud.get('total_study_hours').total_seconds()/3600 for stud in students_app_usage}
        response = []
        [response.append({
            'ID'            :stud.student_id,    
            'Name'          :stud.student_firstname+" "+stud.student_lastname,
            'Student_Type'  :stud.student_type,
            'College'       :stud.college,
            'Branch'        :stud.branch,
            'Mobile'        :stud.phone,
            'Score'         :str(stud.student_score)+'/'+str(stud.student_total_score),
            'Score_%'       :str(round(int(stud.student_score)*100/int(stud.student_total_score),2))+'%' if int(stud.student_total_score) != 0 else '0' +'%',
            'Catogory'      :stud.student_catogory,
            'College_Rank'  :stud.student_college_rank if stud.student_college_rank > 0 else '--',    
            'Overall_Rank'  :stud.student_overall_rank if stud.student_overall_rank > 0 else '--',    
            'Email'         :stud.student_email,
            'CGPA'          :stud.student_CGPA,
            'No_of_hours'   :round(students_app_usage.get(stud.student_id,0),2),
            'Course'        :stud.course_id.course_name,
            'Batch'         :stud.batch_id.batch_name,
                          }) for stud in student]  , 
        # Student_details = students_details.objects.using('mongodb').filter(**student_filters,del_row=False)
        # [data.update({'student_id':student_data.student_question_details}) for student_data in Student_details]
        return JsonResponse(response,safe=False,status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@api_view(['GET'])
def Student_performanceAnalysis(request,student_id):
    try:
        student_info = students_info.objects.get( student_id = student_id,del_row = False)
        PracticeQNs_score = students_details.objects.using('mongodb').get( student_id = student_id,\
                                                                del_row = "False"\
                                                                )
        assessments_objs = students_assessments.objects.filter(
                                    student_id=student_id,
                                    # assessment_status__in=['Completed'],
                                    del_row=False
                                ).values('assessment_type','subject_id__subject_id','course_id__course_id','assessment_week_number',
                                         'assessment_status','assessment_completion_time','assessment_max_score','assessment_score_secured',
                                         'student_test_completion_time')
        students_app_usage = student_app_usage.objects.filter(
                                    student_id = student_info,
                                    del_row=False
                                ).annotate(
                                    duration=ExpressionWrapper(F('logged_out') - F('logged_in'), output_field=DurationField())
                                ).values('logged_in__date').annotate(
                                    total_study_hours=Sum('duration')
                                )
        dates_list_weeks = course_plan_details.objects.filter(
                                    course_id = student_info.course_id,
                                    batch_id = student_info.batch_id,
                                    day_date__lte=timezone.now().__add__(timedelta(days=0, hours=5, minutes=30)),
                                    del_row = False
                                ).values('week','subject_id__subject_id').annotate(
                                    form_date = Min('day_date__date'),
                                    to_date = Max('day_date__date'),
                                    total_study_hours = Sum('duration_in_hours')
                                ).order_by('week')
        dates_list_weeks = {student_info.course_id.course_id+'_'+week.get('subject_id__subject_id')+'_week_'+str(week.get('week')):{
                'form_date':week.get('form_date'),
                'to_date':week.get('to_date'),
                'app_usage':sum([day.get('total_study_hours').total_seconds()/3600 for day in students_app_usage if day.get('logged_in__date') >= week.get('form_date') and day.get('logged_in__date') <= week.get('to_date')])
                ,'total_study_hours':week.get('total_study_hours')
                        }for week in dates_list_weeks}
        
        assessments = {
             assessment.get('course_id__course_id')+'_'+assessment.get('subject_id__subject_id')+'_'+str(assessment.get('assessment_week_number')): assessment
                        for assessment in assessments_objs if assessment.get('assessment_type') == 'Weekly Test'}
        # print(assessments)
        response = {
            'weeks':{},
            'cumulative':{}
        }
        for i in PracticeQNs_score.student_question_details:
            if response.get('weeks').get(i) == None:
                response.get('weeks').update({i:{}})
            if response.get('cumulative').get(i) == None:
                response.get('cumulative').update({i:{
                    'no_of_hours':'0/0','delays':0,
                    'practice_mcq_percentage':0,
                    'practice_coding_percentage':0,
                    'weekly_test_percentage':0,
                    'overall_percentage':0,
                    "Final_Test_score": "-/-",
                    "Final_Test_percentage": '--',
                    "Internship_Test_score": "-/-",
                    "Internship_Test_percentage": '--',

                    
                }})
            for j in PracticeQNs_score.student_question_details.get(i):
                for day in PracticeQNs_score.student_question_details.get(i).get(j):
                    if response.get('weeks').get(i).get(j) == None:
                        response.get('weeks').get(i).update({j:{
                            'week':j.split('_')[-1],
                            'no_of_hours':str(round(dates_list_weeks.get(i+'_'+j).get('app_usage'),2))+'/'+str(dates_list_weeks.get(i+'_'+j).get('total_study_hours')),
                            'delay':0,
                            'practice_mcq_score':'0/0',
                            'practice_mcq_percentage':0,
                            'practice_coding_score':'0/0',
                            'practice_coding_percentage':0,
                            'weekly_test_score':'0/0',
                            'weekly_test_percentage':0,
                            'overall_percentage':0
                        }})
                    day_data = PracticeQNs_score.student_question_details.get(i).get(j).get(day)
                    mcq_scored =float(response.get('weeks').get(i).get(j).get('practice_mcq_score','0/0').split('/')[0]) +float( day_data.get('mcq_score','0/0').split('/')[0])
                    mcq_total = float(response.get('weeks').get(i).get(j).get('practice_mcq_score','0/0').split('/')[1]) +float(day_data.get('mcq_score','0/0').split('/')[1])
                    coding_scored = float(response.get('weeks').get(i).get(j).get('practice_coding_score','0/0').split('/')[0]) +float(day_data.get('coding_score','0/0').split('/')[0])
                    coding_total = float(response.get('weeks').get(i).get(j).get('practice_coding_score','0/0').split('/')[1]) +float(day_data.get('coding_score','0/0').split('/')[1])
                    response.get('weeks').get(i).get(j).update({
                    'practice_mcq_score':str(mcq_scored)+"/"+str(mcq_total),
                    'practice_mcq_percentage':round(mcq_scored/mcq_total*100,2),
                    'practice_coding_score':str(coding_scored)+"/"+str(coding_total),
                    'practice_coding_percentage':round(coding_scored/coding_total*100,2)
                    })
                    practicemcqscored = float(response.get('cumulative').get(i).get('practice_mcq_score','0/0').split('/')[0]) +float( day_data.get('mcq_score','0/0').split('/')[0])
                    practicemcqtotal = float(response.get('cumulative').get(i).get('practice_mcq_score','0/0').split('/')[1]) +float(day_data.get('mcq_score','0/0').split('/')[1])
                    practicecodingscored = float(response.get('cumulative').get(i).get('practice_coding_score','0/0').split('/')[0]) +float(day_data.get('coding_score','0/0').split('/')[0])
                    practicecodingtotal = float(response.get('cumulative').get(i).get('practice_coding_score','0/0').split('/')[1]) +float(day_data.get('coding_score','0/0').split('/')[1])
                    response.get('cumulative').get(i).update({
                    'practice_mcq_score':str(practicemcqscored)+"/"+str(practicemcqtotal),
                    'practice_mcq_percentage':round(practicemcqscored/practicemcqtotal*100,2),
                    'practice_coding_score':str(practicecodingscored)+"/"+str(practicecodingtotal),
                    'practice_coding_percentage':round(practicecodingscored/practicecodingtotal*100,2)

                    })
                weekly_test_data = assessments.get(i+'_'+j.split('_')[1],{})
                delay = (weekly_test_data.get('student_test_completion_time') if weekly_test_data.get('student_test_completion_time') != None else timezone.now().__add__(timedelta(hours=5,minutes=30))) - \
                    (weekly_test_data.get('assessment_completion_time') if weekly_test_data.get('assessment_completion_time') != None else timezone.now().__add__(timedelta(days=0, hours=5, minutes=30)))
                delay = delay.days
                response.get('weeks').get(i).get(j).update({
                    'delay':delay if delay > 0 and delay <=3 else 3 if delay > 3 else 0,
                    'weekly_test_score': str(weekly_test_data.get('assessment_score_secured','0'))+"/"+str(weekly_test_data.get('assessment_max_score','0')),
                    'weekly_test_percentage': (round(weekly_test_data.get('assessment_score_secured',0)/weekly_test_data.get('assessment_max_score',0)*100,2))\
                        if weekly_test_data.get('assessment_max_score',0) != 0 else 0
                     
                })
                overall_percentage = (response.get('weeks').get(i).get(j).get('practice_mcq_percentage') + \
                                    response.get('weeks').get(i).get(j).get('practice_coding_percentage') + \
                                    response.get('weeks').get(i).get(j).get('weekly_test_percentage'))/3
                response.get('weeks').get(i).get(j).update({'overall_percentage':round(overall_percentage,2)})

                weekly_test_secured = float(response.get('cumulative').get(i).get('weekly_test','0/0').split('/')[0]) +float(weekly_test_data.get('assessment_score_secured','0'))
                weekly_test_max = float(response.get('cumulative').get(i).get('weekly_test','0/0').split('/')[1]) +float(weekly_test_data.get('assessment_max_score','0'))
                response.get('cumulative').get(i).update({
                    'weekly_test_score': str(weekly_test_secured)+"/"+str(weekly_test_max),
                    'weekly_test_percentage':(round( weekly_test_secured/weekly_test_max*100,2)) if weekly_test_max != 0 else 0,
                    'delays':response.get('cumulative').get(i).get('delays') + (delay if delay > 0 and delay <=3 else 3 if delay > 3 else 0),
                    
                })
            for h in dates_list_weeks:
             course_key = '_'.join(h.split('_')[0:2])
             if response.get('cumulative').get(course_key) == None:  
                response.get('cumulative').update({course_key:{}})
             hour_spent = response.get('cumulative').get(course_key).get('no_of_hours','0/0').split('/')[0]
             total_hours = response.get('cumulative').get(course_key).get('no_of_hours','0/0').split('/')[1]
             response.get('cumulative').get(course_key).update({
                'no_of_hours': str(round(float(hour_spent)+float(dates_list_weeks.get(h).get('app_usage')),2))+"/"+str(float(total_hours)+float(dates_list_weeks.get(h).get('total_study_hours'))),
                'no_of_hours_percentage': round((float(hour_spent)+float(dates_list_weeks.get(h).get('app_usage')))/(float(total_hours)+float(dates_list_weeks.get(h).get('total_study_hours')))*100,2)
            })
            for tests in assessments_objs:
                if tests.get('assessment_type') == 'Weekly Test':
                    continue
                if response.get('cumulative').get(tests.get('course_id__course_id')+'_'+tests.get('subject_id__subject_id')) == None:
                    response.get('cumulative').update({tests.get('course_id__course_id')+'_'+tests.get('subject_id__subject_id'):{
                    }})
                response.get('cumulative').get(tests.get('course_id__course_id')+'_'+tests.get('subject_id__subject_id')).update({
                    tests.get('assessment_type').replace(' ','_')+'_score': str(tests.get('assessment_score_secured'))+"/"+str(tests.get('assessment_max_score')),
                    tests.get('assessment_type').replace(' ','_')+'_percentage': round(tests.get('assessment_score_secured')/tests.get('assessment_max_score')*100,2)
                })

        response_data = {
            'data':{}
        }
        for i in response.get('weeks').keys():
            response_data.get('data').update({i.split('_')[-1]:{
                'weeks':[response.get('weeks').get(i).get(w) for w in response.get('weeks').get(i)],
                'cumulative':response.get('cumulative').get(i)
            }})
        response_data.update({
                'category':student_info.student_catogory,
                'college_rank':student_info.student_college_rank if student_info.student_college_rank >0 else '--',
                'overall_rank':student_info.student_overall_rank if student_info.student_overall_rank >0 else '--'
            })
            
                # response.get('weeks').get(i).update({j:PracticeQNs_score.student_question_details.get(i).get(j)})
        return JsonResponse(response_data,safe=False,status=200)
    except Exception as e:
        # print(e)
        return JsonResponse({'error': str(e)}, status=500)
