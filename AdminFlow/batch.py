from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta


@api_view(['GET'])
def get_all_courses_for_batch(request):
    try:
        all_courses = courses.objects.filter(del_row=False)  
        courses_list = []
        for course in all_courses:
            course_data = {
                'course_id': course.course_id,
                'course_name': course.course_name,
            }
            courses_list.append(course_data)
        return JsonResponse({'courses': courses_list})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def create_batch(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            if 'batch_id' not in data:  
                existing_batch_count = batches.objects.count() + 1
                batch_id = f'batch{existing_batch_count}'
                try:
                    course_instance = courses.objects.get(course_id=data["course_id"])
                except courses.DoesNotExist:
                    return JsonResponse({'error': f'Course with ID {data["course_id"]} not found.'}, status=400)
                batch = batches(
                    course_id=course_instance, 
                    batch_id=batch_id,
                    batch_name=data['batch_name'],
                    delivery_type=data['delivery_type'],
                    max_no_of_students=data['max_no_of_students'],
                    start_date=data['start_date'],
                    indicative_date=data['indicative_date']
                )
                batch.save()  
            elif 'batch_id' in data:
                try:
                    batch = batches.objects.get(batch_id=data['batch_id'])
                    if 'course_id' in data:
                        try:
                            course_instance = courses.objects.get(course_id=data["course_id"])
                            batch.course_id = course_instance  
                        except courses.DoesNotExist:
                            return JsonResponse({'error': f'Course with ID {data["course_id"]} not found.'}, status=400)
                    batch.batch_name = data.get('batch_name', batch.batch_name)
                    batch.delivery_type = data.get('delivery_type', batch.delivery_type)
                    batch.max_no_of_students = data.get('max_no_of_students', batch.max_no_of_students)
                    batch.start_date = data.get('start_date', batch.start_date)
                    batch.indicative_date = data.get('indicative_date', batch.indicative_date)
                    batch.save()  

                except batches.DoesNotExist:
                    return JsonResponse({'error': 'Batch not found'}, status=404)

            return JsonResponse({'message': 'Batch created/updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
      
@api_view(['GET'])
def get_all_batch(request, course_id):
    try:
        try:
            course_instance = courses.objects.get(course_id=course_id)
        except courses.DoesNotExist:
            return JsonResponse({'error': f'Course with ID {course_id} not found.'}, status=404)
        batches_list = batches.objects.filter(course_id=course_instance, del_row=False)
        if not batches_list:
            return JsonResponse({'batches': []}, status=200)

        batch_data = []
        for batch in batches_list:
            batch_data.append({
                'batch_id': batch.batch_id,
                'batch_name': batch.batch_name,
                'delivery_type': batch.delivery_type,
                'max_no_of_students': batch.max_no_of_students,
                'start_date': batch.start_date.strftime('%Y-%m-%d'),  
                'indicative_date': batch.indicative_date.strftime('%Y-%m-%d')  
            })
        return JsonResponse({'batches': batch_data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def delete_batch(request):
    try:
        data = json.loads(request.body)
        batch = batches.objects.get(batch_id=data['batch_id'])
        batch.del_row = True
        batch.save()  
        return JsonResponse({'message': 'Batch deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

