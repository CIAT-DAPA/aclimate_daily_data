from datetime import datetime, time, timezone

from bson import ObjectId

import requests
import os
from dotenv import load_dotenv
import argparse
from classes.logger import init_logger
from classes.models import ClimaticData, DailyReading, MeasureClimatic, WeatherLinkHistoricalData, WeatherLinkSensorReading, WeatherLinkStation, WeatherStation, WeatherStationDailyData
from pymongo import MongoClient
from typing import Any, List

class DailyWeatherLinkLoader():

    def __init__(self):
        self.logger = init_logger()
        self.today = datetime.now(timezone.utc).date()
        print("running daily_weather_link_loader: " + str(self.today))
        load_dotenv()

        self.WeatherLink_API_KEY = self.get_env_var("WeatherLink_API_KEY")
        self.WeatherLink_API_SECRET: str = self.get_env_var("WeatherLink_API_SECRET")

        self.MONGODB_URI = self.get_env_var("MONGODB_URI")
        self.DATABASE_NAME: str = self.get_env_var("DATABASE_NAME")

        self.COUNTRY_PREFIX: str = self.get_env_var("COUNTRY_PREFIX")



    def get_env_var(self,name: str) -> str:
        value = os.getenv(name)
        assert value is not None, f"Environment variable {name} is not set!"
        return value


    def load_weather_link_stations(self) -> List[WeatherLinkStation]:
        url = 'https://api.weatherlink.com/v2/stations'
        params = {
            'api-key': self.WeatherLink_API_KEY
        }
        headers = {
            "X-Api-Secret": self.WeatherLink_API_SECRET
        }
        try:
            response = requests.get(url=url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return [WeatherLinkStation.model_validate(station) for station in data["stations"]]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error loading WeatherLink stations: {str(e)}")
            return []


    def load_weather_link_data(self, stationId: int):

        # Set time to 12:00:00 UTC
        noon_utc = datetime.combine(self.today, time(hour=12, tzinfo=timezone.utc))

        # Convert to timestamp in seconds since the epoch
        timestamp_seconds = int(noon_utc.timestamp())

        url = f'https://api.weatherlink.com/v2/historic/{stationId}'
        params:dict[str,Any] = {
            'api-key': self.WeatherLink_API_KEY,
            'start-timestamp': timestamp_seconds - (24 * 60 * 60),  # last 24 hours
            'end-timestamp': timestamp_seconds
        }

        headers = {
            "X-Api-Secret": self.WeatherLink_API_SECRET
        }
        try:
            response = requests.get(url=url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return WeatherLinkHistoricalData.model_validate(data)
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Error loading WeatherLink data for station {stationId}: {str(e)}")
            return None


    def aggregate_daily_reading(self, historical_data: WeatherLinkHistoricalData | None):

        if not historical_data:
            return None

        iss_sensor = self.find_iss_sensor(historical_data.sensors)

        if iss_sensor is None:
            print('No iss_sensor present in station: ' +
                str(historical_data.station_id))
            return None

        daily_data = iss_sensor.data

        if len(daily_data) == 0:
            print('iss_sensor readings are empty in station: ' +
                str(historical_data.station_id))
            return None

        precipitation: float = sum(
            [data.rainfall_mm for data in daily_data if data.rainfall_mm is not None])
        temp_min = min(
            [data.temp_out for data in daily_data if data.temp_out is not None], default=None)
        temp_max = max(
            [data.temp_out for data in daily_data if data.temp_out is not None], default=None)

        temp_values = list(
            filter(lambda d: d.temp_out is not None, daily_data))
        temp_avg = sum([data.temp_out for data in temp_values if data.temp_out is not None]
                    )/len(temp_values) if len(temp_values) > 0 else None

        solar_radiation: float = sum(
            [data.solar_rad_avg for data in daily_data if data.solar_rad_avg is not None])

        humidity_min = min(
            [data.hum_out for data in daily_data if data.hum_out is not None], default=None)
        humidity_max = max(
            [data.hum_out for data in daily_data if data.hum_out is not None], default=None)

        humidity_values = list(
            filter(lambda d: d.hum_out is not None, daily_data))
        humidity_avg = sum([data.hum_out for data in daily_data if data.hum_out is not None]
                        )/len(humidity_values) if len(humidity_values) > 0 else None

        daily_reading = DailyReading(
            day= self.today.day,
            data=[
                ClimaticData(measure=MeasureClimatic.PRECIPITATION,
                            value=precipitation),
                ClimaticData(measure=MeasureClimatic.TEMP_MIN, value=temp_min),
                ClimaticData(measure=MeasureClimatic.TEMP_MAX, value=temp_max),
                ClimaticData(measure=MeasureClimatic.TEMP_AVG, value=temp_avg),
                ClimaticData(measure=MeasureClimatic.SOLAR_RADIATION,
                            value=solar_radiation),
                ClimaticData(measure=MeasureClimatic.HUMIDITY_MIN,
                            value=humidity_min),
                ClimaticData(measure=MeasureClimatic.HUMIDITY_MAX,
                            value=humidity_max),
                ClimaticData(measure=MeasureClimatic.HUMIDITY_AVG,
                            value=humidity_avg),
            ]
        )
        return daily_reading


    def find_iss_sensor(self, sensors: List[WeatherLinkSensorReading]):
        return next((sensor_reading for sensor_reading in sensors
                    if sensor_reading.sensor_type in {37, 84}), None)


    def push_daily_reading(self, daily_reading: DailyReading, weather_station_id: ObjectId):

        client: MongoClient[Any] = MongoClient(self.MONGODB_URI)
        db = client[self.DATABASE_NAME]

        # get or create WeatherStationDailyData
        historical_daily_data = db['hs_historical_daily_data']

        # get current month and weather station
        current_year = self.today.year  # For example, 2023
        current_month = self.today.month  # For example, September

        # Check if a document exists for the current month and weather station
        query_filter:dict[str,Any] = {
            "year": current_year,
            "month": current_month,
            "weather_station": weather_station_id,
        }

        existing_document = historical_daily_data.find_one(query_filter)

        if existing_document:
            
            data = [climatic_data.model_dump() for climatic_data in daily_reading.data]

            update_query:dict[str,Any] = {
                "_id": existing_document["_id"],
                "daily_readings.day": daily_reading.day,
            }

            update_data = {"$set": {"daily_readings.$.data": data}}
            # try to update daily_reading if same day exists
            res = historical_daily_data.update_one(update_query, update_data)

            # if not daily_reading of same day exists, push new daily reading
            if res.matched_count == 0:
                insert_query = {"_id": existing_document["_id"]}
                insert_data = {"$push": {"daily_readings": daily_reading.model_dump()}}
                res = historical_daily_data.update_one(insert_query, insert_data)

        else:
            # Document doesn't exist, create a new one
            new_document = WeatherStationDailyData(
                weather_station=weather_station_id,
                month=current_month,
                year=current_year,
                daily_readings=[daily_reading]
            )

            res = historical_daily_data.insert_one(new_document.model_dump())
            

        client.close()


    def get_weather_stations(self, external_prefix: str):
        result: List[WeatherStation] = []
        try:
            client: MongoClient[Any] = MongoClient(self.MONGODB_URI)
            db = client[self.DATABASE_NAME]

            weather_station_collection = db['lc_weather_station']

            # Check if a document exists for weather station
            query_filter:dict[str,Any] = {
                "ext_id":  {"$regex": "^"+self.COUNTRY_PREFIX},
                "origin": "WEATHERLINK"
            }

            documents = weather_station_collection.find(query_filter)

           

            # Iterate over the cursor and convert each document to a WeatherStation
            for document in documents:
                weather_station = WeatherStation.model_validate(document)
                result.append(weather_station)

           
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Error loading WeatherStations for {external_prefix}: {str(e)}")
        return result


    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Load data into the database.")
        parser.add_argument('--source', type=str, required=True,
                            help='Source file to load data from')
        return parser.parse_args()


    def extract_external_station_id(self, input: str):
        prefix = self.COUNTRY_PREFIX
        if input.startswith(prefix):
            remaining_str = input[len(prefix):]  # Remove the prefix
            try:
                # Convert the remaining part to an integer
                return int(remaining_str)
            except ValueError:
                self.logger.error(
                    f"Error extracting external station id for {input}: Not an integer")
                return None
        else:
            self.logger.error(
                f"Error extracting external station id for {input}: Not starting with {prefix}")
            return None


    def main(self):
    # args = parse_arguments()

        self.logger.info(f"Start loading weather data")
        # weather_link_stations = load_weather_link_stations()
        weather_stations = self.get_weather_stations(external_prefix=self.COUNTRY_PREFIX)
        self.logger.info(f"Weather stations found: {len(weather_stations)} ")
       
        count = 0
        for weather_station in weather_stations:
            external_id = self.extract_external_station_id(weather_station.ext_id)

            data = self.load_weather_link_data(
                external_id) if external_id is not None else None
            daily_reading = self.aggregate_daily_reading(data)
            if (daily_reading is not None):
                self.push_daily_reading(
                    daily_reading, weather_station_id=weather_station.id)
                count+=1

        self.logger.info(f"Finished loading weather data. {count}/{len(weather_stations)} weather stations submitted")


