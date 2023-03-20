## Photo2Geo

Photo2geo is a digital photo mapping utility. It is written in Python 3.11.

This utility extracts EXIF GPS data from digital photos. That information is written to a CSV and a KML file. You can import the KML file into **gpxsee** https://www.gpxsee.org/, **gpsvisualizer** https://www.gpsvisualizer.com/, or **google earth** https://earth.google.com/web/ .
You can import the CSV file into **gpsvisualizer** https://www.gpsvisualizer.com/.

## Usage:
### options:
  -h, - -help
  
  -v, - -verbose, displays additional file lists
  
  -i, - -inDir, required input folder/directory to search for photos
  
  -o, - -outDir, required output folder/directory to save CSV and KML files
  
## Requirements

Photo2Geo requires the Python Imaging Library (PIL).