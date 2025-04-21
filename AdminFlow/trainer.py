from django.shortcuts import render
from LMS_MSSQLdb_App.models import *
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
import pytz
from datetime import datetime, timedelta
from LMS_Mongodb_App.models import *
from itertools import chain
import time
@api_view(['POST'])
def create_trainer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            required_fields = ['name', 'mobile_no', 'email_id','gender','address']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
            trainer_id = data.get('id', None)

            if trainer_id:
                try:
                    trainer = trainers.objects.get(trainer_id=trainer_id)
                    trainer.trainer_name = data.get('name', trainer.trainer_name)
                    trainer.phone = data.get('mobile_no', trainer.phone)
                    trainer.trainer_email = data.get('email_id', trainer.trainer_email)
                    trainer.gender = data.get('gender', trainer.gender)
                    trainer.address = data.get("address", trainer.address)
                    trainer.save()

                    return JsonResponse({'message': 'Trainer updated successfully'}, status=200)

                except trainers.DoesNotExist:
                    return JsonResponse({'error': 'Trainer not found'}, status=404)

            else:
                existing_count = trainers.objects.count() + 1
                generated_trainer_id = f'trainee{existing_count}'
                new_trainer = trainers(
                    trainer_id=generated_trainer_id,
                    trainer_name=data['name'],
                    phone=data['mobile_no'],
                    trainer_email=data['email_id'],
                    gender=data['gender'],
                    address=data["address"],
                )
                new_trainer.save()  

                return JsonResponse({'message': 'Trainer created successfully'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def get_all_trainer(request):
    try:
        all_trainers = trainers.objects.filter()  
        trainers_list = []
        
        for trainer in all_trainers:
            course_data = {
                'id': trainer.trainer_id,
                'name': trainer.trainer_name,
                'email_id': trainer.trainer_email,
                'gender': trainer.gender,
                'mobile_no': trainer.phone,
                'address':trainer.address,
                'del_row': trainer.del_row
            }
            trainers_list.append(course_data)
        return JsonResponse({'trainers': trainers_list})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
   

@api_view(['POST'])
def delete_trainer(request):
    try:
        data = json.loads(request.body)
        trainer = trainers.objects.get(trainer_id=data['id'])
        trainer.del_row = True
        trainer.save()  
        return JsonResponse({'message': 'Trainer deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def get_trainer_for_batch(request):
    try:
        data = json.loads(request.body)
        batch_id = data["batch_id"]
        trainer_list=[]


        trainer_objects1 = trainers_details.objects.using('mongodb').filter(batch_ids={batch_id: False}).all()
        trainer_objects2 = trainers_details.objects.using('mongodb').filter(batch_ids={batch_id: True}).all()
        print('trainer object1',trainer_objects1)
        print("Trainer object 2",trainer_objects2)
        trainer_objects = list(chain(trainer_objects1, trainer_objects2))
        print('abc')
        for trainer in trainer_objects:
            print(trainer)
            x=trainers.objects.get(trainer_id=trainer.trainer_id)
            each_trainer={
                "id":x.trainer_id,
                "trainer_name":x.trainer_name,
                "enabled":trainer.batch_ids[batch_id]
            }
            print(x)
            trainer_list.append(each_trainer)
        return JsonResponse({'trainers': trainer_list})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


@api_view(['POST'])
def add_trainers_to_batch(request):
    try:
        data = json.loads(request.body)
        trainer = data['trainer_id']
        batch_id = data['batch_id']
        trainer_instance = trainers_details.objects.using('mongodb').filter(trainer_id=trainer).first()
        print("1",trainer_instance)
        if trainer_instance: 
            print("if condition",trainer_instance.batch_ids)
            if (trainer_instance.batch_ids.get(batch_id)==True or trainer_instance.batch_ids.get(batch_id)==False):
                print("2nd if condition")
                trainer_instance.batch_ids.pop(batch_id)
                trainer_instance.save()
            else:
                print("else condition")
                trainer_instance.batch_ids.update({batch_id: False})
        
                trainer_instance.save()
        else:
            trainers_details.objects.using('mongodb').create(
                trainer_id=trainer,
                batch_ids={batch_id: False}  
            )

        return JsonResponse({'message': 'Trainer added successfully'})
    except Exception as e:
        print("Error:", e)
        return JsonResponse({'error': str(e)}, status=500)
    


@api_view(['POST'])
def enable_trainer_for_batch(request):
    try:
        data = json.loads(request.body)
        trainer_id = data['trainer_id']
        batch_id = data['batch_id']
        trainer_instance = trainers_details.objects.using('mongodb').filter(trainer_id=trainer_id).first()
        if trainer_instance:
            trainer_instance.batch_ids[batch_id] = not(trainer_instance.batch_ids[batch_id])
            trainer_instance.save()
            return JsonResponse({'message': 'Trainer enabled successfully'})
        else:
            return JsonResponse({'error': 'Trainer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)