import json
import random
from azure.storage.blob import BlobServiceClient
from LMS_Project.settings import *
from django.core.cache import cache

def get_blob_service_client():
    account_name = AZURE_ACCOUNT_NAME
    account_key = AZURE_ACCOUNT_KEY
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    return BlobServiceClient.from_connection_string(connection_string)
def get_blob_container_client():
    account_name = AZURE_ACCOUNT_NAME
    account_key = AZURE_ACCOUNT_KEY
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    return BlobServiceClient.from_connection_string(connection_string).get_container_client(AZURE_CONTAINER)

def get_blob(blob_name):
    # cacheresponse = cache.get(blob_name)
    # if cacheresponse:
    #     # print('cache hit')
    #     cache.set(blob_name,cacheresponse)
    #     return cacheresponse
    blob_client = get_blob_container_client().get_blob_client(blob_name)
    # cache.set(blob_name,json.loads(blob_client.download_blob().readall()))
    # blob_client.close()
    return blob_client.download_blob().readall()
    # blob_client.close()
    # return cache.get(blob_name)

def get_list_blob(blob_path,list_of_qns,type):
    container_client =  get_blob_container_client()
    files = []
    for Qn in list_of_qns:
        path = f'{blob_path}{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type}/{Qn}.json'
        cacheres = cache.get(path)
        if cacheres:
            # print('cache hit')
            cache.set(path,cacheres)
            blob_data = cacheres
        else:
            blob_client = container_client.get_blob_client(path)
            blob_data = json.loads(blob_client.download_blob().readall())
            cache.set(path,blob_data)
        blob_data.update({ "Qn_name": Qn})
        files.append(blob_data)
    container_client.close()
    return files
