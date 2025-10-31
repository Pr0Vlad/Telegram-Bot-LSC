import urllib.request
import json
import base64
import re
from typing import Final

APPID: Final = f''
SECRET: Final = f''
url_future_plans = f'https://api.planningcenteronline.com/services/v2/service_types/619990/plans?order=sort_date&filter=future'
team_members = f'https://api.planningcenteronline.com/services/v2/service_types/619990/plans/'
team_positions = f'https://api.planningcenteronline.com/services/v2/service_types/619990/team_positions'
video_team_id = "5556557"
credentials = ('%s:%s' % (APPID, SECRET))
encoded_credentials = base64.b64encode(credentials.encode('ascii'))

#--------------------------------------------------------------------------------------------------
def GetSchedule(schedule, time = ''):
    schedule_time_1 = None
    schedule_time_2 = None
    final_schedule_list = None
    if 'sunday' in schedule.lower():
        if time != "":
            if time != '*':
                schedule_time_1 = f'{schedule} #{time}'
            else:
                schedule_time_1 = f'{schedule} #{1}'
                schedule_time_2 = f'{schedule} #{2}'
        else:
            schedule_time_1 = f'{schedule}'
    elif 'wednesday' in schedule.lower():
        schedule_time_1 = 'Wednesday'
    elif 'communion' in schedule.lower():
        if time != "":
            if time != '*':
                schedule_time_1 = f'{schedule} #{time}'
            else:
                schedule_time_1 = f'Communion #{1}'
                schedule_time_2 = f'Communion #{2}'
        else:
            schedule_time_1 = f'{schedule}'

    service_plans_list = ExtractPlansForService([schedule_time_1, schedule_time_2])
    if len(service_plans_list)> 0:
        final_schedule_list = []
        for service_plan_list in service_plans_list:
            if service_plans_list != None:
                final_schedule_list.append(GetTeam(service_plan_list))
        print(repr(final_schedule_list))
        return final_schedule_list
    else:
        return

#--------------------------------------------------------------------------------------------------
def ExtractPlansForService(schedule_time_list = []) :
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
                    response_data = json.loads(response.read())['data']
                    for service in response_data:
                        plan = service['attributes']
                        if plan['series_title'] == schedule_time:
                            new_plan =  service_info.copy()
                            new_plan['id'] = str(service['id'])
                            new_plan['date'] = plan['short_dates']
                            new_plan['time'] = ExtractTimeFromString(plan['sort_date'])
                            services_list.append((new_plan))
                            break
            else:
                services_list.append(None)
        return services_list
    return

#--------------------------------------------------------------------------------------------------
def ExtractTimeFromString(input_string):
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

#--------------------------------------------------------------------------------------------------
def GetTeam(service_plan):
    if service_plan != None:
        plan_id = service_plan['id']
        position_dict = {'date':service_plan['date'], 'time':service_plan['time']}
        possible_positions = GetAllPossibleVideoPositions()
        position_dict.update({pos: "" for pos in possible_positions})
        req = urllib.request.Request(f'{team_members}{plan_id}/team_members')
        req.add_header('Authorization', 'Basic %s' %encoded_credentials.decode("ascii"))
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read())['data']
            for persons in response_data:
                person = persons['attributes']
                if person['status'] == 'C':
                    if person['team_position_name'] in possible_positions:
                        position_dict[person['team_position_name']] = person['name']
        return position_dict
    else:
        return

#--------------------------------------------------------------------------------------------------
def GetAllPossibleVideoPositions():
    possible_positions = []
    req = urllib.request.Request(f'{team_positions}')
    req.add_header('Authorization', 'Basic %s' %encoded_credentials.decode("ascii"))
    with urllib.request.urlopen(req) as response:
        response_data = json.loads(response.read())['data']
        for pos in response_data:
            team_id = pos.get("relationships", {}).get("team", {}).get("data", {}).get("id")
            if team_id == video_team_id:
                if "director" not in pos['attributes']['name'].lower():
                    possible_positions.append(pos['attributes']['name'])
    return possible_positions

#--------------------------------------------------------------------------------------------------
def GetNextDayServices() :
    plan_date = ""
    service_info = {'id':'', 'date':'', 'time':''}
    services_list = []
    req = urllib.request.Request(url_future_plans)
    req.add_header('Authorization', 'Basic %s' %encoded_credentials.decode("ascii"))
    with urllib.request.urlopen(req) as response:
        response_data = json.loads(response.read())['data']
        for service in response_data:
            plan = service['attributes']
            new_plan =  service_info.copy()
            new_plan['id'] = str(service['id'])
            new_plan['date'] = plan['short_dates']
            new_plan['time'] = ExtractTimeFromString(plan['sort_date'])
            if len(services_list) == 0:
                plan_date = new_plan['date']
            #only adding the services from the same date as the next date of the first service, it can be 1 or 3
            #but once the dates dont match we now got all we need
            if plan_date == new_plan['date']:
                services_list.append((new_plan))
            else:
                break
    return services_list

#--------------------------------------------------------------------------------------------------
def GetNextSchedule():
    service_plans_list = GetNextDayServices()
    if len(service_plans_list)> 0:
        final_schedule_list = []
        for service_plan_list in service_plans_list:
            if service_plans_list != None:
                final_schedule_list.append(GetTeam(service_plan_list))
        return final_schedule_list
    else:
        return

