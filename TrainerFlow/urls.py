
from django.urls import path
from . import views, Test_Creation as t_create

urlpatterns = [
    path('login/<str:mail>/',views.trainer_Admin_Login,name="trainer_home"),
    path('tests/',t_create.test_creation,name="test_create"),
    path('filters/',views.get_filter_options,name="filters"),
    path('tests/get/',t_create.get_tests_details,name="tests"),
    path('tests/get/<str:test_id>/',t_create.get_test_details,name="tests"),
    path('tests/questions/',t_create.get_test_Questions,name="tests"),
    path('tests/sections/',t_create.set_test_sections,name="tests"),
]