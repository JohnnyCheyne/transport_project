
import os
import geopandas as gpd
import pandas as pd
import folium
import webbrowser
import cartopy.crs as ccrs

#LOAD DATA

    #method of travel csv, no geo
method = pd.read_csv('London_data/method.csv', skiprows=6)
    #boundary files
boroughs = gpd.read_file('London_data/London_Boroughs.gpkg')

#CLEAN DATA
method = method.drop(range(34,50))
method = method.rename(index=str, columns={'mnemonic':'gss_code'})
borough_method = boroughs.merge(method, on='gss_code')
borough_method = borough_method.drop(columns=['Area','sub_2011','hectares','nonld_area'])
borough_method['pt_uptake'] = borough_method['%.1']+borough_method['%.2']+borough_method['%.3']

#ALTER BROWSER HERE
web_browser = webbrowser.get('firefox')

def invisible_geo(feature):
    '''This dictionary can be passed any time we add a Folium feature
    that we do not want visualized on the shapefile

    Used in style_function parameter for Folium features'''
    return {
        'fillColor': 'transparent',
        'color': 'None',
        'weight': 1,
        'fillOpacity': 0}

def uptake_method():
    '''Projects an interactive map as an html file, which opens in browser.

    Args: borough_method (GeoDataFrame): merged 2021 census data (csv) with london borough shapefile (gpkg)

    Returns: folium map and transport statistics, and program menu, if True'''
    lm = borough_method.explore(column='pt_uptake',
                                cmap='viridis',
                                legend_kwds={'caption': 'Percentage Uptake of Public Transport'})

    columns_to_show = ['name', 'pt_uptake']
    popup = folium.features.GeoJsonPopup(fields=columns_to_show,
                                         aliases=['Borough', 'Percentage Uptake of Public Transport'],
                                         localize=True,
                                         labels=True,
                                         style='background-color: white;'
                                         )

    folium.GeoJson(data=borough_method, style_function=invisible_geo,
                   popup=popup).add_to(lm)
    if os.name == 'nt':
        path = path.replace('\\', '/')
        map1_html = 'map1.html'
        lm.save(map1_html)
        filepath = os.path.abspath('map1.html')
        filepath_url = 'file://' + filepath

        web_browser.open(filepath_url)
        return program()
    else:
        map1_html = 'map1.html'
        lm.save(map1_html)
        filepath = os.path.abspath('map1.html')
        filepath_url = 'file://' + filepath

        web_browser.open(filepath_url)
        return program()

def uptake_borough():

    '''Contains a dictionary to reflect ambiguous column titles in
    the borough_method dataset

    Requires user to input a mode of transport reflected in the dictionary.

    User can also input an exit command to call the original program menu.

    A correct input produces a chloropleth Folium map with a click-to-show pop-up
    describing the Borough and the percentage uptake of the chosen mode of transport
    in each borough

    Args: borough_method (GeoDataFrame): merged 2021 census data (csv) with london borough shapefile (gpkg)

    Returns: Folium map and transport statistics if True
            "Please enter a valid choice" and restarts function if False'''

    print('What method of transport uptake, as a percentage, would you like to see?')
    print('Options:\n Train\n Underground\n Bicycle\n Car\n Walking\n Bus')
    method = {'Train': '%.2',
              'Underground': '%.1',
              'Bicycle': '%.6',
              'Car': '%.5',
              'Walking': '%.7',
              'Bus': '%.3'}

    while True:
        print('type exit to exit')
        column_input = input('your choice here:')

        if column_input == 'exit':
            return program()
        if column_input in method:  # if input in dictionary: yes
            chosen_column = method[column_input]  # define chosen_column as input in dictionary

            m = borough_method.explore(column=chosen_column,  # map uses chosen column
                                       cmap='viridis',
                                       legend_kwds={'caption': f'Percentage uptake of {column_input}'})
            popup = folium.features.GeoJsonPopup(fields=['name', chosen_column],
                                                 aliases=['Borough', f'Uptake of {column_input}%'],
                                                 localize=True,
                                                 labels=True,
                                                 style='background-color: white;'
                                                 )
            folium.GeoJson(data=borough_method, style_function=invisible_geo,
                           popup=popup).add_to(m)
            highest_use = borough_method[chosen_column].idxmax() #identifies row with highest value
            highest_use_borough = borough_method.loc[highest_use]# identifies row
            pc_use = highest_use_borough[chosen_column]  # locates exact value for column_name
            print(f'{column_input} is most popular in {highest_use_borough["name"]}')
            print(f'{pc_use} percent of people use {column_input} in {highest_use_borough["name"]}')

            if os.name == 'nt':
                path = path.replace('\\', ' / ')
                map2_html = 'map2.html'
                m.save(map2_html)
                filepath = os.path.abspath('map2.html')
                filepath_url = 'file://' + filepath

                web_browser.open(filepath_url)
                return program()
            else:
                map2_html = 'map2.html'
                m.save(map2_html)
                filepath = os.path.abspath('map2.html')
                filepath_url = 'file://' + filepath

                web_browser.open(filepath_url)
                return program()

        else:
            print('Please enter a valid choice')
            uptake_borough()

def program():
    ''' Includes commands for two functions:

    user input "map" calls the uptake_method function
    user input "borough mode" calls the borough_method function

    Parameters: borough_method (GeoDataFrame)

    Both functions automatically open default web browser
    to display separate html files.

    uptake_borough() also returns borough_method statistics in
    the prompt'''
    print('')
    print('Would you like to see a map of public transport uptake in London Boroughs?')
    print('Enter "map" to see this.')
    print('')
    print('If you would like to see the popularity of particular modes of transport\n across London among commuters, enter "borough mode"')
    print('')
    print('Beware: data is from the 2021 census, which took place during covid')
    print('')
    print('Enter your choice below:')
    program_choice = input()

    if program_choice == 'map':
        print('Click on a borough for more information')
        uptake_method()

    elif program_choice == 'borough mode':
        uptake_borough()

    else:
        print('Please try again:')
        program()
        # improve the function by creating a dictionary inside to avoid using the alphanumeric titles.
program()


