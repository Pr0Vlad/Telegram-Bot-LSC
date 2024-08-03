import urllib.request
import socket
import time
import json
import base64
import re
from typing import Final

APPID: Final = f'bfc324a997dcfacd43549bb68609ce4516b0e63f0bd9f0c815199b556aa7ed65'
SECRET: Final = f'1776c42102df0950a89fba7fb55d06fb539d4ea8c431ca7920bc8c3476c686c5'
url_future_plans = f'https://api.planningcenteronline.com/services/v2/service_types/619990/plans?order=sort_date&filter=future'
team_members = f'https://api.planningcenteronline.com/services/v2/service_types/619990/plans/'
credentials = ('%s:%s' % (APPID, SECRET))
encoded_credentials = base64.b64encode(credentials.encode('ascii'))

def GetSchedule(schedule, time = ''):
    schedule_time_1 = None
    schedule_time_2 = None
    final_schedule_list = None
    if 'sunday' in schedule.lower():
        if time != "":
            if time != '*':
                schedule_time_1 = f'{schedule} #{time}'
            else:
                schedule_time_1 = f'{schedule} #{2}'
                schedule_time_2 = f'{schedule} #{3}'
        else:
            schedule_time_1 = f'{schedule}'
    elif 'wednesday' in schedule.lower():
        schedule_time_1 = 'WEDNESDAY'
    elif 'communion' in schedule.lower():
        if time != "":
            if time != '*':
                schedule_time_1 = f'{schedule} #{time}'
            else:
                schedule_time_1 = f'COMMUNION SERVICE #{2}'
                schedule_time_2 = f'COMMUNION {3} Russian'
        else:
            schedule_time_1 = f'{schedule}'

    service_plans_list = extract_plans_for_service([schedule_time_1, schedule_time_2])
    if len(service_plans_list)> 0:
        final_schedule_list = []
        for service_plan_list in service_plans_list:
            if service_plans_list != None:
                final_schedule_list.append(getTeam(service_plan_list))
        print(repr(final_schedule_list))
        return final_schedule_list
    else:
        return

def extract_plans_for_service(schedule_time_list = []) :
    plan_id = ''
    service_info = {'id':'', 'date':'', 'time':''}
    services_list = []
    req = urllib.request.Request(url_future_plans)
    req.add_header('Authorization', 'Basic %s' %encoded_credentials.decode("ascii"))
    print(schedule_time_list)
    if len(schedule_time_list) > 0:
        for schedule_time in schedule_time_list:
            if schedule_time != None:
                print(f'GETTING SCHEDULE FOR: {schedule_time}')
                with urllib.request.urlopen(req) as response:
                    ResponseData = json.loads(response.read())['data']
                    for service in ResponseData:
                        plan = service['attributes']
                        if plan['series_title'] == schedule_time:
                            new_plan =  service_info.copy()
                            new_plan['id'] = str(service['id'])
                            new_plan['date'] = plan['short_dates']
                            new_plan['time'] = extract_time_from_string(plan['sort_date'])
                            services_list.append((new_plan))
                            break
            else:
                services_list.append(None)
        return services_list
    return

def extract_time_from_string(input_string):
    pattern = r'T(\d{2}:\d{2}):\d{2}Z'
    match = re.search(pattern, input_string)
    if match:
        time_without_seconds = match.group(1)
        hour = int(time_without_seconds.split(':')[0])
        am_pm = 'AM' if hour < 12 else 'PM'
        hour = hour if hour == 12 else hour % 12
        formatted_time = f"{hour:02d}:{time_without_seconds.split(':')[1]} {am_pm}"
        return formatted_time
    else:
        return None

def getTeam(service_plan):
    if service_plan != None:
        plan_id = service_plan['id']
        camera_dict = {'date':service_plan['date'], 'time':service_plan['time'], 'Cam 1':'', 'Cam 2':'','Cam 3':'', 'Cam 4':'', 'Cam 5':'', 'Mixer':'', 'Live':''}
        req = urllib.request.Request(f'{team_members}{plan_id}/team_members')
        req.add_header('Authorization', 'Basic %s' %encoded_credentials.decode("ascii"))
        with urllib.request.urlopen(req) as response:
            ResponseData = json.loads(response.read())['data']
            for persons in ResponseData:
                person = persons['attributes']
                if person['status'] == 'C':
                    if person['team_position_name'] in camera_dict.keys():
                        camera_dict[person['team_position_name']] = person['name']
        return camera_dict
    else:
        return



