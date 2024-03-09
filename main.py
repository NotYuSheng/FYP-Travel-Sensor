#!/usr/bin/python3

import os
from dotenv import load_dotenv
import sys
import time
import logging
import RPi.GPIO as GPIO
import dht11
from datetime import datetime, timedelta
import pytz
from decouple import config
import time
from mq2 import *
from mq135 import *

from lib.mq import MQ
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler, Updater

DHT11_PIN = 11;
MQ2_MCP3008_PIN = 0;
MQ135_MCP3008_PIN = 1;

TEMPERATURE_COOLDOWN_PERIOD = 300 # 5 minute
HUMIDITY_COOLDOWN_PERIOD = 300 # 5 minute
AIRQUALITY_COOLDOWN_PERIOD = 300 # 5 minutes
# TODO Trigger alert only when category changes with short 1min cooldown

automatedAlertFlag = 1 # When set(1), automated alerts will trigger per period

last_temperature_alert_time = datetime.now() - timedelta(seconds=TEMPERATURE_COOLDOWN_PERIOD)
last_humidity_alert_time = datetime.now() - timedelta(seconds=HUMIDITY_COOLDOWN_PERIOD)
last_airquality_alert_time = datetime.now() - timedelta(seconds=AIRQUALITY_COOLDOWN_PERIOD)

current_temperature_category = ""
current_humidity_category = ""
current_airquality_category = ""

temperatureInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("More details", callback_data="Temperature-more-details")],
    #[InlineKeyboardButton("Button 2", callback_data="button2_data")],
])

humidityInlineKeyboard = InlineKeyboardMarkup([
    #[InlineKeyboardButton("More details", callback_data="Humidity-more-details")],
    [InlineKeyboardButton("More details", url="https://www.nea.gov.sg/media/news/news/index/new-heat-stress-advisory-launched-to-guide-public-on-minimising-risk-of-heat-related-illnesses")],
    #[InlineKeyboardButton("Button 2", callback_data="button2_data")],
])

airqualityInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("For a more accurate reading", url="https://www.iqair.com/sg/singapore")],
    #[InlineKeyboardButton("Button 2", callback_data="button2_data")],
])

# Load environment variables from .env file
load_dotenv()

# Access environment variables
TELEBOT_API_KEY = os.environ['TELEBOT_API_KEY']

# Static variables
STANDARD_ERROR_MESSAGE = "Seems like something expected has occured...\nThis incident has been recorded"
DHT11_ERROR_MESSAGE = "Error: DHT11 faliure"
LOG_PATH = "logs/log.txt" # Log file location
sgt_timezone = pytz.timezone('Asia/Singapore')
REPEATING_INTERVAL = 1 * 60 * 15 # When sending out a repeated message, have a 15 mins interval
COMMAND = 0

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def getTemperatureAdvMsg (temperature: float) -> str:
    temperature = round(temperature, 1)
    if temperature < 30:
        advisoryMessage = (
            "Temperature: {:.1f}°C \n"
            "Category: ⬜ White \n"
            "Enjoy the cool temperatures!".format(temperature)
        )
        
    elif temperature >= 30 and temperature < 31:
        advisoryMessage = (
            "Temperature: {:.1f}°C \n"
            "Category: 🟩 Green \n"
            "The weaher is warming up, enjoy your activities with moderate precautions!".format(temperature)
        )
        
    elif temperature >= 31 and temperature < 32:
        advisoryMessage = (
            "Temperature: {:.1f}°C \n"
            "Category: 🟨 Yellow \n"
            "Caution! The heat is on the rise, stay hydrated and limit prolong exposure to the sun.".format(temperature)
        )
        
    elif temperature >= 32 and temperature < 33:
        advisoryMessage = (
            "Temperature: {:.1f}°C \n"
            "Category: 🟥 Red \n"
            "High heat alert! Take extra precautions to stay cool and hydrated.".format(temperature)
        )
        
    elif temperature >= 33:
        advisoryMessage = (
            "Temperature: {:.1f}°C \n"
            "Category: ⬛ Black \n"
            "Extreme heat warning! Take immediate action to stay cool and safe!".format(temperature)
        )
    return advisoryMessage
    
