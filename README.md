# Netherlands temperature map
Provides a contour map of temperatures in the Netherlands using scraped weather data from and coordinates of KNMI weather measurement stations. An attempt to replicate KNMI's own https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/temperatuur.png.

Temperatures are interpolated using inverse distance weighting (IDW). To do: more advanced interpolation techniques (e.g. Kriging).

A Jupyter Notebook demonstrating the module can be found [here](example.ipynb).

My motivation for this project was to improve my Python skills in scraping, data visualization and working with geospatial data.
## Dependencies
* numpy
* pandas
* geopandas
* matplotlib
* cartopy
* shapely
* bs4
## References
* **KNMI measurement station coordinates**: KNMI, scraped from http://projects.knmi.nl/datacentrum/catalogus/catalogus/content/nl-obs-surf-stationslijst.htm
* **KNMI weather data**: KNMI, scraped from https://knmi.nl/nederland-nu/weer/waarnemingen
* **Netherlands map**: BRK, CC-BY Kadaster. "Provinciegrenzen 2018 exact, op kustlijn", accessed online at http://www.imergis.nl/asp/47.asp
The Creative Commons Zero license applies to the contents of the KNMI website. Therefore, I am obligated to mention that KNMI was not involved in this project and does not necessarily support it.
