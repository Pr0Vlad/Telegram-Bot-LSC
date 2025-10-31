from typing import Final
from telegram import Update
from telegram.ext import  Application, CommandHandler, MessageHandler, filters, ContextTypes
import PlanningCenterScraper

TOKEN: Final = ''
BOT_USERNAME: Final = ''


#commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to the lsc service scheduling video team bot')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('help page')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('custom command')

#Responses

def handle_response(text: str) -> str:
    schedule_string = ''
    service_string_1 = ''
    service_string_2 = ''
    sunday = "SUNDAY SERVICE"
    if 'schedule' in text:
        #asking for specific upcoming service
        if 'sunday' in text.lower() or 'communion' in text.lower():
            if 'communion' in text.lower():
                sunday = "Communion"
            print(sunday)
            if '1' in text.lower():
                service_string_1 = f'{sunday} #1'
                schedule_string = format_schedule(PlanningCenterScraper.GetSchedule(sunday, '1'),
                [service_string_1, service_string_2])
            elif '2' in text.lower():
                service_string_1 = f'{sunday} #2'
                schedule_string = format_schedule(PlanningCenterScraper.GetSchedule(sunday, '2'),
                [service_string_1, service_string_2])
            elif '*' in text.lower():
                service_string_1 = f'{sunday} #1'
                service_string_2 = f'{sunday} #2'
                schedule_string = format_schedule(PlanningCenterScraper.GetSchedule(sunday, '*'),
                [service_string_1, service_string_2])
        elif 'wednesday' in text.lower():
            print("in wednesday")
            service_string_1 = 'WEDNESDAY SCHEDULE'
            schedule_string = format_schedule(PlanningCenterScraper.GetSchedule('WEDNESDAY SERVICE'),
            [service_string_1, service_string_2])
        #will look at date and grab the schedule for the most upcoming day with service
        elif 'next schedule' in text.lower():
            upcoming_schedule_list = PlanningCenterScraper.GetNextSchedule()
            schedule_string = format_schedule(upcoming_schedule_list)
        if schedule_string != '':
            return f'{schedule_string}'
        else:
            return "COULD NOT FIND SCHEDULE SORRY"

    else:
        return "I DO NOT UNDERSTAND"

def format_schedule(schedule_list, service_names = None):
    schedule_string = ''
    index = -1
    for schedule in schedule_list:
        index += 1
        if schedule != None:
            if schedule == "ERROR FINDING A SERVICE PLAN":
                schedule_string += "could not find service"
            else:
                if index > 0:
                    service_title = "\n" + "\n"
                    if service_names != None:
                        service_title = "\n" + str(service_names[index]) + "\n"

                else:
                    service_title = schedule['date']  + "\n"  + "\n"
                    if service_names != None:
                        service_title = schedule['date']  + "\n" +  str(service_names[index]) + "\n"

                schedule_string += service_title  + schedule['time'] + "\n\n"
                for position, person in schedule.items():
                    if position not in ['date', 'time']:
                        schedule_string += f'{position} - {person} \n'

    return schedule_string

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
    #PlanningCenterScraper.GetSchedule('SUNDAY SERVICE', '2')
    #PlanningCenterScraper.GetSchedule('SUNDAY SERVICE', '3')
    #PlanningCenterScraper.GetSchedule('SUNDAY SERVICE', '*')
    #PlanningCenterScraper.GetSchedule('wednesday SCHEDULE')
    #PlanningCenterScraper.GetSchedule('COMMUNION SERVICE', '*')
    #PlanningCenterScraper.GetNextSchedule()
    app = Application.builder().token(TOKEN).build()

    #commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    #messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    #errors
    app.add_error_handler(error)
    app.run_polling(poll_interval = 5)
