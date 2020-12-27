# !/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from requests import get
import time
import datetime
import requests
from geopy.distance import geodesic
from os import environ
from dotenv import load_dotenv
import emoji

load_dotenv()

WEATHERAPI = environ['WEATHERAPI'] 
BOTTOKEN = environ['BOTTOKEN'] 
MYTLGID = int(environ['MYTLGID'])
CANGAUDIR =(float(environ['HOMELAT']), float(environ['HOMELONG']))
WEB = environ['WEB']
INTRANET = environ['INTRANET']
ENTRADES = environ['ENTRADES']

BINANCE = "https://api.binance.com"


goodWeather = ['Clear', 'Clouds']


class Station(object):

    def __init__(self, name, lat, long, dist):
        self.name = name
        self.lat = lat
        self.long = long
        self.elec = 0
        self.mech = 0
        self.distance = dist
        self.status = False

def fetchBicing(location):
    myLocation = location
    si = json.loads(requests.get('https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_information').content)
    ss = json.loads(requests.get('https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_status').content)['data'][
        'stations']
    id = 0
    stations = []
    for station in si['data']['stations']:
        stLocation = (station['lat'], station['lon'])
        dist = geodesic(myLocation, stLocation).meters
        s = Station(station['name'], station['lat'], station['lon'], dist)
        s.status = ss[id]['status']
        s.mech = int(ss[id]['num_bikes_available_types']['mechanical'])
        s.elec = int(ss[id]['num_bikes_available_types']['ebike'])
        if s.status == 'IN_SERVICE' and s.mech + s.elec > 0:
            stations.append(s)
        id += 1
    stations.sort(key=lambda x: x.distance)
    message =[]
    for i in range(0, 3):
        message.append(f'{stations[i].name} amb:\nBicis elèctriques: {stations[i].elec}\nBicis mecàniques: ' \
                   f'{stations[i].mech}\nDistància: {int(stations[i].distance)} metres\n')

    return message

def removeDailyWeather(update, context):

    j = jobQ.get_jobs_by_name(update.message.chat_id)
    if j:
        j[0].schedule_removal()
        message = context.bot.sendMessage(chat_id=update.message.chat_id,
                                          text='Lo siento, no le volvere a molestar mi amo')
    else:
        message = context.bot.sendMessage(chat_id=update.message.chat_id, text='No le iba a avisar puto')

def setDailyWeather(update, context):
    if not jobQ.get_jobs_by_name(update.message.chat_id):
        message = context.bot.sendMessage(chat_id=update.message.chat_id,
                                          text='Si mi amo, voy a mirar al cielo cada dia')
        jobQ.run_daily(runDailyWeather, datetime.time(6, 30, 00, 000000), name=update.message.chat_id, context=update.message.chat_id)

    else:
        message = context.bot.sendMessage(chat_id=update.message.chat_id, text='Ya le estaba avisando puto')


def weather():
    temps = json.loads(requests.get(WEATHERAPI).text)
    state = ''
    start = 7
    message = ''
    for hora in temps['hourly'][:14]:

        for w in hora['weather']:
            if w['description'] != state:
                if state is '':
                    start = time.localtime(hora['dt']).tm_hour
                    state = w['description']

                else:
                    end = time.localtime(hora['dt']).tm_hour
                    if (w['main'] not in goodWeather):
                        message += f'En les pròximes hores, des de les {start}:00 fins les {end}:00 tindrem un/a {w["description"]}\n'
                    state = w['description']
                    start = end

    return message if message else 'No es preveu mal temps'


def runWeather(update, context):
    message = context.bot.sendMessage(chat_id=update.message.chat_id, text=weather())

def runDailyWeather(context):
    message = context.bot.sendMessage(chat_id=context.job.context, text=weather())


def getPublicIP(update, context):
    if update.message.from_user.id == MYTLGID:
        message = context.bot.sendMessage(chat_id=update.message.chat_id, text=get('https://api.ipify.org').text)

def myBicing(update, context):

    if update.message.from_user.id == MYTLGID:
        try:
            message = fetchBicing(CANGAUDIR)
            for m in message:
                context.bot.sendMessage(chat_id=update.message.chat_id, text=m)

        except Exception as e:
            context.bot.sendMessage(chat_id=update.message.chat_id, text=f'Error al processar: {e}')
            print(e)


