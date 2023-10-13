import argparse

from aclimate_daily_data.data_loader import DownloadDailyData

def main():

    parser = argparse.ArgumentParser(description="Resampling script")
    
    dd = DownloadDailyData()
    dd.main()


if __name__ == "__main__":
    main()
