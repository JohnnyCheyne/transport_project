
import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from cartopy.feature import ShapelyFeature
import cartopy.crs as ccrs
plt.ion() # make the plotting interactive

#LOAD DATA

res_route = gpd.read_file('London_data/restricted_route.json')
cycle = gpd.read_file('London_data/cycle_lane_track.json')  #2017/18 cycle routes
london = gpd.read_file('London_data/London_Boroughs.gpkg')
method_new = pd.read_csv('London_data/method.csv', skiprows=6)
method_old = pd.read_csv('London_data/method.csv.csv', skiprows=6)
cycle_t = cycle.drop(columns=['CLT_CARR',
                              'CLT_SHARED',
                              'CLT_ADVIS',
                              'CLT_PRIORI',
                              'CLT_BBYPAS',
                              'CLT_PARKR',
                              'CLT_WATERR',
                              'CLT_PTIME',
                              'CLT_ACCESS',
                              'CLT_COLOUR',
                              'PHOTO1_URL',
                              'PHOTO2_URL'])
cycle_t = cycle_t[(cycle_t == 'TRUE').any(axis=1)]
uni_crs=ccrs.OSGB()
#def cycle_handles(labels, colors, edge='k', alpha=1)
#create a function to rank boroughs for their

def borough_transit_rank(cycle_t, cycle, london):

    '''Function generates a Cartopy figure for a selected London Borough.
    Args: cycle: linewidth GeoDataFrame of lanes in Greater London
        cycle_t (cycle): dedicated cycle lane track dataframe
        london (london): Greater London borough dataframe

    Returns: - total possible dedicated lane (length) travellable in chosen borough
        - Cartopy plot of chosen London borough with dedicated and non-dedicated cycle tracks
        - A borough ranking for its "true" cycle lane accomodation (2017 data)'''

    print(f'Options:\n{london['name'].to_string(index=False)}')
    print('Select a borough, or enter "exit" to return to menu')
    user_borough = input()

    if user_borough in london['name'].values:


        sample_mask = london.loc[london['name'] == user_borough, 'geometry'].iloc[0]# identifies polygon, not table
        # add a 1m buffer for nearby cycle tracks
        cycle_t = cycle_t.to_crs(uni_crs)
        cycle_buffer = cycle_t.buffer(1)
        clipped_cycle = cycle_buffer.intersection(sample_mask)
        total_length = clipped_cycle.length.sum()
        lengthS = clipped_cycle.length.unique()
        cycleable_length = lengthS.max()

        print(f'You can travel {cycleable_length / 1000:.2f}km without leaving cycle lanes in {user_borough}')
        print('')
        # recreate sample mask for map purposes
        plot_crs = ccrs.PlateCarree()
        london_plot = london.to_crs(plot_crs)
        fig1, ax1 = plt.subplots(figsize=(10, 10), subplot_kw={'projection': plot_crs})


        # need to recreate geometry for single polygon
        sample_mask_geom = london_plot.loc[london_plot['name'] == user_borough, 'geometry'].iloc[0]
        sample_mask_outline = ShapelyFeature(sample_mask_geom, crs=plot_crs, edgecolor='k', facecolor='none',
                                             zorder=3, linewidth=2)
        ax1.add_feature(sample_mask_outline)

        cycle = cycle.to_crs(plot_crs)


        cycle_t_plot = cycle_t.to_crs(plot_crs)
        cycle_t_clip = cycle_t_plot.clip(sample_mask_geom)

        #to fix offset lines
        bor_cycle = cycle['geometry'].clip(sample_mask_geom)
        bor_cycle = bor_cycle.to_crs(cycle_t_clip.crs)
        bor_cycle= bor_cycle.geometry.translate(xoff=0.0015, yoff=-0.0006)
        bor_cycle.plot(ax=ax1, linewidth=2, zorder=3, color='orange', alpha=0.8, label=f'cycleable lanes: {len(bor_cycle)}')
        #re-draw dedicated cycle lanes

        cycle_t_clip.plot(ax=ax1, linewidth=2, zorder=4, color='darkgreen', label=f'dedicated cycle lanes: {len(cycle_t_clip)}')
        ax1.legend(loc='lower right')
        # ax1.set_extent gets confused by the large function, so place the crs call right before plot.show
        #use TOTAL_BOUNDS, not just BOUNDS
        b = bor_cycle.total_bounds
        pady = (b[3]-b[1])*0.10
        padx = (b[2]-b[0])*0.10
        ax1.set_extent([b[0]-padx, b[2]+padx, b[1]-pady, b[3]+pady], crs=plot_crs)

        ax1.set_title(f'{user_borough}')

        print(f'lanes with accomodation for bicycles: {len(bor_cycle)}')
        print(f'dedicated cycle lanes: {len(cycle_t_clip)}')
        print('')
        print('Loading map and ranking...')
        ''' returns a ranking for dedicated cycle lanes'''
        ''' need to add a new function to calculate clipped lengths for each borough, row by row'''
        def london_rank():
            cycle_alt = cycle_t.to_crs(plot_crs) #new cycle_t dataset
            bor_alt = cycle.to_crs(plot_crs)    #new cycle dataset
            london_alt = london.to_crs(plot_crs) #new london dataset
            def mask(row):
                cycle_alt_mask = cycle_alt.clip(row['geometry'])
                bor_alt_mask = bor_alt.clip(row['geometry'])#create mask for each geometry

                cycle_alt_len = len(cycle_alt_mask)
                bor_alt_len = len(bor_alt_mask)

                return pd.Series([cycle_alt_len, bor_alt_len])

            london_alt [['dedicated', 'cycleable']] = london_alt.apply(mask, axis=1) #length of cycle_alt clipped to mask  #length of bor_alt clipped to mask
            london_alt ['pc'] = london_alt['dedicated']/london_alt['cycleable']*100
            london_alt['ranking'] = london_alt['pc'].rank(ascending=False, method='min')
                #add column 'ranking' where it calculates a string of 'rank' labels for each possible borough
            rank = london_alt.loc[london_alt['name'] == user_borough, 'ranking'].values[0]
                #create a final object, the exact rank for a given borough
            return rank


        print(f'In London, {user_borough} is rank {london_rank():.0f} for its dedicated lanes')
        print('')
        plt.show()
        return borough_transit_rank(cycle_t, cycle, london)

    elif user_borough == 'exit':
        print('')
        print('')
        program()

    else:
        print('that is not a borough')
        borough_transit_rank(cycle_t, cycle, london)


