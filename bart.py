#!/usr/bin/env python2.7
"""
Eric's BART Mini-app
"""
import json
import logging
from bs4 import BeautifulSoup as bs
from flask import (Flask, request)
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


class APIError(Exception):
  """Raised when someone else screwed up"""


def get_station(loc):
  """Find the closest station location.

  Uses Google DistanceMatrix, which is why the logic is a bit torturous.
  Params:
    loc: latitude and longitude, comma separated string
  Returns:
    station: dictionary with details about the closest station
  Raises:
    APIError
  """
  dests = "%s|%s" % (CIVIC_CENTER['loc'], BERKELEY['loc'])
  try:
    dist = json.loads(get(GOOGLE_URL % (loc, dests)).text)
    dist = [d['distance']['value'] for d in dist['rows'][0]['elements']]
  except:
    raise APIError("Couldn't find the closest station")
  return CIVIC_CENTER if dist[0] < dist[1] else BERKELEY


def get_trains(station):
  """Find estimated departure times for the given station.

  Uses BART's API, which returns XML for some godawful reason.

  Params:
    station: dictionary for station for which to fetch times
  Returns:
    (times, destination): Tuple: List of train times and lengths, name of line.
  Raises:
    APIError
  """
  try:
    train_soup = bs(get(BART_ETD % station).text)
  except:
    raise APIError("Couldn't get train estimates from BART")
  # XML is a god-awful language for an API.
  etd = [e.parent for e in train_soup("abbreviation", text=lambda x: x in station['dest'])]
  if not etd:
    etd = [e.parent for e in train_soup("abbreviation", text=lambda x: x == station['alt'])]
  if not etd:
    return [], "No trains running."
  trains = [(e.find('minutes').text, e.find('length').text) for e in etd[0]('estimate')]
  return trains, etd[0].find('destination').text


@app.errorhandler(APIError)
def report_error(error):
  """Report API failure messages"""
  logging.exception(error.args[0], error)
  return error.args[0], 500


@app.route('/loc', methods=['POST'])
def get_times():
  """Use posted location to retrieve closest station and departure times.

  Params (POST):
    loc: Latitude and Longitude, comma-separated.
  Returns (JSON):
    station: Name of closest station
    abbr: Station abbreviation
    dest: Line for train estimates
    trains: List of estimated train departures and lengths
  """
  loc = request.form.get('loc', DEFAULT_LOCATION)
  station = get_station(loc)
  trains, line = get_trains(station)
  return json.dumps({
    'station': station['name'],
    'abbr': station['abbr'],
    'dest': line,
    'trains': trains
  })


@app.route('/adv', methods=['POST'])
def get_advisory():
  """Get current advisories for the posted station.

  Params (POST):
    stn: Station abbreviation
  Returns (JSON):
    adv: Current BART Advisory, or empty string if none.
  """
  try:
    stn = request.form.get('stn')
    adv = bs(get(BART_ADV % stn).text)
    msg = adv.find('sms_text').text
  except:
    # Don't want to raise any errors from this call
    msg = ''
  return json.dumps({'adv': msg})

if __name__ == "__main__":
  app.debug = True
  app.run()
