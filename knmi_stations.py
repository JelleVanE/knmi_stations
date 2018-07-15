# Third-party modules
import math
import numpy as np
import pandas as pd
import geopandas as gpd
import re
import difflib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import zipfile
import os
from shapely.geometry import Point
from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup as bs

def get_soup(url):
    """Wrapper to get Beautiful Soup object for url in one line."""
    with urlopen(url) as f:
        return bs(f,'html.parser')

def degmin_to_decdeg(string):
    """Converts coordinates from degrees-minutes as found in the KNMI
    station coordinates table to decimal degrees. Returns a list if
    multiple coordinates are found in the supplied string (for
    instance, a longitude and a latitude)."""
    parsed = re.findall(r"\s*(\d{2})\s*(\d{2})\s*.?\s*",string)
    decdeg = [None for i in range(len(parsed))]
    for i in range(0,len(parsed)):
        """First element (index 0) of parsed[i] is the degrees,
        second element (index 1) is the minutes. The following
        formula computes the decimal degrees based on these numbers.
        """
        decdeg[i] = float(parsed[i][0]) + float(parsed[i][1])/60
    return decdeg

def coordtable():
    """Scrapes KNMI table of weather stations and their coordinates.
    Returns a data frame containing the contents of this table."""
    frame=pd.DataFrame(columns=["sid","name","type","lat","lon","elevation"])
    soup=get_soup('http://projects.knmi.nl/datacentrum/catalogus/catalogus/content/nl-obs-surf-stationslijst.htm')
    rowcontainer=soup.find("table",class_="MsoNormalTable")
    rows=rowcontainer.find_all('tr')
    for row in rows: # Each row corresponds to a station
        cells=row.find_all('td')
        if len(cells) == 6: # Distinguish data rows from table headers, footers
            cellstext=[]
            for cell in cells:
                strip=cell.text.strip()
                if strip=='':
                    strip=None
                cellstext.append(strip)
            frame.loc[len(frame)]=cellstext
    frame.drop(0, inplace=True) # Drop column names row
    for i in range(1,len(frame)+1):
        for var in ["lat","lon"]:
            # Convert degrees-minutes coordinates to decimal degrees
            frame.loc[i,var] = degmin_to_decdeg(frame.loc[i,var])[0]
    return frame

def mnth(x):
    """Converts Dutch month names to month numbers."""
    monthmap={'januari': 1,
            'februari': 2,
            'maart': 3,
            'april': 4,
            'mei': 5,
            'juni': 6,
            'juli': 7,
            'augustus': 8,
            'september': 9,
            'oktober': 10,
            'november': 11,
            'december': 12}
    return monthmap.get(x)

def table(verbose=False):
    """Scrapes KNMI table of weather measurements. Returns
    a data frame containing the contents of this table, as
    well as the coordinates obtained using the coordtable
    function."""
    frame=pd.DataFrame(columns=['t','sid','lat','lon','name','weather_type','temp','rel_humid','wind_dir','wind_speed','sight','atm_pressure'])
    soup=get_soup('http://www.knmi.nl/nederland-nu/weer/waarnemingen')
    # Get date and time of measurements
    datetime=re.findall(r'<h2>Waarnemingen (\d{1,2}) (\w+) (\d{4}) (\d{1,2}):(\d{2}) uur</h2>',str(soup))[0]
    datetime=str(datetime[2])+'-'+str(mnth(datetime[1]))+'-'+str(datetime[0])+' '+str(datetime[3])+':'+str(datetime[4])
    datetime=pd.to_datetime(datetime)
    # Scrape measurement table
    rowcontainer=soup.tbody
    rows=rowcontainer.find_all('tr')
    for row in rows:
        cells=row.find_all('td')
        """First column contains
        date and time of measurements, next three columns are placeholders for
        station id, latitude, longitude."""
        cellstext=[datetime]+[None for i in range(3)]
        for cell in cells:
            strip=cell.text.strip()
            if strip=='':
                strip=None
            cellstext.append(strip)
        frame.loc[len(frame)]=cellstext
    # Numeric columns are made to be considered as such by Python
    numeric_cols=['temp','rel_humid','sight','atm_pressure']
    frame[numeric_cols]=frame[numeric_cols].apply(pd.to_numeric)
    # Next, station coordinates will be added to frame.
    coords = coordtable()
    """The station names in the measurement and coordinates tables do not
    match up nicely. Before matching them, first the names of some stations
    that are very different should be corrected."""
    modify_names = {"Den Helder": "De Kooy", "Eelde": "Groningen"} # Dictionary of station name discrepancies
    for i in frame.index:
        name = frame.loc[i,"name"]
        for old, new in modify_names.items():
            if name == old:
                if verbose:
                    print("Setting alternative name \"" + new + "\" for measurement table station \"" + old + "\"")
                name = new
        """Now that the most glaring discrepancies have been corrected,
        we use a string similarity function to match stations."""
        maxsim = 0
        maxind = -1
        for j in coords.index:
            sim = difflib.SequenceMatcher(None, name, coords.loc[j,"name"]).ratio() #String similarity score
            if sim > maxsim:
                maxsim = sim
                maxind = j
        if verbose:
            print("Matching weather table station \"" + name + "\" and coordinate table station \"" + coords.loc[maxind,"name"] + "\"")
        frame.loc[i,["sid","lat","lon"]] = coords.loc[maxind,["sid","lat","lon"]]
    frame.set_index("sid", inplace=True)
    # Convert longitude and latitude to Geopandas geometry column.
    frame["coords"] = list(zip(frame.lon, frame.lat))
    frame["coords"] = frame["coords"].apply(Point)
    frame.drop(["lat","lon"], axis=1, inplace=True)
    frame = gpd.GeoDataFrame(frame, geometry="coords")
    frame.crs = {'init' :'epsg:4326'} # Decimal degrees are in the WGS84 coordinate system
    return frame