def cycle_change(method_old, london, cycle_t):

    ''' Function returns a chloropleth map of Greater London. It
    depicts the change in bicycle usage by commuters between 2011
     and 2021, as well as the dedicated cycle lanes as of 2017.

     Args: travel_map (gdf): commuter data for 2011 and 2021
     cycle_t (gdf): dedicated cycle lane linestrings for Greater London
     london (gdf): shapefile for borough outlines

     Returns: Greater London cycle lane map with markers, borough labels
     and legend'''

    method_old['bike%2011'] = method_old['Bicycle'] / method_old[
        'All categories: Method of travel to work (2001 specification)'] * 100
    method_new['bike_pc'] = method_new['Bicycle'] / method_new[
        'Total: All usual residents aged 16 years and over in employment the week before the census'] * 100
    method_old['bike_2021'] = method_new['bike_pc']
    method_old['bike_change'] = method_old['bike_2021'] - method_old['bike%2011']
    method_old['bike_pc'] = method_old['bike_change'] / method_old['bike%2011'] * 100
    method_old = method_old.drop(range(34, 37))
    method_old = method_old.drop(37)

    travel_map = method_old.merge(london, left_on='mnemonic', right_on='gss_code', how='right')
    travel_map = gpd.GeoDataFrame(travel_map, geometry='geometry', crs=uni_crs)
    travel_map = travel_map.to_crs(uni_crs)
    # set up chloropleth style map
    travel_map['coords'] = travel_map.geometry.centroid
    fig, ax = plt.subplots(figsize=(19, 10), subplot_kw={'projection': uni_crs})

    travel_map.plot(column='bike_pc',
                    ax=ax,
                    transform=uni_crs,
                    cmap='viridis',
                    legend=True,
                    legend_kwds={'label': 'Change in Bike Usage', 'orientation': 'vertical'},
                    aspect='equal')


    travel_map.set_geometry('coords').plot(marker='^', color='lightblue', markersize=22, alpha=0.8, zorder=2, ax=ax)
    # this takes a white to process. create a new column for the marker at the top of the code

    # can add names for each borough to the map
    london = london.to_crs(uni_crs)

    text_centroids = london.centroid.translate(xoff=200, yoff=500)
    # use london dataset as the names are nicer
    for idx, row in london.iterrows():
        point = text_centroids[idx]
        ax.annotate(text=row['name'],
                    xy=(point.x, point.y),
                    horizontalalignment='right',
                    fontsize=6.5,
                    color='k',
                    zorder=3)

    # it is hard to distinguish the marker from the name label. change this by using
    # translate() function in the above function

    # add cycle lanes
    cycle = cycle_t.to_crs(uni_crs)
    cycle.plot(ax=ax, linewidth=1, zorder=4, color='gray')
    print('Loading map...')
    print('')
    print('')
    plt.show()
    program()

def program():

    '''Menu with input commands for Greater London (cycle_change())
     and borough (borough_transit_rank())functions.'''
    print('Choose either "london" for an overview of London cycle tracks over the last decade and a half,'
          '\n or choose "borough" for a closer look at a specific borough')
    print('')
    print('Cycle lane data is from 2017')
    print('Your choice below:')
    choice = input()
    if choice == 'borough':
        borough_transit_rank(cycle_t, cycle, london)
    elif choice == 'london':
        cycle_change(method_old, london, cycle_t)
    else:
        ValueError
program()