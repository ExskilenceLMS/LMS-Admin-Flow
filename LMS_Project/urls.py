"""LMS_Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from AdminFlow import course as course_views
from AdminFlow import views as admin_views
from AdminFlow import batch as batch_views
from AdminFlow import trainer as trainer_views
from AdminFlow import student as student_views
from AdminFlow import rules as rules_views
from AdminFlow import subjects as subjects_views
from AdminFlow import topics as topics_views
from AdminFlow import sub_topic as sub_topic_views
from AdminFlow import track as track_views
from AdminFlow import login as login_views

from AdminFlow.ContentCreation import sqlviews as sql_views
from AdminFlow.ContentCreation import contentCreation as content_creation_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path("/",admin_views.home,name="hello"),

    path('user/<str:mail>/',login_views.login,name="login"),
    path('add_admin/',login_views.add_admin,name="add_admin"),

    path("create_course/",course_views.create_course,name="create_course"),
    path("get_all_courses/",course_views.get_all_courses,name="get_all_courses"),
    path('delete_course/',course_views.delete_course,name="delete_course"),
    path('get_all_tracks_for_courses/',course_views.get_all_tracks_for_courses,name='get_all_tracks_for_courses'),


    path('get_all_courses_for_batch/',batch_views.get_all_courses_for_batch,name="get_all_courses_for_batch"),
    path('create_batch/', batch_views.create_batch,name="create_batch"),
    path('delete_batch/', batch_views.delete_batch,name="delete_batch"),
    path('get_all_batch/<str:course_id>/', batch_views.get_all_batch,name="get_all_batch"),
    path('create_trainer/',trainer_views.create_trainer,name="create_trainer"),
    path('get_all_trainer/',trainer_views.get_all_trainer,name="get_all_trainer"),
    path('delete_trainer/',trainer_views.delete_trainer,name="delete_trainer"),
    path('add_trainers_to_batch/',trainer_views.add_trainers_to_batch,name="add_trainers_to_batch"),
    path('get_trainer_for_batch/',trainer_views.get_trainer_for_batch,name="get_trainer_for_batch"),
    path('enable_trainer_for_batch/',trainer_views.enable_trainer_for_batch,name="enable_trainer_for_batch"),
    
    path('get_all_students/',student_views.get_all_students,name="get_all_students"),
    path('delete_student/',student_views.delete_student,name="delete_student"),
    path('create_student/',student_views.create_student,name="create_student"),
    path('allocate_student/',student_views.allocate_student,name="allocate_student"),
    path('import_students/',student_views.import_students,name="import_students"),
    path('get_students_of_batch/',student_views.get_students_of_batch,name="get_students_of_batch"),

    path('fetch_rules/',rules_views.fetch_rules,name="fetch_rules"),
    path('update_rules/',rules_views.update_rules,name="update_rules"),
    path('create_subject/',subjects_views.create_subject,name="create_subject"),
    path('get_all_subjects/',subjects_views.get_all_subjects,name="get_all_subjects"),
    path('delete_subject/',subjects_views.delete_subject,name='delete_subject'),
    path('subjects_for_topics/<str:track_id>/',topics_views.subjects_for_topics,name='subjects_for_topics'),
    path('get_all_topics/<str:subject_id>/', topics_views.get_all_topics, name="get_all_topics"),
    path('create_topic/', topics_views.create_topic,name="create_topic"),
    path('delete_topic/',topics_views.delete_topic,name='delete_topic'),
    path('delete_sub_topic/',sub_topic_views.delete_sub_topic,name='delete_sub_topic'),
    
    path('subjects_for_subTopics/<str:track_id>/',topics_views.subjects_for_topics,name='subjects_for_subTopics'),
    path('get_topics_for_subject/<str:subject_id>/',sub_topic_views.get_topics_for_subject,name='get_topics_for_subject'),
    path('create_subTopic/',sub_topic_views.create_subTopic,name='create_subTopic'),
    path('get_all_subTopics/<str:topic_id>/',sub_topic_views.get_all_subTopics,name='get_all_subTopics'),
    path('delete_sub_topic/',sub_topic_views.delete_sub_topic,name='delete_sub_topic'),

    path('create_track/',track_views.create_track,name='create_track'),
    path('get_all_tracks/',track_views.get_all_tracks,name='get_all_tracks'),











    path('Content_creation/dashboard-data/',content_creation_views.dashboard_data,name='dashboard_data'),
    path('Content_creation/topics_subtopics_by_subject/',content_creation_views.topics_subtopics_by_subject,name='topics_subtopics_by_subject'),
    path('Content_creation/get_count_of_questions/<str:subject_id>/',content_creation_views.get_count_of_questions,name='get_count_of_questions'),

    path('Content_creation/tables-data/',sql_views.get_tables_Data,name='get_tables_Data'),
    path('Content_creation/save/', sql_views.save, name='save'),
    path('Content_creation/execute-query/', sql_views.execute_query, name='execute-query'),

    path('Content_creation/Questions/', content_creation_views.get_questions_list, name='get_questions_list'),
    path('Content_creation/course-plan/',content_creation_views.course_Plan,name='course_Plan'),
    path('Content_creation/get_specific_question/',content_creation_views.get_specific_question,name="get_specific_questions"),
    path('Content_creation/get_content_for_subtopic/',content_creation_views.get_content_for_subtopic,name="get_content_for_subtopic"),
    path('Content_creation/content/',content_creation_views.content,name="content"),


]

