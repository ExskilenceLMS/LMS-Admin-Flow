
from django.urls import path
from . import views, Test_Creation as t_create, Test_Assign as t_assign, Test_Report as t_report , performanceAnalysis as t_analysis
from . import Trainer_tickets as tickets
urlpatterns = [
    path('login/<str:mail>/',views.trainer_Admin_Login,name="trainer_home"),
    # Test Creation
    path('tests/',t_create.test_creation,name="test_create"),
    path('filters/',views.get_filter_options,name="filters"),
    path('tests/get/<str:test_id>/',t_create.get_test_details,name="fetch tests"),
    path('tests/questions/',t_create.get_test_Questions,name="fetch questions"),
    path('tests/sections/',t_create.set_test_sections,name="save sections"),
    # Test Assign
    path('tests/get/',t_assign.get_tests_details,name="tests"),
    path('filters/assign/',t_assign.filter_for_assign_tests,name="filters for assigning"),
    path('test/assign/update/',t_assign.update_test_details,name="update test details"),
    path('filters/assign/<str:track>/',t_assign.filter_for_sorting_students,name="filters sorting students"),
    path('filters/assign/<str:course>/<str:batch>/<str:testID>/',t_assign.get_students,name="filters to get students"),
    path('tests/assign/',t_assign.assign_tests,name='Assign tests to students'),
    # Test Report
    path('filters/report/',t_report.filter_for_Test_Report,name="filters for report"),
    path('tests/report/',t_report.get_tests_Report_details,name="tests report"),
    path('tests/report/<str:testID>/',t_report.get_students_test_report,name="tests report"),
    # Performance Analysis
    path('filters/analysis/',t_analysis.filter_for_performanceAnalysis,name="filters for analysis"),
    path('analysis/',t_analysis.performanceAnalysis,name="performance analysis"),

    # tickets
    path('tickets/',tickets.fetch_all_tickets,name="tickets"),
    path('tickets/<str:student_id>/',tickets.fetch_student_tickets,name="tickets"),
    path('ticket/comments/',tickets.trainer_side_comments_for_tickets,name="ticket details"),
]