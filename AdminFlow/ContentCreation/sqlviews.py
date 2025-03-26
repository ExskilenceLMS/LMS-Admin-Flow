from decimal import Decimal
import json
import random
import re
from django.http import HttpResponse
from LMS_Project.settings import *
from rest_framework.decorators import api_view
from datetime import date, datetime, time, timedelta
from LMS_MSSQLdb_App.models import *
import pyodbc
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from azure.storage.blob import ContentSettings
import os
from azure.storage.blob import BlobServiceClient

blob_service_client = BlobServiceClient(account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/",credential=AZURE_ACCOUNT_KEY)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

@api_view(['GET'])
def get_tables_Data(request):
    try:
        data = get_all_tables()
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_all_tables():
    try:
        connection_string = (f'Driver={MSSQL_DRIVER};'
                             f'Server={MSSQL_SERVER_NAME};'
                             f'Database={MSSQL_DATABASE_NAME};'
                             f'UID={MSSQL_USERNAME};'
                             f'PWD={MSSQL_PWD};')
        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        result = {}

        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG='exe_test'")
        tables = [row.TABLE_NAME for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            data = extract_table_rows(rows, columns)
            result[table] = data

        return result
    except Exception as e:
        raise Exception("Error getting tables: " + str(e))
    

def extract_table_rows(rows, columns):
    try:
        data = []
        for row in rows:
            row_data = {}
            for i, value in enumerate(row):
                if isinstance(value, date) or isinstance(value, datetime) or isinstance(value, time):
                    row_data[columns[i]] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_data[columns[i]] = float(value)
                elif value is None:
                    row_data[columns[i]] = 'NULL'
                else:
                    row_data[columns[i]] = value
            data.append(row_data)
        return data
    except Exception as e:
        raise Exception("Error extracting table rows: " + str(e))


@api_view(['POST'])
@csrf_exempt
def save(request):
    data = request.data
    subtopic_id = data.get('subtopic_id')
    level = data.get('level')
    content_type = data.get('type')
    current_file = data.get('currentFile')
    last_updated_by = data.get('Last_Updated_by')

    subject_id = subtopic_id[:2]
    topic_id = subtopic_id[:-2]

    subtopic_folder = f"LMSActualData/{subject_id}/{topic_id}/{subtopic_id}/"

    level_char = level[0].lower()

    def get_next_number(folder_path, file_pattern):
        existing_files = list(container_client.list_blobs(name_starts_with=folder_path))
        existing_numbers = set()

        for blob in existing_files:
            filename = blob.name.split('/')[-1]
            if file_pattern in filename:
                try:
                    number = int(filename.split('m')[-1].split('.')[0])
                    existing_numbers.add(number)
                except ValueError:
                    continue

        if not existing_numbers:
            return 1

        for i in range(1, max(existing_numbers) + 2):
            if i not in existing_numbers:
                return i

        return max(existing_numbers) + 1

    if content_type == 'coding':
        query = data.get('Query')
        table = data.get('Table')
        test_cases = data.get('TestCases')
        explanation = data.get('Expl')

        if not query or not table:
            return JsonResponse({"error": "Query and Table are required"}, status=400)

        try:
            expected_output = execute_query_and_get_output(query)
            test_cases.append({"Testcase": expected_output})

            if current_file:
                try:
                    blob_name = f"{subtopic_folder}Coding/{current_file}"
                    blob_client = container_client.get_blob_client(blob_name)

                    if not blob_client.exists():
                        return JsonResponse({'error': f'File {current_file} not found.'}, status=404)

                    update_data = {
                        'Last_Updated_by': last_updated_by,
                        'level': level,
                        'subtopic_id': subtopic_id,
                        'Name': data.get('Name'),
                        'QNty': data.get('QNty'),
                        'QnTy': data.get('QnTy'),
                        'Qn': data.get('Qn'),
                        'Query': data.get('Query'),
                        'Table': data.get('Table'),
                        'TestCases': data.get('TestCases'),
                        'ExpectedOutput': expected_output , 
                        'Tags': data.get('Tags'),
                        'Template': data.get('Template'),
                        'Examples': data.get('Examples'),
                        'Ans': data.get('Ans'),
                        'FunctionCall': data.get('FunctionCall'),
                        'Explanations': data.get('Explanations'),
                        'Hints': data.get('Hints'),
                        'currentFile': current_file,
                        'LastUpdated': data.get('LastUpdated'),
                        
                    }

                    json_data = json.dumps(update_data, ensure_ascii=False)
                    encoded_data = json_data.encode('utf-8')

                    blob_client.upload_blob(
                        encoded_data,
                        overwrite=True,
                        content_settings=ContentSettings(
                            content_type='application/json',
                            charset='utf-8'
                        )
                    )

                    qn_id = os.path.splitext(current_file)[0]
                    question = questions.objects.get(question_id=qn_id)
                    question.last_updated_by = last_updated_by
                    question.tags = ','.join(data.get('Tags', [])) if isinstance(data.get('Tags'), list) else data.get('Tags', '')
                    question.save()

                    return JsonResponse({
                        'message': 'Question updated successfully',
                        'blob_name': blob_name
                    })

                except Exception as e:
                    print(f"Error updating blob: {str(e)}")
                    return JsonResponse({
                        'error': f'Failed to update question: {str(e)}',
                        'blob_name': blob_name if 'blob_name' in locals() else 'unknown'
                    }, status=500)

            else:
                coding_data = {
                    'CreatedON': data.get('CreatedOn'),
                    'CreatedBy': data.get('CreatedBy'),
                    'level': level,
                    'subtopic_id': subtopic_id,
                    'Name': data.get('Name'),
                    'QNty': data.get('QNty'),
                    'QnTe': data.get('QnTe'),
                    'Qn': data.get('Qn'),
                    'Query': data.get('Query'),
                    'Table': data.get('Table'),
                    'TestCases': data.get('TestCases'),
                    'ExpectedOutput': expected_output,
                    'Tags': data.get('Tags'),
                    'Template': data.get('Template'),
                    'Examples': data.get('Examples'),
                    'Ans': data.get('Ans'),
                    'FunctionCall': data.get('FunctionCall'), 
                    'Explanations': data.get('Explanations'),
                    'Hints': data.get('Hints'),
                    'LastUpdated': data.get('LastUpdated'),
                      
                }

                coding_folder = f"{subtopic_folder}Coding/"
                file_pattern = f"q{subtopic_id}c{level_char}m"
                next_coding_number = get_next_number(coding_folder, file_pattern)

                if next_coding_number > 99:
                    return JsonResponse({'error': 'Maximum number of questions (99) for this level has been reached.'}, status=400)

                coding_filename = f"{file_pattern}{next_coding_number:02d}.json"
                coding_blob_name = coding_folder + coding_filename

                blob_client = container_client.get_blob_client(coding_blob_name)
                if blob_client.exists():
                    return JsonResponse({'error': f'File {coding_filename} already exists.'}, status=400)

                json_data = json.dumps(coding_data, ensure_ascii=False)
                encoded_data = json_data.encode('utf-8')

                blob_client.upload_blob(
                    encoded_data,
                    overwrite=False,
                    content_settings=ContentSettings(
                        content_type='application/json',
                        charset='utf-8'
                    )
                )

                qn_id = os.path.splitext(coding_filename)[0]
                subtopic = sub_topics.objects.get(sub_topic_id=subtopic_id)
                question = questions(
                    question_id=qn_id,
                    sub_topic_id=subtopic,
                    question_type='coding',
                    level=level,
                    created_by=data.get('CreatedBy'),
                    last_updated_by=last_updated_by,
                    reviewed_by='',
                    tags=','.join(data.get('Tags', [])) if isinstance(data.get('Tags'), list) else data.get('Tags', '')
                )
                question.save()

                return JsonResponse({
                    'message': 'Question created successfully',
                    'blob_name': coding_blob_name
                })

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method or content type'}, status=400)

def execute_query_and_get_output(query):
    try:
        query = mysqlToSql(query)
        connection_string = (f'Driver={MSSQL_DRIVER};'
                             f'Server={MSSQL_SERVER_NAME};'
                             f'Database={MSSQL_DATABASE_NAME};'
                             f'UID={MSSQL_USERNAME};'
                             f'PWD={MSSQL_PWD};')
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute(query)

        if query.split(' ')[0].lower() == "select":
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            data = extract_table_rows(rows, columns)
            return data
        else:
            return []
    except pyodbc.Error as e:
        raise Exception(str(e))

@api_view(['POST'])
def execute_query(request):
    data = request.data
    query = data.get('query')
    if not query:
        return JsonResponse({"error": "Query is required"}, status=400)

    try:
        result = local(query)
        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def local(data):
    try:
            query = data
            query = mysqlToSql(query)
            connection_string = (f'Driver={MSSQL_DRIVER};'f'Server={MSSQL_SERVER_NAME};'f'Database={MSSQL_DATABASE_NAME};'f'UID={MSSQL_USERNAME};'f'PWD={MSSQL_PWD};')    
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute(query)
            result=""
            if query.split(' ')[0].lower() == "select":
                D=len(cursor.fetchall())
                if D>0:
                    t=True
                    cursor.execute(query)
                else:
                    t=False
                    result = "Query executed successfully.However, the result set is empty."
            elif (query.split(" ")[0].lower()=="insert") or (query.split(" ")[0].lower()=="delete") :
                table=query.split(' ')[2]
                cursor.execute("select * from "+table)
                t=True  
            elif query.split(" ")[0].lower()=="update":
                table=query.split(' ')[1]
                cursor.execute("select * from "+table)
                t=True
            elif query.split(' ')[0].lower() == "drop":
                table=query.split(' ')[2]
                result = "table ("+table+") droped successfully."
                t=False
            else   :  
                D=len(cursor.fetchall())
                if D>0:
                    t=True
                    cursor.execute(query)
                else:
                    t=False
                    result = "Query executed successfully.However, the result set is empty."
            if t:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                data = extract_table_rows(rows, columns)
                out=data
            else :
                out=[{"result":result}]
                # out='{"result":"'+result+'['+str(00)+']"}'
            conn.close()
            return out
    except pyodbc.Error as e:
            m=str(e).split(']')[-1]
            out=  [{"Error": m.replace("(SQLExecDirectW)')",'')}]#'{"error":"'+m[0:-2]+'"}'
            return out
   
def mysqlToSql(query):
 
    query = dateFormat(query)
 
    if str(query).lower().__contains__("character_length(") or str(query).lower().__contains__("length(" ) or str(query).lower().__contains__("char_length("):
        query = query.replace("CHARACTER_LENGTH(", "LEN(")
        query = query.replace("character_length(", "LEN(")
        query = query.replace("LENGTH(", "LEN(")
        query = query.replace("char_length(", "LEN(")
        query = query.replace("CHAR_LENGTH(", "LEN(")
        query = query.replace("length(", "LEN(")
        query = query.replace("Char_length(", "LEN(")
        query = query.replace("Character_length(", "LEN(")
        query = query.replace("Length()", "LEN(")
    if str(query).lower().__contains__("limit"):
        pattern = re.compile(r"(?i)limit\s*(\d+),\s*(\d+)")
        pattern2 = re.compile(r"(?i)limit\s*(\d+) offset\s*(\d+)")
        limit_pattern_without_offset = re.compile(r"(?i)limit\s*(\d+)")
       
        def replacer(match):
            offset = match.group(1)
            row_count = match.group(2)
            return f"OFFSET {offset} ROWS FETCH NEXT {row_count} ROWS ONLY"
        def replacer_without_offset(match):
            count = match.group(1)
            return f"TOP {count}"
        if (pattern.search(query.lower())):
            query = pattern.sub(replacer, query)
        elif (pattern2.search(query.lower())):
            query = pattern2.sub(replacer, query)
        elif(limit_pattern_without_offset.search(query.lower())):
            new_query = limit_pattern_without_offset.sub(replacer_without_offset, query)
            if  'select' in (new_query).lower():
                top =re.compile(r"(?i)TOP\s*(\d+)")
                ele =  top.search(new_query).group(0)
                new_query = new_query.replace(ele,'')
                query = new_query.replace('select', 'SELECT '+ele+' ') if 'select' in (new_query) else new_query.replace('SELECT', 'SELECT '+ele+' ')
                # query = 'SELECT ' + ele + ' ' + new_query.lower().split('select', 1)[1]
   
    if str(query).lower().__contains__("fetch first") and str(query).lower().__contains__("rows only"):
        pattern = re.compile(r"(?i)fetch first\s*(\d+)")
 
        def replacer(match):
            row_count = match.group(1)
            return f"OFFSET 0 ROWS FETCH NEXT {row_count} "
 
        if (pattern.search(query.lower())):
            query = pattern.sub(replacer, query)
        # nq = str(query).lower().split('fetch first', 1)[1]
        query
 
    if str(query).lower().__contains__("uuid()"):
        query = query.replace("uuid()", "NEWID()")
        query = query.replace("UUID()", "NEWID()")
 
    if str(query).lower().__contains__("now()"):
        query = query.replace("now()", "GETDATE()")
        query = query.replace("NOW()", "GETDATE()")
 
    if str(query).lower().__contains__("version()"):
        query = query.replace("version()", "'ERROR'")
        query = query.replace("VERSION()", "'ERROR'")
        query = query.replace("@@VERSION", "'ERROR'")
        query = query.replace("@@version()", "'ERROR'")
 
    if str(query).lower().__contains__("database()"):
        query = query.replace("database()", "'ERROR'")
        query = query.replace("DATABASE()", "'ERROR'")
        query = query.replace("DB_NAME()", "'ERROR'")
        query = query.replace("db_name()", "'ERROR'")
 
    if str(query).lower().__contains__("user()"):
        query = query.replace("user()", "'ERROR'")
        query = query.replace("USER()", "'ERROR'")
        query = query.replace("SUSER_NAME()", "'ERROR'")
        query = query.replace("suser_name()", "'ERROR'")
 
    if str(query).lower().__contains__("session_user()") or str(query).lower().__contains__("system_user()"):
        query = query.replace("session_user()", "'ERROR'")
        query = query.replace("SESSION_USER()", "'ERROR'")
        query = query.replace("system_user", "'ERROR'")
        query = query.replace("system_user()", "'ERROR'")
        query = query.replace("SYSTEM_USER", "'ERROR'")
        query = query.replace("SYSTEM_USER()", "'ERROR'")
 
    if str(query).lower().__contains__("current_user()"):
        query = query.replace("current_user()", "'ERROR'")
        query = query.replace("current_user", "'ERROR'")
        query = query.replace("CURRENT_USER()", "'ERROR'")
        query = query.replace("CURRENT_USER", "'ERROR'")
 
    if str(query).lower().__contains__("ceil("):
        query = query.replace("ceil(", "CEILING(")
        query = query.replace("CEIL(", "CEILING(")
 
    if str(query).lower().__contains__("date_format("):
        query = query.replace("date_format(", "FORMAT(")
        query = query.replace("DATE_FORMAT(", "FORMAT(")
       
    if str(query).lower().__contains__("date_add(") :
        add = r'(?i)date_add\(([^,]+),\s*interval\s*([^ ]+)\s*([^ )]+)\)'
        add_replacement = r'DATEADD(\3, \2, \1)'
        query = re.sub(add, add_replacement, query)
 
    if str(query).lower().__contains__("date_sub(") :
        sub = r'(?i)date_sub\(([^,]+),\s*interval\s*([^ ]+)\s*([^ )]+)\)'
        sub_replacement = r'DATEADD(\3, -\2, \1)'
        query = re.sub(sub, sub_replacement, query)
 
    if str(query).lower().__contains__("datediff(") :
        query = query.replace("datediff(", "DATEDIFF(day,")
        query = query.replace("DATEDIFF(", "DATEDIFF(day,")
 
    if str(query).lower().__contains__("curdate()") :
        query = query.replace("curdate()", "CAST(GETDATE() AS DATE)")
        query = query.replace("CURDATE()", "CAST(GETDATE() AS DATE)")
 
    if str(query).lower().__contains__("curtime()") :
        query = query.replace("curtime()", "CAST(GETDATE() AS TIME)")
        query = query.replace("CURTIME()", "CAST(GETDATE() AS TIME)")
 
    if str(query).lower().__contains__("if(") :
        query = query.replace("if(", "IIF(")
        query = query.replace("IF(", "IIF(")
 
    if str(query).lower().__contains__("group_concat(") :
        concat = r'(?i)GROUP_CONCAT\(([^,]+)\s*SEPARATOR\s*([^)]*)\)'
        concat_replacement = r'STRING_AGG(\1, \2)'
        query = re.sub(concat, concat_replacement, query)
 
    if str(query).lower().__contains__("mediumint") :
        query = query.replace("mediumint", "INT")
        query = query.replace("MEDIUMINT", "INT")
 
    if str(query).lower().__contains__("mediumtext") or str(query).lower().__contains__("longtext") :
        query = query.replace("mediumtext", "VARCHAR(MAX)")
        query = query.replace("MEDIUMTEXT", "VARCHAR(MAX)")
        query = query.replace("longtext", "VARCHAR(MAX)")
        query = query.replace("LONGTEXT", "VARCHAR(MAX)")
   
    if str(query).lower().__contains__("blob") :
        query = query.replace("blob", "IMAGE")
        query = query.replace("BLOB", "IMAGE")
 
    if str(query).lower().__contains__("timestamp") or str(query).lower().__contains__("year"):
        query = query.replace("timestamp", "DATETIME")
        query = query.replace("TIMESTAMP", "DATETIME")
        query = query.replace("year", "DATETIME")
        query = query.replace("YEAR", "DATETIME")
 
    if str(query).lower().__contains__("boolean") :
        query = query.replace("boolean", "BIT")
        query = query.replace("BOOLEAN", "BIT")
   
    if str(query).lower().__contains__("auto_increment") :
        query = query.replace("auto_increment", "IDENTITY(1,1)")
        query = query.replace("AUTO_INCREMENT", "IDENTITY(1,1)")
   
    if str(query).lower().__contains__("engine") :
        query = query.split('ENGINE')[0]
        query = query.split('engine')[0]
        # query = query +"COLLATE Latin1_General_CI_AS;"
    return query
 
 
   
def dateFormat(query):
    query = str(query).replace('%Y', 'yyyy')
    query = query.replace('%y', 'yy')
    query = query.replace('%m', 'MM')
    query = query.replace('%d', 'dd')
    query = query.replace('%H', 'HH')
    query = query.replace('%i', 'mi')
    query = query.replace('%s', 'ss')
    query = query.replace('%f', 'ms')
    query = query.replace('%a', 'ddd')
    query = query.replace('%b', 'MMM')
    query = query.replace('%W', 'dddd')
    query = query.replace('%M', 'MMMM')
    return query
   
 
 
def get_tables(tables):
    try:
                tabs = []
                connection_string = (f'Driver={MSSQL_DRIVER};'f'Server={MSSQL_SERVER_NAME};'f'Database={MSSQL_DATABASE_NAME};'f'UID={MSSQL_USERNAME};'f'PWD={MSSQL_PWD};')    
                conn = pyodbc.connect(connection_string)
                cursor = conn.cursor()
                tables = str(tables).split(',')
                for table in tables:
                    cursor.execute("SELECT * FROM " + table)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    data = extract_table_rows(rows, columns)
                   
                    tabs.append({"tab_name": table, "data": data})
                return tabs
    except Exception as e:  
        return "Error getting tables: " + str(e)
 
def extract_table_rows(rows, columns):
    try:
        data = []
        for row in rows:
            row_data = {}
            for i, value in enumerate(row):
                if isinstance(value, date) or isinstance(value, datetime) or isinstance(value, time):
                    row_data[columns[i]] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_data[columns[i]] = float(value)
                elif value is None:
                    row_data[columns[i]] = 'NULL'
                else:
                    row_data[columns[i]] = value
            data.append(row_data)
        return data
    except Exception as e:  
        return "Error extracting table rows: " + str(e)
 