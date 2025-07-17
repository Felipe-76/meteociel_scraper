import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta, date
import numpy as np
import os


def validate_date(date_text):
    try:
        date.fromisoformat(date_text)
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def get_ranges_of_dates(start_date, end_date):
    """
    Input: start_date like ["yyyy-mm-dd"] string format
           end_date like ["yyyy-mm-dd"] string format
    Output: Array of strings with dates between start_date and end_date
    """
    try:
        validate_date(start_date)
    except ValueError:
        raise ValueError("Incorrect start_date format, should be YYYY-MM-DD")

    try:
        validate_date(end_date)
    except ValueError:
        raise ValueError("Incorrect end_date format, should be YYYY-MM-DD")

    start_annee = start_date[0:4]
    start_mois = start_date[5:7]
    start_jour = start_date[8:10]
    end_annee = end_date[0:4]
    end_mois = end_date[5:7]
    end_jour = end_date[8:10]

    # 1 more day in the end and in the beginning for Timezone corrections.
    start_dt = date(int(start_annee), int(start_mois), int(start_jour)) - timedelta(
        days=1
    )
    end_dt = date(int(end_annee), int(end_mois), int(end_jour)) + timedelta(days=1)

    delta = timedelta(days=1)

    # store the dates between two dates in a list
    dates = []

    while start_dt <= end_dt:
        # add current date to list by converting  it to iso format
        dates.append(start_dt.isoformat())
        # increment start date by timedelta
        start_dt += delta

    return dates


def get_info_from_url(url):
    station = url[url.find("code2=") + 6 : url.find("&jour2=")]
    jour = url[url.find("&jour2=") + 7 : url.find("&mois2=")]
    mois = url[url.find("&mois2=") + 7 : url.find("&annee2=")]
    annee = url[url.find("&annee2=") + 8 :]
    date = f"{annee}-{str(int(mois)+1).zfill(2)}-{(jour).zfill(2)}"
    return date, station


