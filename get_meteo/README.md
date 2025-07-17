This folder consists of 2 scripts:

# 1. get_meteo_data.py

Has 2 principal functions:

+ get_meteociel_data(date, station, url, csv_export=False):

    Inputs:

        date: [yyyy-mm-dd] string format, optional
        station: number of station, integer or string format, optional
        url: If given will ignore date and station, optional
        csv_export: True or False, optional

    Output:

        df with meteociel data for the given date and station
        path with the filepath of the csv_export if set to True or "" if set to False

    Example use:

        df, path = get_meteociel_data(date="2023-01-01", station="7157", csv_export=False)
        
    Or:

        df, path = get_meteociel_data(url="https://www.meteociel.fr/temps-reel/obs_villes.php?code2=7157&jour2=1&mois2=1&annee2=2021", csv_export=True)

+ def get_historic_meteociel(start_date, end_date, station, csv_export=False):

    Inputs:

        start_date: [yyyy-mm-dd] string format
        end_date: [yyyy-mm-dd] string format
        station: station: string or integer with the number of the station

    Outputs:

        df with data from meteociel ranging from start_date to end_date
        path with the filepath of the csv_export if set to True or "" if set to False

    Example use:

        station = "7157"
        start_date = "2023-01-01"
        end_date = "2023-01-02"
        df, path = get_historic_meteociel(
            start_date=start_date, end_date=end_date, station=station, csv_export=True
        )

# 2. arpege_scraping.py

    Gets the prevision for the next 3 days in the meteociel site.

    Has one main function:

+ get_arpege_data(code, url, csv_export=False):

    Inputs:

        code: int or string format.
        url: optional, url of the prevision for the scraping, will ignore code if given.
        csv_export: True or False

    Outputs:

        df with 3 days prediction meteo data for the given station
        path with the filepath of the csv_export if set to True or "" if set to False

    Example use:

        from arpege_scraping import get_arpege_data
        df, path = get_arpege_data(
            url="https://www.meteociel.fr/previsions/33262/champigny_sur_marne.htm",
            csv_export=True,
        )
        df

    It has the following different models with example links to test:

    "prev_classique": "https://www.meteociel.fr/previsions-arpege-1h/32104/fontenay.htm"

    "plus_fines": "https://www.meteociel.fr/previsions-wrf/32104/fontenay.htm"

    "plus_fines_h_h": "https://www.meteociel.fr/previsions-wrf-1h/32104/fontenay.htm"

    "arome": "https://www.meteociel.fr/previsions-arome/32104/fontenay.htm"

    "arom_h_h": "https://www.meteociel.fr/previsions-arome-1h/32104/fontenay.htm"

    "arpege": "https://www.meteociel.fr/previsions-arpege-1h/32104/fontenay.htm"

    "icon_eu": "https://www.meteociel.fr/previsions-iconeu/32104/fontenay.htm"
    
    "icon_d2": "https://www.meteociel.fr/previsions-icond2/32104/fontenay.htm"

    Altough in the url there is a ville and a code you only need the code to get the correct data from the site, the ville can be anything.

    To find the code for your desired location you need to go to these urls and insert in the box below the page the postal-code or the name of the ville you want.
        
    

## Important notes

+ Keep in mind that to utilize these functions you need to import them in your notebook.
+ All the result files are being wrote in felipe_toolbox/files/meteo_tables.