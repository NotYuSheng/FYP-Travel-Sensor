#!/usr/bin/python3

import os, sys, time
import RPi.GPIO as GPIO
import board
import adafruit_dht

from lib.MCP3008 import MCP3008

from dotenv import load_dotenv
from datetime import datetime, timedelta
from decouple import config

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes, ConversationHandler, filters, MessageHandler, Updater

DHT11_PIN = board.D17 # GPIO 17
MQ2_MCP3008_PIN = 0 # MCP3008 CH0
MQ135_MCP3008_PIN = 1 # MCP3008 CH1

TEMPERATURE_COOLDOWN_PERIOD = 60 # 1 minute
HUMIDITY_COOLDOWN_PERIOD = 60 # 1 minute
AIRQUALITY_COOLDOWN_PERIOD = 60 # 1 minutes
SMOKE_COOLDOWN_PERIOD = 60 # 1 minutes

MQ2_THRESHOLD = 2000
MQ135_THRESHOLD = 800

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

    global automatedAlertFlag, last_temperature_alert_time, last_humidity_alert_time, last_airquality_alert_time, last_smoke_alert_time
    
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

    # Air Quality Alert
    try:
        if adc.read(MQ135_MCP3008_PIN) >= MQ135_THRESHOLD:
            print(f"Air Quality: {adc.read(MQ135_MCP3008_PIN)}")
            advisoryMessage = "🚨AUTOMATED ALERT: \n"
            advisoryMessage += "MQ135 gas sensor detected the presence of gas in your environment. The detected gas may include ammonia, nitrogen oxides, benzene, alcohol, carbon dioxide (CO2), or other harmful gases.\n\n"
            advisoryMessage += "The presence of these gases may indicate various sources such as leaks, emissions from vehicles or industrial processes, or inadequate ventilation, posing risks to health and safety.\n\n"
            advisoryMessage += "Take immediate action to ventilate area, evacuate, and contact authorities. "
            await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=airqualityInlineKeyboard)
            last_airquality_alert_time = datetime.now()
    except Exception as e:
        print(f"Error code #6: An error occurred: {e}")
    
    # Smoke Alert
    try:
        if adc.read(MQ2_MCP3008_PIN) >= MQ2_THRESHOLD:
            print(f"Smoke: {adc.read(MQ2_MCP3008_PIN)}")
            advisoryMessage = "🚨AUTOMATED ALERT: \n"
            advisoryMessage += "MQ2 gas sensor detected the presence of gas in your environment. The detected gas may include LPG, propane, hydrogen, methane, smoke, or other combustible gases.\n\n"
            advisoryMessage += "The presence of these gases may indicate a gas leak\n\n"
            advisoryMessage += "Take immediate action to ventilate area, evacuate, and contact authorities. "
            await context.bot.send_message(job.chat_id, text=advisoryMessage, reply_markup=smokeInlineKeyboard)
            last_smoke_alert_time = datetime.now()
    except Exception as e:
        print(f"Error code #7: An error occurred: {e}")
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
                last_airquality_alert_time = datetime.now()
                
                if adc.read(MQ135_MCP3008_PIN) >= MQ135_THRESHOLD:
                    advisoryMessage = "MQ135 gas sensor detected the presence of gas in your environment. The detected gas may include ammonia, nitrogen oxides, benzene, alcohol, carbon dioxide (CO2), or other harmful gases.\n\n"
                    advisoryMessage += "The presence of these gases may indicate various sources such as leaks, emissions from vehicles or industrial processes, or inadequate ventilation, posing risks to health and safety.\n\n"
                    advisoryMessage += "Take immediate action to ventilate area, evacuate, and contact authorities. "
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
                last_smoke_alert_time = datetime.now()
                
                if adc.read(MQ2_MCP3008_PIN) > MQ2_THRESHOLD:
                    advisoryMessage = "💨 MQ2 gas sensor detected the presence of gas in your environment. The detected gas may include LPG, propane, hydrogen, methane, smoke, or other combustible gases.\n\n"
                    advisoryMessage += "The presence of these gases may indicate a gas leak\n\n"
                    advisoryMessage += "Take immediate action to ventilate area, evacuate, and contact authorities. "
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
    return COMMAND

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
    
    # adc Declaration
    adc = MCP3008()
    
    
    while True:
        os.system("clear")
        print(f"Smoke: {adc.read(MQ2_MCP3008_PIN)}")
        print(f"Air Quality: {adc.read(MQ135_MCP3008_PIN)}")
        time.sleep(1)
    
    
    print("Initialization complete!")
    main()
    
"""
Reference Material(s)
Telegram Bot                        https://docs.python-telegram-bot.org/en/v20.5/examples.html
DHT11 example                       https://github.com/szazo/DHT11_Python
"""