def get_meteociel_data(
    date="2023-01-01",
    meteostation="7157",
    url="",
    csv_export=False,
    filepath="files/meteo_tables/meteociel_scraping/",
):
    """
    Inputs:
        date: [yyyy-mm-dd] string format, optional.
        meteostation: number of station, integer or string format, optional.
        url: If given will ignore date and station, optional.
    Output:
        df with meteociel data for the given date and station.
    """
    # Building the url if it was not given
    if not url:
        # Validate the date input and build the url
        validate_date(date)
        annee = date[0:4]
        mois = date[5:7]
        jour = date[8:10]
        url = f"https://www.meteociel.fr/temps-reel/obs_villes.php?code2={meteostation}&jour2={jour}&mois2={int(mois)-1}&annee2={annee}"
        # print(url)
    else:
        date, meteostation = get_info_from_url(url)

    try:
        # Hosting request
        r = requests.get(url)

        # Parsing html
        soup = BeautifulSoup(r.text, "lxml")

        # Getting table element
        table = soup.find("table", bgcolor="#EBFAF7")

        # Header
        try:
            header = table.find("tr")
        except Exception as e:
            # Data not avaiable, returns empty dataframe.
            # Ex URL: set one avaiable to a future date.
            print(e)
            return pd.DataFrame({}), ""

        headers = [head.text for head in header.find_all("td")]

        # Vent (rafales) is a multicolumn, I will later separate its data into two columns if there is 2 data or into 1 column if there is only 1 data.
        vent_i = headers.index("Vent (rafales)")

        # Data from the rows
        rows_data = [
            [row_data.text for row_data in row.find_all("td")]
            for row in header.find_next_siblings()
        ]

        # If table is empty, only with headers
        if len(rows_data) == 0:
            # print("Empty Table", url)
            return pd.DataFrame({}), ""

        def find_numbers_in_string(input_string):
            if input_string == "":
                return np.nan
            else:
                pattern = r"-?\d+\.\d+|-?\d+"
                found_numbers = re.findall(pattern, input_string)
                numbers_as_string = "".join(found_numbers)

                return numbers_as_string

        # Getting wind direction data from the popover
        def get_wind_dir(wind_dir_popover):
            deg_i = wind_dir_popover.find("°")
            wind_dir_temp = wind_dir_popover[deg_i - 4 : deg_i + 2]
            wind_dir = find_numbers_in_string(wind_dir_temp)
            return wind_dir

        wind_dirs = []
        for row in header.find_next_siblings():
            try:
                wind_dir = get_wind_dir(
                    row.find_all("td")[vent_i].div.img.attrs["onmouseover"]
                )
                wind_dirs.append(float(wind_dir))
            except:
                # Some dates don't have the wind direction
                wind_dirs.append(np.nan)

        vent_row_0 = rows_data[0][vent_i + 1]
        if "(" in vent_row_0:
            # 2 data in the same field: Vent Moyen and rafales max, concatenated in the same header (multicolumn header)
            headers = (
                headers[0:vent_i]
                + ["Vent Moyen", "Rafales Max", "wind_direction_deg"]
                + headers[vent_i + 1 :]
            )
            #
            vent_moyens = [
                float(
                    find_numbers_in_string(
                        row_data[vent_i + 1][: row_data[vent_i + 1].find("(") - 2]
                    )
                    if row_data[vent_i + 1].find("/") != -1
                    else np.nan
                )
                # row_data[vent_i + 1][: row_data[vent_i + 1].find("(") - 2]
                for row_data in rows_data
            ]
            #
            rafales_max = [
                float(
                    find_numbers_in_string(
                        row_data[vent_i + 1][row_data[vent_i + 1].find("(") + 1 : -1]
                    )
                    if row_data[vent_i + 1].find("(") != -1
                    else np.nan
                )
                # row_data[vent_i + 1][row_data[vent_i + 1].find("(") + 1 : -1]
                for row_data in rows_data
            ]
            # vent_dir = header.find_next_siblings()[vent_i]

            for i in range(len(rows_data)):
                rows_data[i][vent_i] = vent_moyens[i]
                rows_data[i][vent_i + 1] = rafales_max[i]
                rows_data[i][vent_i] = vent_moyens[i]
                # Inserting the wind direction data in each row
                rows_data[i] = (
                    rows_data[i][: vent_i + 2]
                    + [wind_dirs[i]]
                    + rows_data[i][vent_i + 2 :]
                )

        else:
            # 1 data in the same field: Vent Moyen, concatenated in the same header (multicolumn header)
            headers = (
                headers[0:vent_i]
                + ["Vent Moyen", "wind_direction_deg"]
                + headers[vent_i + 1 :]
            )
            for i in range(len(rows_data)):
                try:
                    rows_data[i][vent_i] = float(
                        find_numbers_in_string((rows_data[i][vent_i + 1]))
                    )
                except:
                    rows_data[i][vent_i] = np.nan
                rows_data[i][vent_i + 1] = wind_dirs[i]

        df = pd.DataFrame(rows_data, columns=headers)

        # Drop unwanted rows
        if "Temps" in df.columns:
            df.drop("Temps", axis="columns", inplace=True)

        # Adjust time data to unique format with date
        date_format = "%Y-%m-%d %H:%M:%S"
        date_col = df.columns[0]
        df[date_col] = df[date_col].apply(
            lambda x: (
                datetime.strptime(
                    (date + " " + x.replace("h", ":").replace(" ", "") + ":00"),
                    date_format,
                )
                if x[-1] != "h"
                else datetime.strptime(
                    (date + " " + x.replace("h", ":00").replace(" ", "") + ":00"),
                    date_format,
                )
            )
        )

        # Adjusting df columns names
        df.rename(
            columns={
                date_col: "date",
                "Néb.": "nebulosity_octas",
                "Temps": "temps",
                "Visi": "visibility_km",
                "Température": "temp_degC",
                "Humi.": "humidity_%",
                "Point de rosée": "pt_rosee_degC",
                "Humidex": "humidex",
                "Windchill": "windchill",
                "Vent Moyen": "mean_wind_speed_km_h",
                "Rafales Max": "rafales_max_km_h",
                "Pression": "pression_hPa",
                "Précip. mm/h": "precipitation_mm",
                "Max rain rate": "max_rain_rate_mm_h",
            },
            inplace=True,
        )

        # Adjusting data values
        def get_precipitation(x):
            if "aucune" in x:
                return 0.0
            elif "m" in x:
                height = float(find_numbers_in_string(x[: x.find("m")]))
                try:
                    time = float(find_numbers_in_string(x[x.find("(") : x.find(")")]))
                except:
                    time = 1
                return height
                # Implementing rate == height/time is not consistent with some tables from meteociel
                return height / time
                # return round(height / time, 2)
            else:
                return np.nan

        try:
            df["nebulosity_octas"] = df["nebulosity_octas"].apply(
                lambda x: (
                    float(x[0 : x.find("/")])
                    if (
                        x != " "
                        and x != ""
                        and x != "\xa0"
                        and x != "\xa0 "
                        and x != "&nbsp"
                    )
                    else np.nan
                )
            )
        except:
            pass

        try:
            df["precipitation_mm"] = df["precipitation_mm"].apply(
                lambda x: get_precipitation(x)
            )
        except:
            pass

        problem_cols = []
        for col in df.columns:
            if col not in [
                "date",
                "nebulosity_octas",
                "precipitation_mm",
                "wind_direction_deg",
                "mean_wind_speed_km_h",
                "rafales_max_km_h",
            ]:
                try:
                    df[col] = df[col].apply(
                        lambda x: (
                            float(find_numbers_in_string(x))
                            if (
                                x != " "
                                and x != ""
                                and x != "\xa0"
                                and x != "\xa0 "
                                and x != "&nbsp"
                            )
                            else np.nan
                        )
                    )
                except Exception as e:
                    problem_cols.append((col, e))

        if problem_cols != []:
            print("*********************************************")
            print("url: ", url)
            print("problem_cols:", problem_cols)
            print("*********************************************")

        # Sorting date/hour in ascending
        df.sort_values("date", ascending=True, inplace=True)

        # Exporting to csv if desired
        if csv_export == True:
            try:
                filename = f"{meteostation}_{date}.csv"
                os.makedirs(filepath, exist_ok=True)
                df.to_csv(filepath + filename, index=False)
            except Exception as e:
                print("******")
                print("Error in the csv export path, see if atleast a df was returned.")
                print("current directory: ", os.getcwd())
                print(e)
                print("******")
            return df, filepath + filename
        else:
            return df, ""
    except Exception as e:
        print("******")
        print("Error in scraping ", url)
        print(e)
        print("******")
        return pd.DataFrame({}), ""


