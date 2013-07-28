import json
import logging
import traceback
from bs4 import BeautifulSoup as bs
from flask import (
    Flask,
    render_template,
    request,
    )
from requests import get

ORIGIN = "37.777092,-122.415891"

# Boy, it's a lot easier to hardcode these.
CIVIC_CENTER = {
  'name': 'Civic Center',
  'loc': "37.779471,-122.413809",
  'abbr':'civc',
  'dir':'n',
  'dest':['RICH'],
  'alt':'PITT'
}

BERKELEY = {
  'name':'Downtown Berkeley',
  'loc':"37.869842,-122.267986",
  'abbr':'dbrk',
  'dir':'s',
  'dest':['MLBR','DALY'],
  'alt':'FRMT'
}


GOOGLE_URL = "http://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&sensor=false"
BART_ETD   = "http://api.bart.gov/api/etd.aspx?cmd=etd&orig=%(abbr)s&dir=%(dir)s&key=MW9S-E7SL-26DU-VV8V"
BART_ADV   = "http://api.bart.gov/api/bsa.aspx?cmd=bsa&orig=%s&key=MW9S-E7SL-26DU-VV8V"

app = Flask(__name__)

def get_station(loc):
  dests = "%s|%s" % (CIVIC_CENTER['loc'], BERKELEY['loc'])
  distances = json.loads(get(GOOGLE_URL % (loc, dests)).text)
  distances = [d['distance']['value'] for d in distances['rows'][0]['elements']]
  return CIVIC_CENTER if distances[0] > distances[1] else BERKELEY

def get_trains(station):
  is_alt = False
  train_soup = bs(get(BART_ETD % station).text)
  # XML is a god-awful language for an API.
  etd = [e.parent for e in train_soup("abbreviation", text=lambda x: x in station['dest'])]
  if not etd:
    etd = [e.parent for e in train_soup("abbreviation", text=lambda x: x == station['alt'])]
  if not etd:
    return [], "No trains running."
  trains = [(e.find('minutes').text, e.find('length').text) for e in etd[0]('estimate')]
  return trains, etd[0].find('destination').text

@app.route('/loc', methods=['POST'])
def get_times():
  try:
    loc = request.form.get('loc', ORIGIN)
    station = get_station(loc)
    trains, line = get_trains(station)
    return json.dumps({
      'station': station['name'],
      'abbr': station['abbr'],
      'dest': line,
      'trains': trains
    })
  except Exception as err:
    logging.exception("Error!")

@app.route('/adv', methods=['POST'])
def get_advisory():
  try:
    stn = request.form.get('stn')
    adv = bs(get(BART_ADV % stn).text)
    return json.dumps({'adv': adv.find('sms_text').text})
  except Exception as err:
    logging.exception("Error!!")

if __name__ == "__main__":
  app.debug = True
  app.run()
