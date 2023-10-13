from enum import Enum


from typing import List, Optional
from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, BeforeValidator,  Field


class WeatherLinkStation(BaseModel):
    station_name: str
    station_id: int
    latitude: float
    longitude: float

    class Config:
        extra = "allow"

        
class WeatherLinkSensorData(BaseModel):
    rainfall_mm: Optional[float]= None
    solar_rad_avg: Optional[float]= None
    temp_out: Optional[Annotated[float, BeforeValidator(lambda v: (v - 32) * 5.0/9.0)]]= None #convert fahrenheit to celsius
    hum_out: Optional[float]= None
    
    ts: int

    class Config:
        extra = "allow"

class WeatherLinkSensorReading(BaseModel):
    sensor_type: int
    data_structure_type: int
    data: List[WeatherLinkSensorData]

    class Config:
        extra = "allow"


class WeatherLinkHistoricalData(BaseModel):
    station_id: int
    generated_at: int
    sensors: List[WeatherLinkSensorReading]

    class Config:
        extra = "allow"


class WeatherStation(BaseModel):
    id: ObjectId = Field(..., alias='_id')
    name:str
    ext_id:str
    origin:str

   
    class Config:
        extra = "allow"
        arbitrary_types_allowed=True


class MeasureClimatic(str, Enum):
    PRECIPITATION = "prec"
    TEMP_MAX = "t_max"
    TEMP_MIN = "t_min"
    TEMP_AVG = "t_avg"
    HUMIDITY_MAX = "hum_max"
    HUMIDITY_MIN = "hum_min"
    HUMIDITY_AVG = "hum_avg"
    HUMIDITY_REL = "rel_hum"
    SOLAR_RADIATION = "sol_rad"
    PRECIPITATION_TER1 = "prec_ter_1"
    PRECIPITATION_TER2 = "prec_ter_2"



class ClimaticData(BaseModel):
    measure: MeasureClimatic 
    value: float | None


class DailyReading(BaseModel):
    day: int
    data: List[ClimaticData]

class WeatherStationDailyData(BaseModel):
    weather_station: ObjectId 
    month: int 
    year: int 
    daily_readings:List[DailyReading]
    
    class Config:
       arbitrary_types_allowed = True



    