def get_random_questions(types,subtops,levels):
    try:
        container_client =  get_blob_container_client()
        files = {}
        cacheresponse = cache.get('lms_rules/rules.json')
        if cacheresponse:
            # print('cache hit')
            cache.set('lms_rules/rules.json',cacheresponse)
            Rules = cacheresponse
        else:
            blob_client = container_client.get_blob_client('lms_rules/rules.json')
            Rules = json.loads(blob_client.download_blob().readall())
            cache.set('lms_rules/rules.json',Rules)
        for type in types:
            for subtop in subtops:
                cacheed_lists = cache.get(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/')
                if cacheed_lists:
                    cache.set(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/',cacheed_lists)
                    all_qns_list = cacheed_lists
                else:
                    all_qns_list =container_client.list_blobs(
                                    name_starts_with =f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/')
                    cache.set(f'subjects/{subtop[0:2]}/{subtop[0:-2]}/{subtop}/{type.lower()}/',all_qns_list)
                all_qns = [blob.name.split('/')[-1].split('.')[0] for blob in all_qns_list]
                Easy    = [qn for qn in all_qns if qn[-4]=='e']
                Medium  = [qn for qn in all_qns if qn[-4]=='m']
                Hard    = [qn for qn in all_qns if qn[-4]=='h']
                Qns     = []
                if len(Easy) > 0 :
                    Qns.extend(random.sample(Easy, levels.get(type,{}).get(subtop,{}).get('level1',0)))
                if len(Medium)>0:
                    Qns.extend(random.sample(Medium, levels.get(type,{}).get(subtop,{}).get('level2',0)))
                if len(Hard)>0:
                    Qns.extend(random.sample(Hard, levels.get(type,{}).get(subtop,{}).get('level3',0)))
                score = 0
                l1 =0
                l2 =0
                l3 =0
                for Qn in Qns:
                    level =  'Level'+('1' if Qn[-4].lower()=='e' else '2' if Qn[-4].lower()=='m' else '3' if Qn[-4].lower()=='h' else '3')
                    if level == 'Level1':
                        l1 = l1+1
                    if level == 'Level2':
                        l2 = l2+1
                    if level == 'Level3':
                        l3 = l3+1
                for level in Rules.get(type.lower(),[]):
                    if level.get('level').lower() == 'level1':
                        level_score = l1*int(level.get('score'))
                    if level.get('level').lower() == 'level2':
                        level_score = l2*int(level.get('score'))
                    if level.get('level').lower() == 'level3':
                        level_score = l3*int(level.get('score'))
                    score = score +level_score
                # Scoring works if all the questions are there
                
                # for level in Rules.get(type.lower(),[]):
                #     level_score = int(levels.get(type,{}).get(subtop,{}).get(level.get('level').lower(),0))*int(level.get('score'))
                #     score = score +level_score
                files.update({type:files.get(type,[])+Qns,
                            type+'_score':files.get(type+'_score',0)+score})
        container_client.close()
        return files
    except Exception as e :
        return 'error'
# def get_blob_list(blob_name):
#     container_client = get_blob_container_client()

#     blob_list = container_client.list_blobs(name_starts_with=blob_name)
    
#     for blob in blob_list:
#         blob_client = container_client.get_blob_client(blob['name'])
#         blob_properties = blob_client.get_blob_properties()

#         print(f"Blob Name: {blob['name']}")
#         print(f"Last Modified: {blob_properties['last_modified']}")
#         print(f"Blob Size: {blob_properties['size']} bytes")
#         print(f"Blob Content Type: {blob_properties['content_settings'].content_type}")

#     return blob_list
# def get_questions_staus(blob_path,list_of_qns,type):
#     container_client =  get_blob_container_client()
#     files = []
#     cacheresponse = cache.get('LMS_Rules/Rules.json')
#     if cacheresponse:
#         # print('cache hit')
#         cache.set('LMS_Rules/Rules.json',cacheresponse)
#         Rules = cacheresponse
#     else:
#         blob_client = container_client.get_blob_client('LMS_Rules/Rules.json')
#         Rules = json.loads(blob_client.download_blob().readall())
#         cache.set('LMS_Rules/Rules.json',Rules)
#     print(type)
#     if type.lower() == 'mcq':
#         for Qn in list_of_qns:
#             path = f'{blob_path}{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type}/{Qn}.json'
#             cacheres = cache.get(path)
#             if cacheres:
#                 # print('cache hit')
#                 cache.set(path,cacheres)
#                 blob_data = cacheres
#             else:
#                 blob_client = container_client.get_blob_client(path)
#                 blob_data = json.loads(blob_client.download_blob().readall())
#                 cache.set(path,blob_data)
#             blob_data.update({'Qn_name':Qn,'maxscore':Rules.get(type.lower(),[])[0].get('score')})
#             files.append(blob_data)
#     elif type.lower() == 'coding':
#         for Qn in list_of_qns:
#             path = f'{blob_path}{Qn[1:3]}/{Qn[1:-7]}/{Qn[1:-5]}/{type}/{Qn}.json'
#             cacheres = cache.get(path)
#             if cacheres:
#                 # print('cache hit')
#                 cache.set(path,cacheres)
#                 blob_data = cacheres
#             else:
#                 blob_client = container_client.get_blob_client(path)
#                 blob_data = json.loads(blob_client.download_blob().readall())
#                 cache.set(path,blob_data)
#             blob_data.update({'Qn_name':Qn,'maxscore':Rules.get(type.lower(),[])[0].get('score')})
#             files.append(blob_data)
#     print(files)
#     container_client.close()
#     return files
# import uuid
# from azure.storage.blob import ContentSettings
# def upload_video_to_blob(file):

#     container_client = get_blob_container_client()

#     blob_name = f"videos/{uuid.uuid4()}_{file.name}"
#     blob_client = container_client.get_blob_client(blob_name)
#     # blob_client.set_http_headers(content_type='video/mp4')
#     content_type = 'video/mp4'
#     blob_client.upload_blob(file, overwrite=True,content_settings=ContentSettings(content_type=content_type))
    
#     path = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/{blob_name}"
#     blob_client.close()

#     return path