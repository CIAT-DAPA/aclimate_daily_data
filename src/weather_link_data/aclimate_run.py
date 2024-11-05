import argparse

from daily_weather_link_loader import DailyWeatherLinkLoader
from historical_weather_link import HistoricalDailyData

def main():

    parser = argparse.ArgumentParser(description="Resampling script")
    
    #dd = DailyWeatherLinkLoader()
    #dd.main()

    hd = HistoricalDailyData()
    hd.main()

    


if __name__ == "__main__":
    main()
