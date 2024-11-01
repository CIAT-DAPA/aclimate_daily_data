import argparse

from daily_weather_link_loader import DailyWeatherLinkLoader

def main():

    parser = argparse.ArgumentParser(description="Resampling script")
    
    dd = DailyWeatherLinkLoader()
    dd.main()


if __name__ == "__main__":
    main()
