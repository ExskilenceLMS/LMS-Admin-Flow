from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
import time
from LMS_Mongodb_App.models import *
from AdminFlow.collegeBranch import generate_id
@api_view(['POST'])
def get_all_students(request):
    try:
        batch_id=request.data.get('batch_id')
        all_students = students_info.objects.filter(del_row=False, batch_id=batch_id)  
        students_list = []
        for student in all_students:
            student_data =  {
                "student_id": student.student_id,
                "student_firstname": student.student_firstname,
                "course_id": student.course_id.course_id,
                "batch_id": student.batch_id.batch_id,
                "student_lastname": student.student_lastname,
                "student_email": student.student_email,
                "student_gender": student.student_gender,
                "student_country": student.student_country,
                "student_state": student.student_state,
                "student_city": student.student_city,
                "student_dob": student.student_dob,
                "student_address": student.address,
                "student_pincode": student.student_pincode,
                "student_phone": student.phone,
                "student_altphone": student.student_alt_phone,
                "student_isActive": student.isActive,
                "student_qualification": student.student_qualification,
                "student_type": student.student_type,
                "college": student.college,
                "branch": student.branch,
                "allocate": student.allocate
        }
            students_list.append(student_data)
        return JsonResponse({'students': students_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['POST'])
def get_students_of_batch(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            batch_id=data['batch_id']
            batch_instance = batches.objects.get(batch_id=batch_id)
            course_id=data['course_id']
            course_instance = courses.objects.get(course_id=course_id)
            all_students = students_info.objects.filter(del_row=False, batch_id=batch_instance, course_id =course_instance   )  
            students_list = []
            for student in all_students:
                student_data =  {
                    "student_id": student.student_id,
                    "student_firstname": student.student_firstname,
                    "course_id": student.course_id.course_id,
                    "batch_id": student.batch_id.batch_id,
                    "student_lastname": student.student_lastname,
                    "student_email": student.student_email,
                    "student_gender": student.student_gender,
                    "student_country": student.student_country,
                    "student_state": student.student_state,
                    "student_city": student.student_city,
                    "student_dob": student.student_dob,
                    "student_address": student.address,
                    "student_pincode": student.student_pincode,
                    "phone": student.phone,
                    "student_altphone": student.student_alt_phone,
                    "isActive": student.isActive,
                    "student_qualification": student.student_qualification,
                    "student_type": student.student_type,
                    "college": student.college,
                    "branch": student.branch,
                    "allocate": student.allocate
            }
                students_list.append(student_data)
            return JsonResponse({'students': students_list,'max':batch_instance.max_no_of_students})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def delete_student(request):
    try:
        data = json.loads(request.body)
        student = students_info.objects.get(student_id=data['id'])
        student.del_row = True
        student.save()  
        return JsonResponse({'message': 'Student deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def create_stud(req):
    try:
        if not isinstance(req, dict):
            raise ValueError("Request data must be a dictionary")
        data = req
        print("Received data:", data)
        student_id = data.get('student_id')
        if not student_id or not isinstance(student_id, str):
            raise ValueError("Student ID must be a non-empty string")

        print("Checking if student exists with ID:", student_id)
        if students_details.objects.using('mongodb').filter(student_id=student_id).exists():
            print('Student already exists')
            return HttpResponse("Student already exists")
        else:
            print('Adding new student')
            student = students_details(
                student_id=student_id
            )
            student.save(using='mongodb')
            return HttpResponse("Added Successfully")
    except Exception as e:
        print("Error:", e)
        return HttpResponse("Failed")

@api_view(['POST'])
def create_student(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['student_firstname', 'student_lastname', 'student_email', 'student_gender', 'phone', 'student_type']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

            student_id = data.get('student_id', None)
            student_dob = data.get("student_dob", None)
            if student_dob:
                try:
                    dob = datetime.fromisoformat(student_dob)  
                except ValueError:
                    return JsonResponse({'error': f'Invalid date format for student_dob. Expected ISO format.'}, status=400)
            else:
                dob = None  
            if student_id:
                try:
                    student = students_info.objects.get(student_id=student_id)
                    try:
                        
                        course_instance = courses.objects.get(course_id=data["course_id"])
                    except courses.DoesNotExist:
                        return JsonResponse({'error': 'Course not found'}, status=404)

                    try:
                        batch_instance = batches.objects.get(batch_id=data['batch_id'])
                    except batches.DoesNotExist:
                        return JsonResponse({'error': 'Batch not found'}, status=404)

                    student.course_id = course_instance
                    student.student_firstname = data.get("student_firstname", student.student_firstname)
                    student.student_lastname = data.get("student_lastname", student.student_lastname)
                    student.student_email = data.get("student_email", student.student_email)
                    student.student_country = data.get("student_country", student.student_country)
                    student.student_state = data.get("student_state", student.student_state)
                    student.student_city = data.get("student_city", student.student_city)
                    student.student_gender = data.get("student_gender", student.student_gender)
                    student.student_pincode = data.get("student_pincode", student.student_pincode)
                    student.student_alt_phone = data.get("student_altphone", student.student_alt_phone)
                    student.isActive = data.get("isActive", student.isActive)
                    student.student_dob = dob
                    student.student_qualification = data.get("student_qualification", student.student_qualification)
                    student.batch_id = batch_instance
                    student.address = data.get("address", student.address)
                    student.phone = data.get("phone", student.phone)
                    student.student_type = data.get("student_type", student.student_type)
                    student.college = data.get("college", student.college)
                    student.branch = data.get("branch", student.branch)
                    student.allocate=data.get("allocate", student.allocate)
                    student.save()
                    create_stud({"student_id":data.get('student_id')})
                    
                    return JsonResponse({'message': 'Student updated successfully'}, status=200)

                except students_info.DoesNotExist:
                    return JsonResponse({'error': 'Student not found'}, status=404)

            else:
                existing_count = students_info.objects.count() + 1
                course_instance = courses.objects.get(course_id=data["course_id"])
                # generated_student_id = f'Stud{existing_count}'
                batch_instance = batches.objects.get(batch_id=data['batch_id'])
                
                new_student = students_info(
                    student_id=generate_id(data['college'],data['branch'],data['student_type'][0]),
                    course_id=course_instance,
                    student_firstname=data.get("student_firstname", None),
                    student_lastname=data.get("student_lastname", None),
                    student_email=data.get("student_email", None),
                    student_country=data.get("student_country", None),
                    student_state=data.get("student_state", None),
                    student_city=data.get("student_city", None),
                    student_gender=data.get("student_gender", None),
                    student_pincode=data.get("student_pincode", None),
                    student_alt_phone=data.get("student_altphone", None),
                    isActive=data.get("isActive", None),
                    student_dob=dob,
                    student_qualification=data.get("student_qualification", None),
                    batch_id=batch_instance,
                    address=data.get("address", None),
                    phone=data.get("phone", None),
                    student_type=data.get("student_type", None),
                    college=data.get("college", None),
                    branch=data.get("branch", None),
                    allocate=data.get("allocate", None)
                )
                res=create_stud({"student_id":new_student.student_id})
                print(res)
                new_student.save()
                return JsonResponse({'message': 'Student created successfully'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def allocate_student(request):
    try:
        data = json.loads(request.body)
        student = students_info.objects.get(student_id=data['student_id'])
        student.allocate = not(student.allocate)
        student.save()
        return JsonResponse({'data': not(student.allocate)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def import_students(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    course_id = data.get('course_id')
    batch_id = data.get('batch_id')
    students_data = data.get("data")

    edited_count = 0
    edited_student = ""
    saved_count = 0
    error_count = 0
    saved_student = ""
    error_student = ""
    max_students_reached = ""

    try:
        batch_instance = batches.objects.get(batch_id=batch_id)
    except batches.DoesNotExist:
        return JsonResponse({
            'message': 'Batch does not exist',
            'error_count': 1
        }, status=400)

    current_student_count = students_info.objects.filter(batch_id=batch_instance, del_row=False).count()
    max_students = batch_instance.max_no_of_students

    for student in students_data:
        student_email = student["EmailId"]
        exist = students_info.objects.filter(student_email=student_email).first()

        if exist:
            try:
                course_instance = courses.objects.get(course_id=course_id)
            except courses.DoesNotExist:
                error_count += 1
                error_student += f"{student_email}, "
                continue

            dob_str = student["DOB"]
            if dob_str == "":
                dob = None
            else:
                try:
                    if len(dob_str.split('/')[-1]) == 4:
                        dob = datetime.strptime(dob_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                    else:
                        dob = datetime.strptime(dob_str, '%d/%m/%y').strftime('%Y-%m-%d')
                except ValueError:
                    error_count += 1
                    error_student += f"{student_email}, "
                    continue

            is_active = student["IsActive"].upper() == "TRUE"
            allocate_value = student["Allocate"].upper() == "TRUE"
            print('drtyuikol;bguik',exist.student_id)
            create_stud({"student_id":exist.student_id})
            exist.student_firstname = student["FirstName"]
            exist.student_lastname = student["LastName"]
            exist.course_id = course_instance
            exist.batch_id = batch_instance
            exist.student_email = student_email
            exist.student_dob = dob
            exist.student_gender = student["Gender"]
            exist.student_country = student["Country"]
            exist.student_state = student["State"]
            exist.student_city = student["City"]
            exist.address = student["Address"]
            exist.student_pincode = student["Pincode"]
            exist.phone = student["Mobile"]
            exist.student_alt_phone = student["AltMobile"]
            exist.isActive = is_active
            exist.student_qualification = student["Qualification"]
            exist.student_type = student["StudentType"]
            exist.college = student["College"]
            exist.branch = student["Branch"]
            exist.allocate = allocate_value
            exist.save()
            edited_count += 1
            edited_student += f"{student_email}, "

        else:
            if current_student_count >= max_students:
                max_students_reached += f"{student_email}, "
                continue

            try:
                course_instance = courses.objects.get(course_id=course_id)
            except courses.DoesNotExist:
                error_count += 1
                error_student += f"{student_email}, "
                continue

            dob_str = student["DOB"]
            try:
                if len(dob_str.split('/')[-1]) == 4:
                    dob = datetime.strptime(dob_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                else:
                    dob = datetime.strptime(dob_str, '%d/%m/%y').strftime('%Y-%m-%d')
            except ValueError:
                error_count += 1
                error_student += f"{student_email}, "
                continue

            is_active = student["IsActive"].upper() == "TRUE"
            allocate_value = student["Allocate"].upper() == "TRUE"

            id = generate_id(student['College'], student['Branch'], student['StudentType'][0])
            new_student = students_info(
                student_id=id,
                student_firstname=student["FirstName"],
                student_lastname=student["LastName"],
                course_id=course_instance,
                batch_id=batch_instance,
                student_email=student_email,
                student_dob=dob,
                student_gender=student["Gender"],
                student_country=student["Country"],
                student_state=student["State"],
                student_city=student["City"],
                address=student["Address"],
                student_pincode=student["Pincode"],
                phone=student["Mobile"],
                student_alt_phone=student["AltMobile"],
                isActive=is_active,
                student_qualification=student["Qualification"],
                student_type=student["StudentType"],
                college=student["College"],
                branch=student["Branch"],
                allocate=allocate_value
            )
            new_student.save()
            res=create_stud({"student_id":new_student.student_id})
            current_student_count += 1
            saved_count += 1
            saved_student += f"{student_email}, "

    response_data = {
        'message': 'Students imported successfully',
        'edited_count': edited_count,
        'saved_count': saved_count,
        'error_count': error_count,
        'edited_student': edited_student,
        'saved_student': saved_student,
        'error_student': error_student,
    }

    if max_students_reached:
        response_data['max_students_reached'] = 'Maximum no of students was ' + str(max_students) + '. Hence these students were not added: ' + max_students_reached

    return JsonResponse(response_data)


@api_view(['POST'])
def check_mail_and_number(request):
    try:
        request_data = json.loads(request.body)
        email = request_data.get('email')

        try:
            student = students_info.objects.get(student_email=email)

            student_data = {
                "student_id": student.student_id,
                "course_id": student.course_id.course_id,
                "student_firstname": student.student_firstname,
                "student_lastname": student.student_lastname,
                "student_email": student.student_email,
                "student_country": student.student_country,
                "student_state": student.student_state,
                "student_city": student.student_city,
                "student_gender": student.student_gender,
                "student_pincode": student.student_pincode,
                "student_alt_phone": student.student_alt_phone,
                "isActive": student.isActive,
                "student_dob": student.student_dob,
                "student_qualification": student.student_qualification,
                "batch_id": student.batch_id.batch_id,
                "address": student.address,
                "phone": student.phone,
                "student_type": student.student_type,
                "college": student.college,
                "branch": student.branch,
                "allocate": student.allocate,
            }

            return JsonResponse({'data': student_data})

        except students_info.DoesNotExist:
            return JsonResponse({'data': None})  # This will trigger the `else` on frontend

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

