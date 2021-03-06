from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from crimeAPI.models import Crime
from interactivesBackend import secrets

import geopy

import time

class Command(BaseCommand):
    help = 'Geocode as many crimes as possible, starting with the most recent non-geocoded and working backwards'

    def handle(self, *args, **options):
        crimes = Crime.objects.all().filter(geocoded=False).order_by('-offense_time')[:2500]
        
        startTime = time.clock()
        for crime in crimes:
            geocoder = geopy.geocoders.GoogleV3(api_key = secrets.API_KEY)
            if time.clock() - startTime < 0.2: # rate limited to 5 per second
                sleepTime = .2 - (time.clock() - startTime) # prevent giving time.sleep
                                                            # a negative number
            if sleepTime > 0:
                time.sleep(sleepTime)

            try:
                query = crime.offense_address
                crimeLocInfo = geocoder.geocode(query = query)
                startTime = time.clock()
                crime.geocode_location = Point(crimeLocInfo.longitude, crimeLocInfo.latitude)
                crime.geocoded = True
                crime.save()
            except geopy.exc.GeocoderQueryError:
                pass
            except geopy.exc.GeocoderQuotaExceeded:
                # out of queries
                break
            except geopy.exc.GeocoderTimedOut:
                pass
            except AttributeError:
               pass
