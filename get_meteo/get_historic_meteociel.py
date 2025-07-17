from get_meteo.get_meteo_data import get_historic_meteociel

if __name__ == "__main__":
    start_date = "2019-01-01"
    end_date = "2019-01-02"
    station = "7157"
    filepath = "/"
    _, csv_path = get_historic_meteociel(
        start_date, end_date, station, csv_export=True, filepath=filepath
    )