def dlshp():
    """Downloads shape file for the Netherlands."""
    f, h = urlretrieve("http://www.imergis.nl/shp/2018-Imergis_provinciegrenzen_kustlijn-shp.zip")
    z = zipfile.ZipFile(file = f, mode = 'r')
    z.extractall(path=os.getcwd()+"/shp")
    z.close()

def map(label=False,timestamp=False,dropifna=["temp"]):
    """Plots map of the Netherlands and locations of KNMI stations.
    Returns station data, Netherlands geometry data, figure and axis,
    so that they can be used later and/or plotted over.
    Arguments:
    - label: When set equal to a column name in the data frame returned
      by the table function, each station will be labeled by the
      contents of this column.
    - timestamp: If set to True, a timestamp for the KNMI data will be
      plotted.
    - dropifna: A list containing column names from the data frame
      returned by the table function. Any stations that have a null
      value in any of these columns will be dropped."""
    data=table()
    data.dropna(subset=dropifna, inplace=True)
    crs = ccrs.PlateCarree() #Plate carree map projection
    data = data.to_crs(crs.proj4_init) #Project station coordinates to plate carree
    fig, ax = plt.subplots(subplot_kw={'projection': crs})
    ax.set_extent([3,7.5,50.5,54])
    # Import Netherlands shapefile, also projected to plate carree
    netherlands = gpd.read_file("shp/2018-Imergis_provinciegrenzen_kustlijn.shp")
    netherlands.to_crs(crs.proj4_init, inplace=True)
    netherlands.plot(ax=ax, color="#FFBF80")
    data.plot(ax=ax, color="#FF6600", markersize=8, marker="D")
    # Label stations
    if label:
        for x, y, lbl in zip(data.geometry.x, data.geometry.y, data[label]):
            ax.annotate(lbl, xy=(x, y), xytext=(3, 3), textcoords="offset points")
    # Place timestamp
    if timestamp:
        ax.text(3.1,50.6,"Weather data: " + str(data.t.iloc[0]) + " - Source: KNMI")
    return data, netherlands, fig, ax

def distance(p, data):
    """Returns the distance of shapely point p from each station.
    table function output must be provided as argument data."""
    return data["coords"].apply(p.distance)

def idw(data, x, y, p, column="temp"):
    """Imputes values of variable supplied by argument "column"
    at Point (x,y) using inverse distance weighting. The parameter
    "p" is a parameter that determines how much weight is given
    to stations close to or far from (x,y): the higher "p" is, the
    more weight is given to closer stations."""
    dist = distance(Point(x,y), data)
    weights = (dist==0)
    if sum(weights)==0:
        weights = dist.apply(lambda x: 1/x**p)
    return sum(weights*data[column])/sum(weights)

def contour(impute_f=idw, p=4.5, column="temp", label="column"):
    """Makes a contour plot on the map supplied by function map.
    The "column" argument determines on which variable from the
    "table" function output the contours are based. The argument
    "label" can either be set to "column", in which case the
    stations are labeled with the value of that variable, or to
    "name", in which case stations are labeled by their name.
    The argument "impute_f" is the imputation function. The
    argument "p" is the inverse distance weighting parameter and
    is used in case the imputation function is set to idw."""
    if label == "column":
        lbl = column
    elif label == "name":
        lbl = "name"
    else:
        lbl = False
    data, netherlands, fig, ax = map(label=lbl, timestamp=True)
    # Supplies idw with the "p" argument in case impute_f is idw
    if impute_f==idw:
        def impute_f(data, x, y, column):
            return idw(data, x, y, p, column)
    # Vectors of all (x,y) coordinates on the Netherlands map.
    x = np.linspace(netherlands.geometry.bounds.minx.min(), netherlands.geometry.bounds.maxx.max(), 100)
    y = np.linspace(netherlands.geometry.bounds.miny.min(), netherlands.geometry.bounds.maxy.max(), 100)
    # Impute variable specified as "column" for each (x,y) coordinate
    z = np.array([[None for j in range(len(x))] for i in range(len(y))])
    for i in range(0,len(y)):
        for j in range(0,len(x)):
            z[i][j] = impute_f(data, x[j], y[i], column)
    ctr = ax.contourf(x,y,z,range(math.floor(z.min()),math.ceil(z.max())+1),alpha=0.35,cmap="coolwarm")
    legend = plt.colorbar(ctr)
    plt.show()
