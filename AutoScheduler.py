import json
import urllib.error
import urllib.request
from datetime import datetime

import PlanningCenterScraper

AUTOSCHEDULE_URL_TEMPLATE = "https://services.planningcenteronline.com/~api/services/v2/service_types/619990/plans/{plan_id}/autoschedule"
PLAN_URL_TEMPLATE = "https://api.planningcenteronline.com/services/v2/service_types/619990/plans/{plan_id}"
TEST_AUTOSCHEDULE_PLAN_ID = "87970649"


#--------------------------------------------------------------------------------------------------
def AutoScheduleNearestSunday():
    plans = GetNearestSundayPlans()

    if len(plans) == 0:
        return {'success': False, 'message': 'Could not find an upcoming Sunday service.'}

    return AutoSchedulePlans(plans)


#--------------------------------------------------------------------------------------------------
def AutoScheduleTestPlan():
    plan = GetPlan(TEST_AUTOSCHEDULE_PLAN_ID)

    if plan is None:
        return {'success': False, 'message': 'Could not find the test autoschedule plan.'}

    return AutoSchedulePlan(plan)


#--------------------------------------------------------------------------------------------------
def AutoSchedulePlan(plan):
    try:
        response_data = StartAutoSchedule(plan['id'])
    except urllib.error.HTTPError as error:
        return {'success': False, 'message': f"Planning Center autoschedule failed with status {error.code}."}
    except urllib.error.URLError as error:
        return {'success': False, 'message': f"Could not reach Planning Center: {error.reason}"}

    scheduled_people = response_data.get('data', [])

    return {'success': True, 'plan': plan, 'scheduled_count': len(scheduled_people), 'scheduled_people': GetScheduledPeople(scheduled_people)}


#--------------------------------------------------------------------------------------------------
def AutoSchedulePlans(plans):
    results = []

    for plan in plans:
        results.append(AutoSchedulePlan(plan))

    return {'success': all(result['success'] for result in results), 'plans': plans, 'results': results}


#--------------------------------------------------------------------------------------------------
def GetPlan(plan_id):
    response_data = PlanningCenterScraper.GetApiJson(
        PLAN_URL_TEMPLATE.format(plan_id=plan_id)
    )
    plan = response_data.get('data')

    if plan is None:
        return None

    return FormatPlan(plan)


#--------------------------------------------------------------------------------------------------
def GetNearestSundayPlan():
    plans = GetNearestSundayPlans()

    if len(plans) == 0:
        return None

    return plans[0]


#--------------------------------------------------------------------------------------------------
def GetNearestSundayPlans():
    response_data = PlanningCenterScraper.GetApiJson(PlanningCenterScraper.url_future_plans)
    sunday_plans = []

    for plan in response_data['data']:
        formatted_plan = FormatPlan(plan)
        sort_date = formatted_plan['sort_date']

        if sort_date is None:
            continue

        plan_date = datetime.fromisoformat(sort_date.replace('Z', '+00:00'))
        if plan_date.weekday() != 6:
            continue

        sunday_plans.append(formatted_plan)

    if len(sunday_plans) == 0:
        return []

    nearest_sunday_date = sunday_plans[0]['short_dates']

    return [plan for plan in sunday_plans if plan['short_dates'] == nearest_sunday_date]


#--------------------------------------------------------------------------------------------------
def FormatPlan(plan):
    attributes = plan['attributes']

    return {'id': plan['id'], 'series_title': attributes['series_title'], 'short_dates': attributes['short_dates'], 'time': PlanningCenterScraper.ExtractTimeFromString(attributes['sort_date']), 'sort_date': attributes['sort_date'], 'planning_center_url': attributes['planning_center_url']}


#--------------------------------------------------------------------------------------------------
def StartAutoSchedule(plan_id):
    payload = {
        'data': {
            'type': 'Autoschedule',
            'attributes': {},
            'relationships': {
                'team': {
                    'data': {
                        'id': int(PlanningCenterScraper.video_team_id),
                        'type': 'Team'
                    }
                }
            }
        }
    }

    request = urllib.request.Request(
        AUTOSCHEDULE_URL_TEMPLATE.format(plan_id=plan_id),
        data=json.dumps(payload).encode('utf-8'),
        method='POST'
    )
    request.add_header(
        'Authorization',
        'Basic %s' %PlanningCenterScraper.encoded_credentials.decode("ascii")
    )
    request.add_header('Content-Type', 'application/json')
    request.add_header('Accept', 'application/vnd.api+json')

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


#--------------------------------------------------------------------------------------------------
def GetScheduledPeople(scheduled_people):
    people = []

    for scheduled_person in scheduled_people:
        attributes = scheduled_person.get('attributes', {})
        name = attributes.get('name')
        if name is not None:
            people.append({'name': name, 'position': GetScheduledPosition(scheduled_person)})

    return people


#--------------------------------------------------------------------------------------------------
def GetScheduledPosition(scheduled_person):
    relationships = scheduled_person.get('relationships', {})
    plan_person = relationships.get('plan_person', {}).get('data', {})

    if plan_person.get('type') != 'PlanPerson':
        return ''

    plan_person_id = plan_person.get('id')
    plan_id = relationships.get('plan', {}).get('data', {}).get('id')

    if plan_id is None or plan_person_id is None:
        return ''

    plan_person_data = PlanningCenterScraper.GetApiJson(
        f"{PlanningCenterScraper.team_members}{plan_id}/team_members/{plan_person_id}"
    )

    return plan_person_data['data']['attributes'].get('team_position_name', '')
