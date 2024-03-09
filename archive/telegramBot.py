#!/usr/bin/python3

import sys
import time
import logging
import RPi.GPIO as GPIO
import dht11
import threading

from lib.mq import MQ

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# TODO: Move to seperate file
STANDARD_ERROR_MESSAGE = "Seems like something expected has occured...\nThis incident has been recorded"
DHT11_ERROR_MESSAGE = "Error: DHT11 faliure"
LOG_PATH = "logs/log.txt"

# TODO: Move to secure file 
TELEBOT_API_KEY = '6433815808:AAE8hYNT1X6Gu8CFQSelrHnXeuPb4y1yoko'

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

COMMAND, GENDER = range(2)

def loggerInit() -> logging.Logger:
    """Create logger instance"""
    # Enable logging
    logging.basicConfig(
        filename=LOG_PATH,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )
    # set higher logging level for httpx to avoid all GET and POST requests being logged
    logging.getLogger("httpx").setLevel(logging.WARNING)
    loggerInstance = logging.getLogger(__name__)
    return loggerInstance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user for their command."""
    user = update.message.from_user
    reply_keyboard = [
                        ['Temperature'],
                        ['Humidity'],
                        ['Air Quality']
                        ]
    
    msg = ("Hi " + user.first_name + "! My name is Sensor Bot, nice to meet you!\n"
        + "For your reference, your user id is: " + msg.chat.id + "\n"
        + "Send /cancel at any time to stop talking to me.\n"
        + "Please select a command below.")


     
    placeholder_msg = "Command?"
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, input_field_placeholder=placeholder_msg
        ),
    )
    return COMMAND

async def command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected command and ask for next command."""
    user = update.message.from_user
    #loggerInstance.info("Command of %s: %s", user.first_name, update.message.text)
    print(f"Command of {user.first_name}: {update.message.text}")
    if (update.message.text == "Temperature"):
        temperatureResult = dht11Instance.read()
        
        if temperatureResult.is_valid():
            await update.message.reply_text(
                "Temperature: %-3.1f C" % temperatureResult.temperature,
            )
        else:
            await update.message.reply_text(
                "Error: DHT11_ERROR_MESSAGE %d\n%s" % (temperatureResult.error_code, STANDARD_ERROR_MESSAGE),
            )
    elif (update.message.text == "Humidity"):
        humidityResult = dht11Instance.read()
        
        if humidityResult.is_valid():
            await update.message.reply_text(
                "The current humidity is: %-3.1f %%" % humidityResult.humidity,
            )
        else:
            await update.message.reply_text(
                "Error: DHT11_ERROR_MESSAGE %d\n%s" % (humidityResult.error_code, STANDARD_ERROR_MESSAGE),
            )
    elif (update.message.text == "Air Quality"):
        await update.message.reply_text("LPG: %g ppm, CO: %g ppm, Smoke: %g ppm" % (perc["GAS_LPG"], perc["CO"], perc["SMOKE"]))
    else:
        await update.message.reply_text(
            STANDARD_ERROR_MESSAGE
        )
    return COMMAND

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    #loggerInstance.info("User %s canceled the conversation.", user.first_name)
    print(f"User {user.first_name} canceled the conversation.", )
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def tempPrinter():
    count = 0;
    while (1):
        count += 1
        print(count)
        time.sleep(1)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEBOT_API_KEY).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COMMAND: [MessageHandler(filters.Regex("^(Temperature|Humidity|Air Quality)$"), command)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    print("Intialization complete")

if __name__ == "__main__":
    # Create logger instance
    #loggerInstance = loggerInit()
    
    # DHT11 Temperature and Humidity Sensor Initialization
    dht11Instance = dht11.DHT11(pin=17)
    
    # MQ135 Gas Sensor Calibration + Initilization
    # TODO, record calibrated constants
    mq = MQ();
    perc = mq.MQPercentage()
    """
    main_thread = threading.Thread(target=main)
    temp_thread = threading.Thread(target=tempPrinter)

    main_thread.start()
    temp_thread.start()
    """
    main()

"""
Reference Material(s)
Telegram Bot                        https://docs.python-telegram-bot.org/en/v20.5/examples.html
DHT11 example                       https://github.com/szazo/DHT11_Python
MQ135 gas sensor                    https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/
"""
