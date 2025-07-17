import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np
import os


def get_info_from_prevision_url(url):
    prevision = url.split(".")[2].split("/")[1]
    code = url.split("/")[-2]
    ville = url.split(".")[-2].split("/")[-1]
    return code, ville, prevision


def find_numbers_in_string(input_string):
    if input_string == "":
        return np.nan
    else:
        pattern = r"-?\d+\.\d+|-?\d+"
        found_numbers = re.findall(pattern, input_string)
        numbers_as_string = "".join(found_numbers)

    return numbers_as_string


def get_date_from_prevision(arpege_soup):
    d = (
        arpege_soup.find("table", cellpadding=5)
        .find_next("table")
        .find_next("table")
        .find_next("table")
        .find("td")
        .text
    )

    date_pattern = (
        r"(\d{2} [A-Za-zûé]+ \d{4})"  # Matches the date format (ex: 08 novembre 2023)
    )

    date_match = re.search(date_pattern, d)
    date = date_match.group(1) if date_match else None

    # Define a dictionary to map month names in French to month numbers
    month_dict = {
        "janvier": "01",
        "février": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12",
    }

    # Split the input date into day, month, and year
    day, month, year = date.split()

    if len(day) == 1:
        day = f"0{day}"

    # Convert the month name to a month number
    month_number = month_dict.get(month.lower())

    # Format the date in yyyy-mm-dd
    formatted_date = f"{year}-{month_number}-{day}"

    return formatted_date


