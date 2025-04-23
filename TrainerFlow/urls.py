
from django.urls import path
from . import views, Test_Creation as t_create, Test_Assign as t_assign

urlpatterns = [
    path('login/<str:mail>/',views.trainer_Admin_Login,name="trainer_home"),
    # Test Creation
    path('tests/',t_create.test_creation,name="test_create"),
    path('filters/',views.get_filter_options,name="filters"),
    path('tests/get/',t_create.get_tests_details,name="tests"),
    path('tests/get/<str:test_id>/',t_create.get_test_details,name="tests"),
    path('tests/questions/',t_create.get_test_Questions,name="tests"),
    path('tests/sections/',t_create.set_test_sections,name="tests"),
    # Test Assign
    path('filters/assign/',t_assign.filter_for_assign_tests,name="filters for assigning"),
    path('test/assign/update/',t_assign.update_test_details,name="update test details"),
    path('filters/assign/<str:track>/',t_assign.filter_for_sorting_students,name="filters sorting students"),
    path('filters/assign/<str:course>/<str:batch>/',t_assign.get_students,name="filters to get students"),
    path('tests/assign/',t_assign.assign_tests,name='Assign tests to students'),

]