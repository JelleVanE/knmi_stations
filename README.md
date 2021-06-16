# Netherlands temperature map
The contour function in the knmi_stations module provides a contour map of temperatures in the Netherlands using scraped weather data from and coordinates of KNMI weather measurement stations. An attempt to replicate KNMI's own https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/temperatuur.png.

Temperatures are interpolated using inverse distance weighting (IDW) for now.

A Jupyter Notebook demonstrating the module can be found [here](example.ipynb).

My motivation for this project was to improve my Python skills in scraping, data visualization and working with geospatial data.

Please take caution:
* The default value of the IDW power parameter (4.5) was in no way chosen in a scientific manner.
* IDW is a weighted average of the supplied data, so it cannot extrapolate in the sense that all computed temperatures will be in the range between the minimum and maximum of all KNMI stations.
* Although temperatures at sea are imputed and shown in the contour plot, these values are expected to be very inaccurate. A future step is to restrict the contour plot to land, similarly to KNMI's map mentioned above.
## Dependencies
* numpy
* pandas
* geopandas
* matplotlib
* cartopy
* shapely
* bs4
## To do
* More advanced interpolation techniques (e.g. Kriging).
* Graphical improvements for the contour plots.
## References
* **KNMI measurement station coordinates**: KNMI, scraped from http://projects.knmi.nl/datacentrum/catalogus/catalogus/content/nl-obs-surf-stationslijst.htm
* **KNMI weather data**: KNMI, scraped from https://knmi.nl/nederland-nu/weer/waarnemingen
* **Netherlands map**: BRK, CC-BY Kadaster. "Provinciegrenzen 2018 exact, op kustlijn", accessed online at http://www.imergis.nl/asp/47.asp
The Creative Commons Zero license applies to the contents of the KNMI website. Therefore, I am obligated to mention that KNMI was not involved in this project and does not necessarily support it.