def getHumidityAdvMsg (humidity: float) -> str:
    if humidity < 20:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: Dry \n"
            "Extremely low humidity! Be mindful of potential dehydration and increased risk of static electricity".format(humidity)
        )
        
    elif humidity >= 20 and humidity < 40:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: Comfortable \n"
            "Enjoy the comfortable humidity levels!".format(humidity)
        )            
        
    elif humidity >= 40 and humidity < 60:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: Moderate \n"
            "Moderate Humidity levels. Stay hydrated and comfortable".format(humidity)
        )
    
    elif humidity >= 60 and humidity < 80:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: Humid \n"
            "Humidity on the rise! Be cautious of potential discomfort due to higher moisture levels".format(humidity)
        )
    
    elif humidity >= 80:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: High \n"
            "High humidity alert! Take precautions to stay cool and comfortable".format(humidity)
        )
    return advisoryMessage

"""
def getAirQualityAdvMsg(airQuality: float) -> str:
    
    airQuality = round(airQuality)
    if airQuality <= 50:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Good \n"
            "tempMessage".format(airQuality)
        )
        
    elif airQuality > 50 and airQuality <= 100:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Moderate \n"
            "tempMessage".format(airQuality)
        )
    
    elif airQuality > 100 and airQuality <= 150:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Unhealth for sensitive groups \n"
            "tempMessage".format(airQuality)
        )
    
    elif airQuality > 150 and airQuality <= 200:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Unhealthy \n"
            "tempMessage".format(airQuality)
        )
    
    elif airQuality > 200 and airQuality <= 300:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Very unhealthy \n"
            "tempMessage".format(airQuality)
        )
    
    elif airQuality > 300:
        advisoryMessage = (
            "Air Quality: {:}ppm \n"
            "Category: Hazardous \n"
            "tempMessage".format(airQuality)
        )
    return advisoryMessage

"""
"""
def inlineButtonHandler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    # Handle the button click based on the callback data
    if data == "Temperature-more-details":
        # Handle Button 1 click
        pass
    elif data == "Humidity-more-details":
        # Handle Button 2 click
        pass
"""

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message when sensor value exceed threshold."""

    global automatedAlertFlag, last_temperature_alert_time, last_humidity_alert_time, last_airquality_alert_time
    
    # End process if alert disabled
    if (not automatedAlertFlag):
        return
    
    job = context.job
    dht11Result = dht11Instance.read()
    
    if dht11Result.is_valid():
        currentTemperature = dht11Result.temperature
        currentHumidity = dht11Result.humidity
        
        # Temperature Alerts
        advisoryMessage = "🚨AUTOMATED ALERT: \n" + getTemperatureAdvMsg(currentTemperature)
        
        if (datetime.now() - last_temperature_alert_time).total_seconds() >= TEMPERATURE_COOLDOWN_PERIOD:
            await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=temperatureInlineKeyboard)
            last_temperature_alert_time = datetime.now()
        
        # Humidity Alerts
        advisoryMessage = "🚨AUTOMATED ALERT: \n" + getHumidityAdvMsg(currentHumidity)
        
        print(type(last_humidity_alert_time))
        print(type(HUMIDITY_COOLDOWN_PERIOD))
        
        if (datetime.now() - last_humidity_alert_time).total_seconds() >= HUMIDITY_COOLDOWN_PERIOD:
            await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=humidityInlineKeyboard)
            last_humidity_alert_time = datetime.now()
    
    
    
    perc2 = mq2.MQPercentage()
    perc135 = mq135.MQPercentage()
    
    """
    # Read sensor data from CH7 of MCP3008
    mq135_value = read_adc(7)
    
    # Convert the sensor value to PPM
    ppm = round(convert_to_ppm(mq135_value))
    
    if (ppm > 0) and (ppm < 500):
        # Air Quality Alerts
        advisoryMessage = "🚨AUTOMATED ALERT: \n" + getAirQualityAdvMsg(ppm)
        
        if (datetime.now() - last_airquality_alert_time).total_seconds() >= AIRQUALITY_COOLDOWN_PERIOD:
            await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=airqualityInlineKeyboard)
            last_airquality_alert_time = datetime.now()
    """
    
    return
        
    """
    else:
        await context.bot.send_message(job.chat_id, text="Alarm DHT11 Error")
    """
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user for their command."""
    user = update.message.from_user
    reply_keyboard = [
                        ['Temperature'],
                        ['Humidity'],
                        ['Air Quality'],
                        #['PSI'],
                        ['Alerts On/Off']
                        ]
    msg = ("Hi " + user.first_name + ", welcome to TravelSensor Bot!"
            + "\n\n"
            + "What can this bot do?"
            + "\n"
            + "TravelSensor is your ultimate travel companion, ensuring your safety and well-being. Linked to a Raspberry Pi device attached to your bag, our bot provides real-time environmental data, giving you peace of mind on your journeys."
            + "\n\n"
            + "🚨 Alerts and Notifications"
            + "Receive instant updates on temperature, humidity, and various gases you are exposed to. If you encounter extreme conditions, TravelSensor will notify you, allowing you to take immediate action and protect yourself."
            + "\n\n"
            + "📊 Query Data"
            + "Want to check the current status of your environment? Simply ask TravelSensor for the latest environmental data, and it will provide you with detailed information to ensure everything is in order."
            + "\n\n"
            + "Start your worry-free travels with TravelSensor today! Type /help to explore all available commands and features. Safe travels!")

    """
    msg = ("Hi " + user.first_name + "! My name is Sensor Bot, nice to meet you!\n"
        + "Send /cancel at any time to stop talking to me.\n"
        + "Please select a command below.")
    """
    
    placeholder_msg = "Command?"
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, input_field_placeholder=placeholder_msg
        ),
    )
    
    chat_id = str(update.message.chat_id)
    
    context.job_queue.run_repeating(alarm, 10, chat_id=chat_id, name=str(chat_id))
    #context.job_queue.run_once(alarm, 1, chat_id=chat_id, name=str(chat_id), data=due)
    
    return COMMAND

