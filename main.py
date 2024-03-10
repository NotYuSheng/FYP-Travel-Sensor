#!/usr/bin/python3

import os, sys, time
import RPi.GPIO as GPIO
import board
import adafruit_dht

from dotenv import load_dotenv
from datetime import datetime, timedelta
from decouple import config

from mq2 import *
from mq135 import *
#from lib.mq import MQ # TODO Remove this

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler, Updater

DHT11_PIN = board.D17 # GPIO 17
MQ2_MCP3008_PIN = 0 # MCP3008 CH0
MQ135_MCP3008_PIN = 1 # MCP3008 CH1

TEMPERATURE_COOLDOWN_PERIOD = 300 # 5 minute
HUMIDITY_COOLDOWN_PERIOD = 300 # 5 minute
AIRQUALITY_COOLDOWN_PERIOD = 300 # 5 minutes
SMOKE_COOLDOWN_PERIOD = 300 # 5 minutes

# TODO, CALIBRATE
SMOKE_THRESHOLD = 5.0
ALCOHOL_THRESHOLD = 5.0
LPG_THRESHOLD = 5.0
CH4_THRESHOLD = 5.0
PROPANE_THRESHOLD = 5.0

automatedAlertFlag = 1 # When set(1), automated alerts will trigger per period

last_temperature_alert_time = datetime.now() - timedelta(seconds=TEMPERATURE_COOLDOWN_PERIOD)
last_humidity_alert_time = datetime.now() - timedelta(seconds=HUMIDITY_COOLDOWN_PERIOD)
last_airquality_alert_time = datetime.now() - timedelta(seconds=AIRQUALITY_COOLDOWN_PERIOD)
last_smoke_alert_time = datetime.now() - timedelta(seconds=SMOKE_COOLDOWN_PERIOD)

temperatureInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("More details", url="https://www.nea.gov.sg/media/news/news/index/new-heat-stress-advisory-launched-to-guide-public-on-minimising-risk-of-heat-related-illnesses")],
])

humidityInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("More details", url="https://www.nea.gov.sg/media/news/news/index/new-heat-stress-advisory-launched-to-guide-public-on-minimising-risk-of-heat-related-illnesses")],
])

airqualityInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("More details", url="https://www.haze.gov.sg/")],
])

smokeInlineKeyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("More details", url="https://www.haze.gov.sg/")],
    #[InlineKeyboardButton("Button 2", callback_data="button2_data")],
])

# Load environment variables from .env file
load_dotenv()

# Access environment variables
TELEBOT_API_KEY = os.environ['TELEBOT_API_KEY']

