#!/usr/bin/env python
# coding: utf-8

import ee
import datetime
import pandas as pd
from IPython.display import Image
import numpy

def my_fun(arg):
  return arg

def ee_array_to_df(arr, list_of_bands):
    """Transforms client-side ee.Image.getRegion array to pandas.DataFrame."""
    df = pd.DataFrame(arr)

    # Rearrange the header.
    headers = df.iloc[0]
    df = pd.DataFrame(df.values[1:], columns=headers)

    # Remove rows without data inside.
    df = df[['longitude', 'latitude', 'time', *list_of_bands]].dropna()

    # Convert the data to numeric values.
    for band in list_of_bands:
        df[band] = pd.to_numeric(df[band], errors='coerce')

    # Convert the time field into a datetime.
    df['datetime'] = pd.to_datetime(df['time'], unit='ms')

    # Keep the columns of interest.
    df = df[['time','datetime',  *list_of_bands]]

    return df

def main():
    ee.Authenticate()
    ee.Initialize()


    print(ee.Image("NASA/NASADEM_HGT/001").get("title").getInfo())

    ee_date = ee.Date('2020-01-01')

    py_date = datetime.datetime.utcfromtimestamp(ee_date.getInfo()['value']/1000.0)
    print (py_date)

    py_date = datetime.datetime.utcnow()
    print (py_date)

    ee_date = ee.Date(py_date)
    print (ee_date)

    print(ee.Image("NASA/NASADEM_HGT/001").get("title").getInfo())

    lc = ee.ImageCollection('MODIS/006/MCD12Q1')

    lst = ee.ImageCollection('MODIS/006/MOD11A1')

    elv = ee.Image('USGS/SRTMGL1_003')

    i_date = '2017-01-01'

    # Final date of interest (exclusive).
    f_date = '2020-01-01'

    lst = lst.select('LST_Day_1km', 'QC_Day').filterDate(i_date, f_date)


    # Define the urban location of interest as a point near Lyon, France.
    u_lon = 4.8148
    u_lat = 45.7758
    u_poi = ee.Geometry.Point(u_lon, u_lat)


    # Define the rural location of interest as a point away from the city.
    r_lon = 5.175964
    r_lat = 45.574064
    r_poi = ee.Geometry.Point(r_lon, r_lat)

    scale = 1000  # scale in meters

    # Print the elevation near Lyon, France.
    elv_urban_point = elv.sample(u_poi, scale).first().get('elevation').getInfo()

    print('Ground elevation at urban point:', elv_urban_point, 'm')


    # Calculate and print the mean value of the LST collection at the point.
    lst_urban_point = lst.mean().sample(u_poi, scale).first().get('LST_Day_1km').getInfo()
    print('Average daytime LST at urban point:', round(lst_urban_point*0.02 -273.15, 2), '°C')

    # Print the land cover type at the point.
    lc_urban_point = lc.first().sample(u_poi, scale).first().get('LC_Type1').getInfo()

    print('Land cover value at urban point is:', lc_urban_point)

    #Get a time series


    # to inspect a time series, probably make some charts and calculate statistics about a place. Hence, we import the data at the given locations using the getRegion() method.


    # Get the data for the pixel intersecting the point in urban area.
    lst_u_poi = lst.getRegion(u_poi, scale).getInfo()
    print (lst_u_poi)

    # Get the data for the pixel intersecting the point in rural area.
    lst_r_poi = lst.getRegion(r_poi, scale).getInfo()
    print (lst_r_poi)

    # Preview the result.
    print (lst_u_poi[:5])

    lst_df_urban = ee_array_to_df(lst_u_poi,['LST_Day_1km'])
    print (lst_df_urban)

    lst_df_urban = ee_array_to_df(lst_u_poi,['LST_Day_1km'])
    print (lst_df_urban)

    def t_modis_to_celsius(t_modis):
        """Converts MODIS LST units to degrees Celsius."""
        t_celsius =  0.02*t_modis - 273.15
        return t_celsius

    # Apply the function to get temperature in celsius.
    lst_df_urban['LST_Day_1km'] = lst_df_urban['LST_Day_1km'].apply(t_modis_to_celsius)
    print (lst_df_urban)

    # Do the same for the rural point.
    lst_df_rural = ee_array_to_df(lst_r_poi,['LST_Day_1km'])
    lst_df_rural['LST_Day_1km'] = lst_df_rural['LST_Day_1km'].apply(t_modis_to_celsius)

    print (lst_df_urban.head())


    # get static maps of land surface temperature and ground elevation around a region of interest. 

    # Define a region of interest with a buffer zone of 1000 km around Lyon.
    roi = u_poi.buffer(1e6)
    print (roi)

    # Reduce the LST collection by mean.
    lst_img = lst.mean()

    # Adjust for scale factor.
    lst_img = lst_img.select('LST_Day_1km').multiply(0.02)

    # Convert Kelvin to Celsius.
    lst_img = lst_img.select('LST_Day_1km').add(-273.15)

    print (lst_img,lst_img,lst_img)


    # Create a URL to the styled image for a region around France.
    url = lst_img.getThumbUrl({
        'min': 10, 'max': 30, 'dimensions': 512, 'region': roi,
        'palette': ['blue', 'yellow', 'orange', 'red']})
    print(url)

    # Display the thumbnail land surface temperature in France.
    print('\nPlease wait while the thumbnail loads, it may take a moment...')
    Image(url=url)


    # Clip an image by a region of interest

    elv_img = elv.updateMask(elv.gt(0))

    # Get a feature collection of administrative boundaries.
    countries = ee.FeatureCollection('FAO/GAUL/2015/level0').select('ADM0_NAME')

    # Filter the feature collection to subset France.
    france = countries.filter(ee.Filter.eq('ADM0_NAME', 'France'))

    # Clip the image by France.
    elv_fr = elv_img.clip(france)

    # Create the URL associated with the styled image data.
    url = elv_fr.getThumbUrl({
        'min': 0, 'max': 2500, 'region': roi, 'dimensions': 512,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']})

    # Display a thumbnail of elevation in France.
    Image(url=url)

    # Create a buffer zone of 10 km around Lyon.
    lyon = u_poi.buffer(10000)  # meters

    url = elv_img.getThumbUrl({
        'min': 150, 'max': 350, 'region': lyon, 'dimensions': 512,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']})
    Image(url=url)


    # Save a GeoTIFF file in your Google Drive

    task = ee.batch.Export.image.toDrive(image=elv_img,
                                        description='elevation_near_lyon_france',
                                        scale=30,
                                        region=lyon,
                                        fileNamePrefix='my_export_lyon',
                                        crs='EPSG:4326',
                                        fileFormat='GeoTIFF')
    task.start()

    task.status()


    # Get a link to download your GeoTIFF

    link = lst_img.getDownloadURL({
        'scale': 30,
        'crs': 'EPSG:4326',
        'fileFormat': 'GeoTIFF',
        'region': lyon})
    print(link)
    
main()