async def command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected command and ask for next command."""
    
    global automatedAlertFlag, last_temperature_alert_time, last_humidity_alert_time, last_airquality_alert_time
    
    user = update.message.from_user
    print(f"Command of {user.first_name}: {update.message.text}")
    #loggerInstance.info("Command of %s: %s", user.first_name, update.message.text)
    
    dht11Result = dht11Instance.read()
    
    count = 0
    if (update.message.text == "Temperature"):
        while (True):
            dht11Result = dht11Instance.read()
            if dht11Result.is_valid():
                currentTemperature = dht11Result.temperature
                advisoryMessage = getTemperatureAdvMsg(currentTemperature)
                last_temperature_alert_time = TEMPERATURE_COOLDOWN_PERIOD;
                await update.message.reply_text(text=advisoryMessage, reply_markup=temperatureInlineKeyboard)
                break
            else:
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load temperature, possibly caused by loose wiring",
                    )
                    break;
                await update.message.reply_text("Loading Temperature...")
                count += 1
                time.sleep(1)
    
    elif (update.message.text == "Humidity"):
        while (True):
            dht11Result = dht11Instance.read()
            if dht11Result.is_valid():
                currentHumidity = dht11Result.humidity
                advisoryMessage = getHumidityAdvMsg(currentHumidity)
                last_humidity_alert_time = HUMIDITY_COOLDOWN_PERIOD;
                await update.message.reply_text(text=advisoryMessage, reply_markup=humidityInlineKeyboard)
                break
            else:
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load temperature, possibly caused by loose wiring",
                    )
                    break;
                await update.message.reply_text("Loading Humidity...")
                count += 1
                time.sleep(1)
                
    elif (update.message.text == "Air Quality"):
        while (True):
               
            break
    
    elif (update.message.text == "Alerts On/Off"):
        if automatedAlertFlag:
            alertMessage = "Automated alerts disabled"
        else:
            alertMessage = "Automated alerts enabled"
            last_temperature_alert_time = TEMPERATURE_COOLDOWN_PERIOD;
            last_humidity_alert_time = HUMIDITY_COOLDOWN_PERIOD;
        automatedAlertFlag = not automatedAlertFlag
        await update.message.reply_text(text=alertMessage)
        
    else:
        await update.message.reply_text(
            STANDARD_ERROR_MESSAGE
        )
    return COMMAND # TODO redundant

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    #loggerInstance.info("User %s canceled the conversation.", user.first_name)
    print(f"User {user.first_name} canceled the conversation.", )
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Add conversation handler
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEBOT_API_KEY).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COMMAND: [MessageHandler(filters.Regex("^(Temperature|Humidity|Air Quality|Alerts On/Off)$"), command)],
            #COMMAND: [MessageHandler(filters.Regex("^(Temperature|Humidity|Air Quality|PSI|Alerts On/Off)$"), command)],
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
    dht11Instance = dht11.DHT11(pin=DHT11_PIN)
    
    # MQ135 Gas Sensor Calibration + Initilization
    mq2 = MQ2(MQ2_MCP3008_PIN);
    mq135 = MQ135(MQ135_MCP3008_PIN);
    
    main()
    
"""
Reference Material(s)
Telegram Bot                        https://docs.python-telegram-bot.org/en/v20.5/examples.html
DHT11 example                       https://github.com/szazo/DHT11_Python
MQ135 gas sensor                    https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/
"""