def serverCheck(context):

    try:
        web = requests.get(WEB).status_code
        if web != 200:
            updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que la web esta caiguda')
    except:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que la web esta caiguda')
    try:
        entrades = requests.get(ENTRADES).status_code
        if entrades != 200:
            updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que les entrades esta caigudes')
    except:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que la entrades esta caiguda')
    try:
        intranet = requests.get(INTRANET).status_code
        if intranet != 200:
            updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que la intranet esta caiguda')
    except:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":computer::computer:", use_aliases=True)} Sembla que la intranet esta caiguda')



def specialMessage(update, context):

    # if update.message.new_chat_photo:
    #     message = context.bot.sendPoll(chat_id=update.message.chat_id, question="FoC", options=['F', 'C'], is_anonymous=False)

    if update.message.chat.type in ['supergroup', 'group']:
        if 'engrescat' in update.message.text.lower():
            message = context.bot.sendAnimation(chat_id=update.message.chat_id, animation='https://giphy.com/gifs/U5UieHLUiMpisOzAe5')
    if update.message.location:
        myLocation = (update.message['location']['latitude'], update.message['location']['longitude'])

        try:
            message = fetchBicing(myLocation)

            for m in message:
                context.bot.sendMessage(chat_id=update.message.chat_id, text=m)

        except Exception as e:
            if update.message.from_user.id == MYTLGID:
                context.bot.sendMessage(chat_id=update.message.chat_id, text=f'Error al processar: {e}')
            print(e)


'''Binance api messages'''

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def btcPrice(update, context):
    dollars = float(json.loads(requests.get(f'{BINANCE}/api/v3/ticker/price?symbol=BTCUSDT').text)['price'])
    eur = float(json.loads(requests.get(f'{BINANCE}/api/v3/ticker/price?symbol=BTCEUR').text)['price'])
    context.bot.sendMessage(chat_id=update.message.chat_id, text=f'Preu del bitcoin:  {dollars}$ ({eur}€)')

def bitcoinWatch(context):
    global BTCUSD
    dollars = float(json.loads(requests.get(f'{BINANCE}/api/v3/ticker/price?symbol=BTCUSDT').text)['price'])
    eur = float(json.loads(requests.get(f'{BINANCE}/api/v3/ticker/price?symbol=BTCEUR').text)['price'])
    if BTCUSD == 0:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'Bot just booted up, price monitoring at: {dollars}$ ({eur}€)',)
        BTCUSD = truncate(dollars, -3)
        print(f'dollars:{dollars}    '
              f'BTCUSD: {BTCUSD}')
    elif truncate(dollars, -3) > BTCUSD:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":chart_with_upwards_trend:", use_aliases=True)} '
                                                      f'BTC Up! {dollars}$ ({eur}€)')
        BTCUSD = truncate(dollars, -3)
        print(f'dollars:{dollars}    '
              f'BTCUSD: {BTCUSD}')
    elif truncate(dollars, -3) < BTCUSD:
        updater.bot.sendMessage(chat_id=MYTLGID, text=f'{emoji.emojize(":chart_with_downwards_trend:", use_aliases=True)} '
                                                      f'BTC Down! {dollars}$ ({eur}€)')
        BTCUSD = truncate(dollars, -3)
        print(f'dollars:{dollars}    '
              f'BTCUSD: {BTCUSD}')


"""Run the bot."""
BTCUSD = 0
updater = Updater(token=BOTTOKEN, use_context=True)
jobQ = updater.job_queue

dp = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
dp.add_handler(CommandHandler('weather', runWeather))
dp.add_handler(CommandHandler('ip', getPublicIP))
dp.add_handler(CommandHandler('bicing', myBicing))
dp.add_handler(CommandHandler('btc', btcPrice))
dp.add_handler(CommandHandler('startWeather', setDailyWeather, pass_job_queue=True))
dp.add_handler(CommandHandler('stopWeather', removeDailyWeather, pass_job_queue=True))
dp.add_handler(MessageHandler(Filters.all, specialMessage))

jobQ.run_repeating(serverCheck, 300)
jobQ.run_once(bitcoinWatch, 0)
jobQ.run_repeating(bitcoinWatch, 300)
updater.start_polling()
updater.idle()




