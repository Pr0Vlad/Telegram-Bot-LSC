from datetime import time
import os
from typing import Final
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import AutoScheduler
import PlanningCenterScraper

TOKEN: Final = os.environ.get('TELEGRAM_BOT_TOKEN', '')
BOT_USERNAME: Final = os.environ.get('TELEGRAM_BOT_USERNAME', '')
TEST_GROUP_CHAT_ID: Final = -1002056776351
REAL_GROUP_CHAT_ID: Final = -1003399538168
BIRTHDAY_CHAT_ID: Final = REAL_GROUP_CHAT_ID
BIRTHDAY_TIME: Final = time(hour=9, minute=0, tzinfo=ZoneInfo("America/New_York"))


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to the lsc service scheduling video team bot')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('help page')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('custom command')


async def birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_birthday_message(send_empty_message=True))


async def auto_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_auto_schedule_message())


async def test_auto_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_test_auto_schedule_message())


async def daily_birthday_check(context: ContextTypes.DEFAULT_TYPE):
    message = get_birthday_message()

    if message == '':
        return

    await context.bot.send_message(chat_id=BIRTHDAY_CHAT_ID, text=message)


# Responses
def handle_response(text: str) -> str:
    lower_text = text.lower().strip()

    if lower_text == 'auto schedule':
        return get_auto_schedule_message()

    if lower_text == 'test auto schedule':
        return get_test_auto_schedule_message()

    if 'schedule' not in text:
        return "I DO NOT UNDERSTAND"

    schedule_string = get_schedule_response(text)

    if schedule_string != '':
        return f'{schedule_string}'

    return "COULD NOT FIND SCHEDULE SORRY"


def get_schedule_response(text: str) -> str:
    lower_text = text.lower()

    if 'sunday' in lower_text or 'communion' in lower_text:
        service_name = get_service_name(lower_text)
        print(service_name)
        return get_service_schedule_response(service_name, lower_text)

    if 'wednesday' in lower_text:
        print("in wednesday")
        return get_wednesday_schedule_response()

    # Will look at date and grab the schedule for the most upcoming day with service.
    if 'next schedule' in lower_text:
        upcoming_schedule_list = PlanningCenterScraper.GetNextSchedule()
        return format_schedule(upcoming_schedule_list)

    return ''


def get_service_name(text: str) -> str:
    if 'communion' in text:
        return "Communion"

    return "SUNDAY SERVICE"


def get_service_schedule_response(service_name: str, text: str) -> str:
    service_number = get_requested_service_number(text)

    if service_number == '':
        return ''

    service_names = get_service_titles(service_name, service_number)
    schedule_list = PlanningCenterScraper.GetSchedule(service_name, service_number)

    return format_schedule(schedule_list, service_names)


def get_requested_service_number(text: str) -> str:
    if '1' in text:
        return '1'

    if '2' in text:
        return '2'

    if '*' in text:
        return '*'

    return ''


def get_service_titles(service_name: str, service_number: str) -> list[str]:
    if service_number == '*':
        return [f'{service_name} #1', f'{service_name} #2']

    return [f'{service_name} #{service_number}', '']


def get_wednesday_schedule_response() -> str:
    service_names = ['WEDNESDAY SCHEDULE', '']
    schedule_list = PlanningCenterScraper.GetSchedule('WEDNESDAY SERVICE')

    return format_schedule(schedule_list, service_names)


def format_schedule(schedule_list, service_names=None):
    schedule_string = ''

    if schedule_list is None:
        return schedule_string

    for index, schedule in enumerate(schedule_list):
        if schedule is None:
            continue

        if schedule == "ERROR FINDING A SERVICE PLAN":
            schedule_string += "could not find service"
            continue

        service_title = get_schedule_title(schedule, index, service_names)
        schedule_string += service_title + schedule['time'] + "\n\n"

        for position, person in schedule.items():
            if position not in ['date', 'time']:
                schedule_string += f'{position} - {person} \n'

    return schedule_string


def get_schedule_title(schedule, index, service_names=None) -> str:
    if index > 0:
        if service_names is not None:
            return "\n" + str(service_names[index]) + "\n"

        return "\n\n"

    if service_names is not None:
        return schedule['date'] + "\n" + str(service_names[index]) + "\n"

    return schedule['date'] + "\n\n"


def get_birthday_message(send_empty_message=False) -> str:
    birthdays = PlanningCenterScraper.GetTodaysBirthdays()

    if len(birthdays) == 0:
        if send_empty_message:
            return "No video team birthdays today."

        return ''

    if len(birthdays) == 1:
        return f"Happy Birthday {birthdays[0]}!"

    birthday_list = "\n".join(f"- {name}" for name in birthdays)
    return f"Happy Birthday to:\n{birthday_list}"


def get_auto_schedule_message() -> str:
    result = AutoScheduler.AutoScheduleNearestSunday()
    return format_auto_schedule_message(result)


def get_test_auto_schedule_message() -> str:
    result = AutoScheduler.AutoScheduleTestPlan()
    return format_auto_schedule_message(result, is_test=True)


def format_auto_schedule_message(result, is_test=False) -> str:
    if not result['success']:
        return result['message']

    if 'results' in result:
        return format_multi_auto_schedule_message(result)

    plan = result['plan']
    prefix = 'Test auto schedule started' if is_test else 'Auto schedule started'
    message = (
        f"{prefix} for {plan['series_title']} "
        f"on {plan['short_dates']}.\n"
        f"Planning Center returned {result['scheduled_count']} assignments."
    )

    if result['scheduled_count'] == 0:
        return message

    scheduled_people = "\n".join(
        format_scheduled_person(person)
        for person in result['scheduled_people']
    )
    return f"{message}\n{scheduled_people}"


def format_multi_auto_schedule_message(result) -> str:
    plans = result['plans']
    service_summaries = []
    total_assignments = 0

    for plan_result in result['results']:
        if not plan_result['success']:
            service_summaries.append(plan_result['message'])
            continue

        plan = plan_result['plan']
        total_assignments += plan_result['scheduled_count']
        service_summary = (
            f"{plan['series_title']} at {plan['time']}: "
            f"{plan_result['scheduled_count']} assignments"
        )

        if plan_result['scheduled_count'] > 0:
            scheduled_people = "\n".join(
                format_scheduled_person(person)
                for person in plan_result['scheduled_people']
            )
            service_summary += f"\n{scheduled_people}"

        service_summaries.append(service_summary)

    message = (
        f"Auto schedule started for {len(plans)} services on "
        f"{plans[0]['short_dates']}.\n"
        f"Planning Center returned {total_assignments} total assignments."
    )

    return message + "\n\n" + "\n\n".join(service_summaries)


def format_scheduled_person(person) -> str:
    if person['position'] == '':
        return f"- {person['name']}"

    return f"- {person['name']}: {person['position']}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'USER {update.message.chat.id} in {message_type}: "{text}"')
    if "group" in message_type:
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    print('BOT:', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    print('STARTING BOT...')
    app = Application.builder().token(TOKEN).build()

    #commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('birthdays', birthday_command))
    app.add_handler(CommandHandler('autoschedule', auto_schedule_command))
    app.add_handler(CommandHandler('testautoschedule', test_auto_schedule_command))

    #messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #errors
    app.add_error_handler(error)

    if app.job_queue != None:
        app.job_queue.run_daily(daily_birthday_check, time=BIRTHDAY_TIME)
    else:
        print('Birthday daily check not scheduled. Install python-telegram-bot[job-queue].')

    app.run_polling(poll_interval=5)