def get_prevision_data(
    code="",
    url="",
    timezone="Europe/Paris",
    csv_export=False,
    prevision="previsions-arpege-1h",
    filepath="files/meteo_tables/meteo_prev/",
):
    """
    Inputs:
        code: number of the local in meteociel, integer or string format, optional
            To find the code of your desired location go to the url of the predictions and insert the postal-code of the region in the box below the page.
        url: If given will ignore code, optional
        timezone: timezone for the data (eg. "Europe/Paris"), to further convert to UTC
        csv_export: To export the data in csv if set to True
        prevision is one the options from meteociel: ["previsions","previsions-wrf","previsions-wrf-1h","previsions-arome","previsions-arome-1h","previsions-arpege-1h","previsions-iconeu","previsions-icond2"]
    Output:
        df with prediction meteo data for the given station
    """

    # Building the url if it was not given
    if not url:
        previsions_list = [
            "previsions",
            "previsions-wrf",
            "previsions-wrf-1h",
            "previsions-arome",
            "previsions-arome-1h",
            "previsions-arpege-1h",
            "previsions-iconeu",
            "previsions-icond2",
        ]

        if prevision not in previsions_list:
            raise ValueError(f"Prevision must be one of {previsions_list}")

        # Validate the date input and build the url
        url = f"https://www.meteociel.fr/{prevision}/{code}/neimportepaslaville.htm"
        # print(url)

        if not code:
            raise KeyError(
                "Give the desired station code (found in the URL) for the prevision"
            )

    else:
        code, ville, prevision = get_info_from_prevision_url(url)

    try:
        # Hosting request
        r = requests.get(url)

        # Parsing html
        soup = BeautifulSoup(r.text, "lxml")

        try:
            start_date = get_date_from_prevision(soup)
        except:
            print(url)
            raise ValueError(
                "Date not accessible from the page or date scraping error (see function get_date)."
            )

        # Getting table element
        tables = soup.find("table", cellpadding=5)

        # Separating Header and data rows
        try:
            table = tables.find("table")
            rows = table.find_all("tr")
            header_color = rows[0]["bgcolor"]
            headers = table.find_all_next(bgcolor=header_color)
            n_header_rows = len(headers)
            data_rows = rows[n_header_rows:]

            # Supports header of 2 rows max.
            colspans = [int(col.get("colspan", 1)) for col in headers[0].find_all("td")]
            columns = [col.text for col in headers[0].find_all("td")]
            columns_2 = [col.text for col in headers[1].find_all("td")]

            # Building the header columns
            try:
                n_headers_prev = sum(colspans)
                header = []
                j = 0

                for i in range(len(columns)):
                    if colspans[i] != 1:
                        for _ in range(colspans[i]):
                            header.append(columns[i] + " " + columns_2[j])
                            j += 1
                    else:
                        header.append(columns[i])
                n_headers = len(header)
            except:
                print("Couldn't properly build header")
                if n_headers != n_headers_prev:
                    print("Inconsistency in the length of Multiheaders")

            if n_headers != n_headers_prev:
                print("Inconsistency in the length of Multiheaders")

        except Exception as e:
            # Data not avaiable, returns empty dataframe.
            print(e)
            return pd.DataFrame({}), ""

        table_data = {head: [] for head in header}

        # Getting data
        jour_hours = []
        jours = []
        imgs = []
        n_hours = ""
        for data_row in data_rows:
            # Appending Temps img
            try:
                imgs.append(data_row.find_all("img")[-1].get("src").split("/")[-1])
            except:
                imgs.append(np.nan)

            # Appending the rest of the data
            data = data_row.find_all("td")
            if len(data) == 11:
                start = 1
                if n_hours:
                    jour_hours.append(n_hours)
                n_hours = 0
                jour = data[0].text
                jours.append(jour)
                n_hours += 1
            else:
                start = 0
                n_hours += 1
            for i in range(start, len(data)):
                if data[i].text != "":
                    table_data[header[i - start + 1]].append(data[i].text)
                else:
                    table_data[header[i - start + 1]].append(data[i].img["alt"])

        jour_hours.append(n_hours)

        for k in range(len(jours)):
            table_data[header[0]].extend([jours[k]] * jour_hours[k])

        df = pd.DataFrame(table_data)

        df.rename(
            columns={
                header[2]: "temp_degC",
                header[3]: "windchill",
                header[4]: "wind_direction_deg",
                header[5]: "mean_wind_speed_km_h",
                header[6]: "rafales_max_km_h",
                header[7]: "precipitation_mm",
                header[8]: "humidity_%",
                header[9]: "pression_hPa",
                header[10]: "temps",
            },
            inplace=True,
        )

        df["temps_img"] = imgs

        df["precipitation_mm"] = df["precipitation_mm"].apply(
            lambda x: float(find_numbers_in_string(x)) if x != "--" else 0.0
        )

        get_numbers_cols = [
            "temp_degC",
            "humidity_%",
            "pression_hPa",
            "wind_direction_deg",
            "rafales_max_km_h",
            "mean_wind_speed_km_h",
            "windchill",
        ]
        problem_cols = []
        for col in get_numbers_cols:
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
            print("url: ", url)
            print(problem_cols)

        # Adjust nebulosity_octas from nebulosity_octas_prev (used previous one)
        def get_neb_from_img(img):
            if "Averses de pluie faibles" in img:
                return 7.0
            if "soleil.gif" in img:
                return 0.0
            if "voile.png" in img:
                return 2.0
            if "peu_nuageu" in img:
                return 3.0
            if "mitige.gif" in img:
                return 4.0
            if "pluie.gif" in img:
                return 7.0
            if "grele.gif" in img:
                return 7.0
            if "neige.gif" in img:
                return 8.0
            if "oragefaibl" in img:
                return 7.0
            if "brouillard" in img:
                return 8.0
            if "pluie_neig" in img:
                return 8.0
            if "nuageux.gi" in img:
                return 8.0
            else:
                return np.nan

        df["nebulosity_octas"] = df["temps_img"].apply(lambda x: get_neb_from_img(x))

        def get_nth_day_next_month(ref_date, n):
            # Convert the input string to a datetime object
            input_date = datetime.strptime(ref_date, "%Y-%m-%d")

            # Calculate the nth day of the next month
            nth_day_of_next_month = (
                input_date.replace(day=1) + timedelta(days=32)
            ).replace(day=n)

            # Convert the result back to the desired format
            result_date_str = nth_day_of_next_month.strftime("%Y-%m-%d")
            return result_date_str

        def get_nth_day_prev_month(ref_date, n):
            # Convert the input string to a datetime object
            input_date = datetime.strptime(ref_date, "%Y-%m-%d")

            # Calculate the nth day of the prev month
            nth_day_of_prev_month = (
                input_date.replace(day=1) - timedelta(days=2)
            ).replace(day=n)

            # Convert the result back to the desired format
            result_date_str = nth_day_of_prev_month.strftime("%Y-%m-%d")
            return result_date_str

        def get_table_date(x, ref_date):
            # OBS: Sometimes the date in the table in the right is not the date in the first row of the data table.
            # The if-else clause below solves this issue and the issue when there`s month transitions`.
            ref_datetime = datetime.strptime(ref_date, "%Y-%m-%d")
            ref_day = ref_datetime.day
            if int(x) < ref_day:
                dates = [
                    datetime.strftime(ref_datetime.replace(day=int(x)), "%Y-%m-%d"),
                    get_nth_day_next_month(ref_date, int(x)),
                ]
                # Get closest date
                return min(
                    dates,
                    key=lambda date: abs(
                        ref_datetime - datetime.strptime(date, "%Y-%m-%d")
                    ),
                )
            else:
                dates = [
                    datetime.strftime(ref_datetime.replace(day=int(x)), "%Y-%m-%d"),
                    get_nth_day_prev_month(ref_date, int(x)),
                ]
                # Get closest date
                return min(
                    dates,
                    key=lambda date: abs(
                        ref_datetime - datetime.strptime(date, "%Y-%m-%d")
                    ),
                )

        df["Jour"] = df["Jour"].apply(
            lambda x: get_table_date(find_numbers_in_string(x), start_date)
        )

        # Converting date column to date-time column.
        df["date"] = df["Jour"] + " " + df["Heure"] + ":00"
        df.drop(["Jour", "Heure"], axis="columns", inplace=True)

        df = df[
            [
                "date",  #
                "temp_degC",  #
                "windchill",
                "wind_direction_deg",  #
                "mean_wind_speed_km_h",  #
                "rafales_max_km_h",
                "precipitation_mm",  #
                "humidity_%",  #
                "pression_hPa",  #
                "temps",
                "temps_img",
                "nebulosity_octas",  #
                # visibility_km (marked the ones necessary for the meteo.txt TELEMAC)
            ]
        ]

        # Creating a "date_local" column
        df["date_local"] = df["date"]

        # Converting the "date" column to UTC
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(timezone)
        df["date"] = (
            df["date"]
            .dt.tz_convert("UTC")
            .apply(lambda x: datetime.strftime(x, format="%Y-%m-%d %H:%M:%S"))
        )
        df.rename(columns={"date": "date_UTC"}, inplace=True)

        if csv_export == True:
            filename = f"{code}_{prevision}_{df['date_UTC'].iloc[0].replace(' ', '_')[0:13]}h.csv"
            os.makedirs(filepath, exist_ok=True)
            try:
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


if __name__ == "__main__":
    code = "32104"  # Example code for location
    prevision = "previsions-arpege-1h"
    # url = "https://www.meteociel.fr/previsions-arpege-1h/32104/neimportepaslaville.htm"

    try:
        if url:
            _, csv_path = get_prevision_data(url=url, csv_export=True)
    except:
        _, csv_path = get_prevision_data(
            code=code, prevision=prevision, csv_export=True
        )