# Static variables
STANDARD_ERROR_MESSAGE = "Seems like something expected has occured...\nThis incident has been recorded"
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
            "Category: 🌵 Dry \n"
            "Extremely low humidity! Be mindful of potential dehydration and increased risk of static electricity".format(humidity)
        )
        
    elif humidity >= 20 and humidity < 40:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: 🍃 Comfortable \n"
            "Enjoy the comfortable humidity levels!".format(humidity)
        )            
        
    elif humidity >= 40 and humidity < 60:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: 🌱 Moderate \n"
            "Moderate Humidity levels. Stay hydrated and comfortable".format(humidity)
        )
    
    elif humidity >= 60 and humidity < 80:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: 💧 Humid \n"
            "Humidity on the rise! Be cautious of potential discomfort due to higher moisture levels".format(humidity)
        )
    
    elif humidity >= 80:
        advisoryMessage = (
            "Humidity: {:.1f}% \n"
            "Category: 🌊 High \n"
            "High humidity alert! Take precautions to stay cool and comfortable".format(humidity)
        )
    return advisoryMessage

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message when sensor value exceed threshold."""

    global automatedAlertFlag, last_temperature_alert_time, last_humidity_alert_time, last_airquality_alert_time
    
    # End process if alert disabled
    if (not automatedAlertFlag):
        return
    
    job = context.job
    try:
        currentTemperature = dht11.temperature
        currentHumidity = dht11.humidity
        
        # Temperature Alerts
        if currentTemperature >= 31:
            advisoryMessage = "🚨AUTOMATED ALERT: \n" + getTemperatureAdvMsg(currentTemperature)
            
            if (datetime.now() - last_temperature_alert_time).total_seconds() >= TEMPERATURE_COOLDOWN_PERIOD:
                await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=temperatureInlineKeyboard)
                last_temperature_alert_time = datetime.now()
        
        # Humidity Alerts
        if currentHumidity < 20 or currentHumidity >= 60:
            advisoryMessage = "🚨AUTOMATED ALERT: \n" + getHumidityAdvMsg(currentHumidity)
            
            if (datetime.now() - last_humidity_alert_time).total_seconds() >= HUMIDITY_COOLDOWN_PERIOD:
                await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=humidityInlineKeyboard)
                last_humidity_alert_time = datetime.now()
    
    except Exception as e:
        print(f"Error code #1: An error occurred: {e}")
        print(f"    Note: Errors happen fairly often, DHT11's are hard to read, don't worry and just requery.")

    try:
        advisoryMessage = ""
        percMQ2 = mq2.MQPercentage()
        percMQ135 = mq135.MQPercentage()

        lpgPPM = percMQ2["LPG"]
        coPPM = percMQ2["CO"]
        smokePPM = percMQ2["SMOKE"]
        propanePPM = percMQ2["PROPANE"]
        h2PPM = percMQ2["H2"] # Hydrogen
        alcoholPPM = percMQ2["ALCOHOL"]
        ch4PPM = percMQ2["CH4"] # Methane

        acetonPPM = percMQ135["ACETON"]
        toluenoPPM = percMQ135["TOLUENO"]
        alcoholPPM = percMQ135["ALCOHOL"]
        co2PPM = percMQ135["CO2"]
        nh4PPM = percMQ135["NH4"]
        coPPM = percMQ135["CO"]
        
        if lpgPPM > LPG_THRESHOLD or ch4PPM > CH4_THRESHOLD or propanePPM > PROPANE_THRESHOLD:
            advisoryMessage += "Warning: Flammable gas detected in your environment. Please take immediate precautions and assess the situation.\n"
        if smokePPM > SMOKE_THRESHOLD:
            advisoryMessage += "Warning: Smoke has been detected in your environment. Please take precautions and assess the situation.\n"
        if alcoholPPM > ALCOHOL_THRESHOLD:
            advisoryMessage += "Warning: Alcohol has been detected in your environment. Please be cautious and ensure a safe and well-ventilated space.\n"
        if advisoryMessage != "":
            await update.message.reply_text(text=advisoryMessage)
    except Exception as e:
        print(f"Error code #6: An error occurred: {e}")
        
    return
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user for their command."""
    user = update.message.from_user
    reply_keyboard = [
                        ['Temperature'],
                        ['Humidity'],
                        ['Air Quality'],
                        ['Smoke'],
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
    
    placeholder_msg = "Command?"
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, input_field_placeholder=placeholder_msg
        ),
    )
    
    chat_id = str(update.message.chat_id)
    
    context.job_queue.run_repeating(alarm, 10, chat_id=chat_id, name=str(chat_id))
    
    return COMMAND