def get_historic_meteociel(
    start_date,
    end_date,
    meteostation,
    timezone="Europe/Paris",
    csv_export=False,
    filepath="files/meteo_tables/meteociel_scraping/",
):
    """
    Input: start_date: [yyyy-mm-dd] string format
           end_date: [yyyy-mm-dd] string format
           meteostation: string or integer with the number of the station
           timezone: timezone for the data (eg. "Europe/Paris"), to further convert to UTC.
    Output: df with data from meteociel ranging from start_date to end_date
    """

    if end_date < start_date:
        raise ValueError("end_date must be bigger or equal than start_date")

    dates = get_ranges_of_dates(start_date, end_date)
    ret_df = pd.DataFrame({})

    for date in dates:
        df, _ = get_meteociel_data(date, meteostation, csv_export=False)
        ret_df = pd.concat([ret_df, df], axis="rows")

    # Creating a "date_local" column
    ret_df["date_local"] = ret_df["date"]

    # Converting the "date" column to UTC
    ret_df["date"] = (
        pd.to_datetime(ret_df["date"])
        .dt.tz_localize(timezone, nonexistent="NaT", ambiguous="NaT")
        .dt.tz_convert(timezone)
    )

    # Dropping inexistent UTC dates (daytime transitions at last sunday in march and october for Paris)
    ret_df.dropna(subset=["date"], inplace=True, axis="index")
    ret_df["date"] = (
        ret_df["date"]
        .dt.tz_convert("UTC")
        .apply(lambda x: datetime.strftime(x, format="%Y-%m-%d %H:%M:%S"))
    )
    ret_df.rename(columns={"date": "date_UTC"}, inplace=True)

    # Selecting data only between the provided start_date and end_date (UTC)
    ret_df = ret_df[
        (ret_df["date_UTC"] >= start_date)
        & (
            ret_df["date_UTC"]
            < datetime.strftime(
                datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1),
                format="%Y-%m-%d",
            )
        )
    ]

    ret_df.reset_index(inplace=True, drop=True)

    if csv_export == True:
        try:
            filename = f"{meteostation}_{start_date}--{end_date}.csv"
            os.makedirs(filepath, exist_ok=True)
            ret_df.to_csv(filepath + filename, index=False)
        except Exception as e:
            print("******")
            print("Error in the csv export path, see if atleast a df was returned.")
            print("current directory: ", os.getcwd())
            print(e)
            print("******")

        return ret_df, filepath + filename

    else:
        return ret_df, ""


if __name__ == "__main__":
    # For the matlab the csv_export must be True and then the matlab reads the table from the path of the csv.
    url = "https://www.meteociel.fr/temps-reel/obs_villes.php?code2=7157&jour2=01&mois2=0&annee2=2023"
    try:
        if url:
            _, csv_path = get_meteociel_data(url=url, csv_export=True)
    except:
        _, csv_path = get_meteociel_data(
            date=mydate, meteostation=station, csv_export=True
        )
