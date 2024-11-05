from daily_weather_link_loader import DailyWeatherLinkLoader
from typing import Any, List, Optional
from datetime import datetime, time, timedelta
from classes.models import ClimaticData, DailyReading, MeasureClimatic, WeatherLinkHistoricalData, WeatherLinkSensorReading, WeatherLinkStation, WeatherStation, WeatherStationDailyData
import requests
import os
import re

class HistoricalDailyData(DailyWeatherLinkLoader):
    
    def __init__(self):
        # Llama al constructor de la clase padre para inicializar los atributos
        super().__init__()
        self.WeatherLink_URL = "https://api.weatherlink.com/v2/"
        self.days_before = 2


    def extract_unauthorized_ids(self, message: str) -> List[int]:

        match = re.search(r'Access is not authorized for one or more stations: ([\d,]+)', message)
        if match:
            return list(map(int, match.group(1).split(',')))
        return []

    def get_weather_link_stations_info(self, station_ids: List[int]) -> List[WeatherLinkStation]:
        # Convertir el array de IDs a una cadena separada por comas
        ids_string = ",".join(map(str, station_ids))

        url = f'{self.WeatherLink_URL}stations/{ids_string}'
        
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
            stations = []
            for station in data["stations"]:

                stations.append(WeatherLinkStation.model_validate(station))
            
            return stations
        
        except requests.exceptions.HTTPError as e:

            # Verificar si el error es 403
            if response.status_code == 403:
                # Extraer los IDs no autorizados del mensaje de error
                unauthorized_ids = self.extract_unauthorized_ids(response.json().get("message", ""))
            
                self.logger.error(f"Access is not authorized for these stations: {unauthorized_ids}")

                # Filtrar los IDs no autorizados
                filtered_ids = [station_id for station_id in station_ids if station_id not in unauthorized_ids]

                # Realizar una nueva petición solo con los IDs autorizados
                if filtered_ids:

                    url = f'{self.WeatherLink_URL}stations/{filtered_ids}'
                    response = requests.get(url=url, headers=headers, params=params)
                    response.raise_for_status()

                    data = response.json()
                    stations = []
                    for station in data["stations"]:

                        stations.append(WeatherLinkStation.model_validate(station))
                    
                    return stations

            self.logger.error(f"Error loading WeatherLink stations: {str(e)}")
            return []

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error loading WeatherLink stations: {str(e)}")
            return []
        

    def load_weather_data_for_stations(self, stations: List[WeatherLinkStation]):

        all_historical_data = []

        for station in stations:
            registered_date = datetime.fromtimestamp(station.registered_date) if station.registered_date else None
            subscription_end_date = datetime.fromtimestamp(station.subscription_end_date) if station.subscription_end_date else self.today
            
            # Calcular la fecha límite para la carga de datos
            end_date = self.today - timedelta(days=self.days_before)
            
            # Determinar la fecha de inicio
            start_date = registered_date if registered_date and registered_date <= end_date else end_date
            
            # Iterar desde la fecha de inicio hasta la fecha de finalización (hasta dos días antes de hoy)
            current_date = start_date
            
            while current_date <= end_date:
                historical_data = self.load_weather_link_data(station.station_id, current_date)
                print(historical_data)
                current_date += timedelta(days=1)

            all_historical_data.append(historical_data)


    def main(self):

        weather_stations = self.get_weather_stations(external_prefix=self.COUNTRY_PREFIX)
        
        external_ids = [self.extract_external_station_id(weather_station.ext_id) for weather_station in weather_stations]

        weatherlink_data = self.get_weather_link_stations_info(external_ids)

        print(weatherlink_data)

        historical_data = self.load_weather_data_for_stations(weatherlink_data)
        



        
            
            