async def command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected command and ask for next command."""
    
    global automatedAlertFlag, last_temperature_alert_time, last_humidity_alert_time, last_airquality_alert_time
    
    user = update.message.from_user
    print(f"Command of {user.first_name}: {update.message.text}")
    
    count = 0
    if (update.message.text == "Temperature"):
        while True:
            try:
                currentTemperature = dht11.temperature
                advisoryMessage = getTemperatureAdvMsg(currentTemperature)
                last_temperature_alert_time = datetime.now()
                await update.message.reply_text(text=advisoryMessage, reply_markup=temperatureInlineKeyboard)
                break
            except Exception as e:
                print(f"Error code #2: An error occurred: {e}")
                print(f"    Note: Errors happen fairly often, DHT11's are hard to read, don't worry and just requery.")
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load temperature, possibly caused by loose wiring",
                    )
                    break
                await update.message.reply_text("Loading Temperature...")
                count += 1
                time.sleep(1)
    
    elif (update.message.text == "Humidity"):
        while True:
            try:
                currentHumidity = dht11.humidity
                advisoryMessage = getHumidityAdvMsg(currentHumidity)
                last_humidity_alert_time = datetime.now()
                await update.message.reply_text(text=advisoryMessage, reply_markup=humidityInlineKeyboard)
                break
            except Exception as e:
                print(f"Error code #3: An error occurred: {e}")
                print(f"    Note: Errors happen fairly often, DHT11's are hard to read, don't worry and just requery.")
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load temperature, possibly caused by loose wiring",
                    )
                    break
                await update.message.reply_text("Loading Humidity...")
                count += 1
                time.sleep(1)
                
    elif (update.message.text == "Air Quality"):
        while True: 
            try:
                advisoryMessage = ""
                percMQ2 = mq2.MQPercentage()
                percMQ135 = mq135.MQPercentage()

                lpgPPM = percMQ2["LPG"]
                coPPM = percMQ2["CO"]
                smokePPM = percMQ2["SMOKE"]
                propanePPM = percMQ2["PROPANE"]
                h2PPM = percMQ2["H2"] # Hydrogen
                alcoholPPM = percMQ2["ALCOHOL"]
                ch4PPM = percMQ2["CH4"] # Methane

                acetonPPM = percMQ135["ACETON"]
                toluenoPPM = percMQ135["TOLUENO"]
                alcoholPPM = percMQ135["ALCOHOL"]
                co2PPM = percMQ135["CO2"]
                nh4PPM = percMQ135["NH4"]
                coPPM = percMQ135["CO"]
                
                print("----------MQ2----------")
                print("LPG: %g ppm, CO: %g ppm, Smoke %g ppm, Propane %g ppm, H2 %g ppm, Alcohol: %g ppm, CH4: %g ppm" % (percMQ2["LPG"], percMQ2["CO"], percMQ2["SMOKE"], percMQ2["PROPANE"], percMQ2["H2"], percMQ2["ALCOHOL"], percMQ2["CH4"]))
                print("---------MQ135---------")
                print("ACETON: %g ppm, TOLUENO: %g ppm, ALCOHOL: %g ppm, CO2: %g ppm, NH4: %g ppm, CO: %g ppm" % (percMQ135["ACETON"], percMQ135["TOLUENO"], percMQ135["ALCOHOL"], percMQ135["CO2"], percMQ135["NH4"], percMQ135["CO"]))
                
                if lpgPPM > LPG_THRESHOLD or ch4PPM > CH4_THRESHOLD or propanePPM > PROPANE_THRESHOLD:
                    advisoryMessage += "Warning: Flammable gas detected in your environment. Please take immediate precautions and assess the situation.\n"
                if smokePPM > SMOKE_THRESHOLD:
                    advisoryMessage += "Warning: Smoke has been detected in your environment. Please take precautions and assess the situation.\n"
                if alcoholPPM > ALCOHOL_THRESHOLD:
                    advisoryMessage += "Warning: Alcohol has been detected in your environment. Please be cautious and ensure a safe and well-ventilated space.\n"
                if advisoryMessage != "":
                    await update.message.reply_text(text=advisoryMessage, reply_markup=airqualityInlineKeyboard)
                    break
                else:
                    advisoryMessage = "Great news! No dangerous gases have been detected in your environment. Enjoy the peace of mind and breathe freely in a safe and healthy atmosphere."
                    await update.message.reply_text(text=advisoryMessage)
                    break
            except Exception as e:
                print(f"Error code #4: An error occurred: {e}")
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load air quality, possibly caused by loose wiring",
                    )
                    break
                await update.message.reply_text("Loading Air Quality...")
                count += 1
                time.sleep(1)
            break

    elif (update.message.text == "Smoke"):
        while True: 
            try:
                percMQ2 = mq2.MQPercentage()
                smokePPM = percMQ2["SMOKE"]
                print("SMOKE: %g ppm" % (percMQ2["SMOKE"]))
                
                if smokePPM > SMOKE_THRESHOLD:
                    advisoryMessage = "Warning: Smoke has been detected in your environment. Please take precautions and assess the situation."
                else:
                    advisoryMessage = "Your environment is currently clear of smoke. Enjoy the clean air!"
                
                await update.message.reply_text(text=advisoryMessage, reply_markup=smokeInlineKeyboard)
            except Exception as e:
                print(f"Error code #5: An error occurred: {e}")
                if (count > 3):
                    await update.message.reply_text(
                        "Failed to load smoke, possibly caused by loose wiring",
                    )
                    break
                await update.message.reply_text("Loading Smoke...")
                count += 1
                time.sleep(1)
            break
    
    elif (update.message.text == "Alerts On/Off"):
        if automatedAlertFlag:
            alertMessage = "Automated alerts disabled"
        else:
            alertMessage = "Automated alerts enabled"
            last_temperature_alert_time = datetime.now() - timedelta(seconds=TEMPERATURE_COOLDOWN_PERIOD)
            last_humidity_alert_time = datetime.now() - timedelta(seconds=HUMIDITY_COOLDOWN_PERIOD)
            last_airquality_alert_time = datetime.now() - timedelta(seconds=AIRQUALITY_COOLDOWN_PERIOD)
            last_smoke_alert_time = datetime.now() - timedelta(seconds=SMOKE_COOLDOWN_PERIOD)
        
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
    print(f"User {user.first_name} canceled the conversation.", )
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEBOT_API_KEY).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COMMAND: [MessageHandler(filters.Regex("^(Temperature|Humidity|Air Quality|Smoke|Alerts On/Off)$"), command)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("Bot shut down")

if __name__ == "__main__":
    # DHT11 Temperature and Humidity Sensor Initialization
    dht11 = adafruit_dht.DHT11(DHT11_PIN)
    
    # MQ2 & MQ135 Gas Sensors Calibration + Initilization
    mq2 = MQ2(MQ2_MCP3008_PIN)
    mq135 = MQ135(MQ135_MCP3008_PIN)
    print("Initialization complete!")
    main()
    
"""
Reference Material(s)
Telegram Bot                        https://docs.python-telegram-bot.org/en/v20.5/examples.html
DHT11 example                       https://github.com/szazo/DHT11_Python
"""
