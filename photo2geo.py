# photo2geo.py

''''
Bobby Price
n0mad-samurai
'''
'''
Python 3.x
'''
'''
License: GPLv3
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY# without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

To view a copy of the GNU General Public License
visit: http://www.gnu.org/licenses/gpl.html
'''
'''
Photo2geo is a digital photo mapping utility.
This utility extracts EXIF GPS data from
digital photos. That information is written
to a CSV and a KML file.
'''

import os       # os interfaces
import sys      # system specific functions
import re       # regex functions
import cmd      # support for line-oriented command interpreters
import csv      # csv processing functions
import time     # time processing functions
import argparse # parser for command-line options, arguments and sub-commands

from PIL import Image   # use Pillow Image class to process images

# Validate search path
def CheckInPath(inPath):

    # Validate input path
    # if not validated
    # exit program with error
    if not os.path.exists(inPath):
        sys.exit('Path does not exist: '+inPath)

    # Validate input path is readable
    if not os.access(inPath, os.R_OK):
        sys.exit('Directory is not readable: '+inPath)

    # No errors
    else:
        return inPath

# Validate save path
def CheckOutPath(outPath):

    # Validate output path
    # if not validated
    # exit program with error
    if not os.path.exists(outPath):
        sys.exit('Path does not exist: '+outPath)

    # Validate output path is writeable
    if not os.access(outPath, os.W_OK):
        sys.exit('Directory is not writeable: '+outPath)

    # No errors
    else:
        return outPath

# create the process class
class PhotoProcess():

    def __init__(self):

        # lists for capturing processed files
        self.fileList = []
        self.imageList = []
        self.noImageList = []
        self.noExifList = []
        self.noExifDateList = []
        self.noGpsList = []
        self.gpsZeroList = []
        self.resultList = []
        self.commentsList = []

        # initiate the cli method
        self.ParseCommandLine()

    # define the cli method
    def ParseCommandLine(self):

        # create an object to capture cli argument definitions
        parser = argparse.ArgumentParser('Python utility to extract EXIF GPS data from digital photos. It writes that data to CSV and KML files\n')

        # cli arguments for verbose option, directory to search, save csv results, save tablular results
        parser.add_argument('-v', '--verbose', help="option: displays additional file lists", action='store_true')
        parser.add_argument('-i', '--inDir', type= CheckInPath, required=True, help="required: directory/folder to search for photos")
        parser.add_argument('-o', '--outDir', type= CheckOutPath, required=True, help="required: directory/folder to save csv and kml files")

        # assign selected arguments to an object list
        args = parser.parse_args()

        # check args list for options
        # assign boolean results
        if args.verbose:
            self.VERBOSE = True
        else:
            self.VERBOSE = False

        # assign objects to the given directory arguments
        self.searchPath = args.inDir
        self.savePath = args.outDir

    # Process files in the folder/directory
    def ProcessFiles(self):

        # create the list of files
        count = 0
        for root, dirs, files in os.walk(self.searchPath):

            # separate filenames from path
            # and add those names to self.fileList
            for name in files:
                count += 1
                self.fileList.append(name)

            # exit program with error if directory is empty
            if count == 0:
                sys.exit('Directory is empty or files are hidden: '+root)

        # create the list of images
        for fname in self.fileList:

            '''
            Enable skip of my ghost file anomaly.
            If a recognized image in a sub-directory
            is used as a thumbnail for that
            sub-directory icon, the script will
            attempt to process that icon as if it
            were an image in the current directory.
            This produced a 'file does not exist' error.
            '''
            if os.path.exists(self.searchPath+'/'+fname):
                
                imgPath = self.searchPath+'/'+fname
                
                # identify valid image files and add those to self.imageList
                try:
                    with Image.open(imgPath) as img:
                        img.verify()
                        self.imageList.append(fname)
                        img.close
                except:
                    self.noImageList.append(fname)

        # parse self.imageList and
        # reconnect each image name
        # with its path
        # so much separating and rejoining of paths
        for image in self.imageList:
            fullName = os.path.join(self.searchPath, image)

            # open fullName of image
            # as bytes for reading
            # assign to object f
            with open(fullName, 'rb') as f:

                # case insensitive search of
                # image object f for
                # byte string 'exif' to ensure
                # there is an EXIF tag
                exifFound = re.search(b'exif', f.read(), re.I)
                f.close()

            # if there is a result
            if exifFound:

                with Image.open(fullName) as img:

                    # assign all EXIF metadata to objects
                    imgExif = img.getexif()

                    # EXIF DateTimeOriginal EXIF tag
                    XFDT = 306

                    # GPS IFD EXIF tag
                    GPSIFD = 34853

                    # test for EXIF date/time IFD tag
                    if imgExif.get(XFDT):

                        # assign EXIF DateTimeOriginal to object
                        dateInfo = imgExif.get(XFDT)

                        # split date and time into separate objects
                        exifDate, localTime = dateInfo.split(' ')
                        localDate = exifDate.replace(':', '-')

                    else:
                        self.noExifDateList.append(fname)

                    # test for EXIF GPS IFD tag
                    if imgExif.get_ifd(GPSIFD):

                        # assign GPS metadata to a dictionary
                        gpsInfo = imgExif.get_ifd(GPSIFD)

                    else:
                        self.noGpsList.append(fname)

                    '''
                    GPSLatitudeRef N or S(-) is dictionary key 1
                    GPSLatitude is 2
                    GPSLongitudeRef E or W(-) is dictionary key 3
                    GPSLongitude is 4
                    '''
                    LATREF = 1
                    LATDAT = 2
                    LONREF = 3
                    LONDAT = 4

                    # test for zero or null value in GPS metadata
                    # get GPSLatitude values assigned to degree, minute, second respectively
                    if str(gpsInfo.get(LATDAT)) not in ('(nan, nan, nan)'):
                        d2, m2, s2 = gpsInfo.get(LATDAT)

                        # convert DMS to DD.dd
                        try:
                            dd2Lat = float(d2 + m2 / 60 + s2 / 3600)
                            rndLat = round(dd2Lat, 6)
                            
                        except Exception as err:
                            sys.exit('GPS data error - \n', + str(err))

                        # assign '-' for Southern reference
                        if gpsInfo.get(LATREF) not in ('S'):
                            latitude = rndLat
                        else:
                            latitude = -rndLat

                    else:
                        # give that zero or null value an actual numeral decimal value
                        latitude = float(0.0)

                    # test for zero or null value in GPS metadata
                    # get GPSLongitude values assigned to degree, minute, second respectively
                    if str(gpsInfo.get(LONDAT)) not in ('(nan, nan, nan)'):
                        d4, m4, s4 = gpsInfo.get(LONDAT)

                        # convert DMS to DD.dd
                        try:
                            dd4Lon = float(d4 + m4 / 60 + s4 / 3600)
                            rndLon = round(dd4Lon, 6)
                            
                        except Exception as err:
                            sys.exit('GPS data error - \n', + str(err))

                        # assign '-' for Western reference
                        if gpsInfo.get(LONREF) not in ('W'):
                            longitude = rndLon
                        else:
                            longitude = -rndLon

                    else:
                        # give that zero or null value an actual numeral decimal value
                        longitude = float(0.0)

                    if latitude == float(0.0):
                        self.gpsZeroList.append(fname)

                # create final result list tuple
                self.resultList.append([image,localDate,localTime,latitude,longitude])

            # if there is no result
            # add that image
            # to self.noExifList
            else:
                self.noExifList.append(image)

        # create list of images that may contain comments
        # just because I can
        for image in self.imageList:
            fullName = os.path.join(self.searchPath, image)
            with open(fullName, 'rb') as f:

                # case sensitive search
                # for byte string 'File'
                commentsFound = re.search(b'File', f.read())

            if commentsFound:

                # create list of images with comments
                self.commentsList.append(image)

        # verbose display option
        if self.VERBOSE:

            # assign an object for OS cli options
            cli = cmd.Cmd()

            print('\nThese were not recognized as image files:')
            cli.columnize(self.noImageList, displaywidth=40)

            print('\nThese image files did not contain EXIF data:')
            cli.columnize(self.noExifList, displaywidth=40)

            print('\nThese image files contained EXIF data but no GPS data:')
            cli.columnize(self.noGpsList, displaywidth=40)

            print('\nThese image files contained EXIF GPS lat/lon data that was "0, 0, 0":')
            cli.columnize(self.gpsZeroList, displaywidth=40)

            print('\nThese image files may contain other comments:')
            cli.columnize(self.commentsList, displaywidth=40)

        # all methods completed
        # with no errors
        return True

    # Display of results
    # with a column format
    def DisplayResults(self):

        # display a message
        print('\nThese are the results:')

        # create header object
        header = [['Image Name','Local Date','Local Time','Latitude','Longitude']]

        # create object that joins the header and self.resultList
        dumpTable = header + self.resultList

        '''
        iterate through each element/column
        of each row of dumpTable, determine
        max width of each column, assign
        those values +3 to an object list
        '''
        widest_cols = [(max([len(str(row[i])) for row in dumpTable]) + 3) for i in range(len(dumpTable[0]))]

        # interate through column widths
        # using each column width, assign
        # that value to the row format list
        row_format = ''.join(["{:<" + str(widest_col) + "}" for widest_col in widest_cols])

        # display the table
        # by interating through
        # each row in dumpTable
        for row in dumpTable:

            # display all elements of each
            # row using the row_format
            print(row_format.format(*row))

    # CSV Results save to file
    def CsvResultsSave(self):

        # save csv file to the given directory
        try:
            # object contains full path to results file 'PhotoResults.csv'
            self.resultsCSV = self.savePath+'/Photo2GeoResults.csv'

            header = ['Image Name','Local Date','Local Time','Latitude','Longitude']

            # assign object to handle results file write process
            with open(self.resultsCSV, 'w') as outFile:

                writer = csv.writer(outFile)
                writer.writerow(header)
                writer.writerows(self.resultList)

                # close the file/end the write process
                outFile.close

            # display a message
            print('\nCSV File: '+self.savePath+'/Photo2GeoResults.csv Created')

        # catch and display error if we cannot
        # open the results file for writing
        except Exception as err:
            print('Failed: CSV File Save: '+str(err))

    # KML results save to file
    def KmlResultsSave(self):

        # save csv file to the given directory
        try:
            # object contains full path to results file 'PhotoResults.csv'
            self.resultsKML = self.savePath+'/Photo2GeoResults.kml'

            dataCSV = csv.reader(open(self.resultsCSV), delimiter = ',')
            
            #Skip the 1st header row.
            next(dataCSV, None)
            
            #Open the file to be written.
            f = open(self.resultsKML, 'w')

            # write the kml file
            f.write("<?xml version='1.0' encoding='UTF-8'?>\n")
            f.write("<kml xmlns='http://earth.google.com/kml/2.2'>\n")
            f.write("<Document>\n")
            f.write("   <name>""Photo2GeoResults.kml""</name>\n")

            for row in dataCSV:
                f.write("   <Placemark>\n")
                f.write("       <name>" + str(row[0]) + "</name>\n")
                f.write("       <description>""Mapped Photo""</description>\n")
                f.write("       <TimeStamp>\n")
                f.write("           <when>" + str(row[1]) + "T" + str(row[2]) + "</when>\n")
                f.write("       </TimeStamp>\n")                
                f.write("       <Point>\n")
                f.write("           <coordinates>" + str(row[4]) + "," + str(row[3]) + ",""0""</coordinates>\n")
                f.write("       </Point>\n")              
                f.write("   </Placemark>\n")

            f.write("</Document>\n")
            f.write("</kml>\n")
            f.close()

            # display a message
            print('\nKML File: '+self.savePath+'/Photo2GeoResults.kml Created')
            
        # catch and display error if we cannot
        # open the results file for writing
        except Exception as err:
            print('Failed: KML File Save: '+str(err))        

# the main routine
if __name__ == '__main__':

    # capture start time
    startTime = time.time()

    VERSION = 'v0.20 March 2023'


    # instantiate the process class
    PhotoObj = PhotoProcess()

    print('\nWelcome to photo2geo '+VERSION)
    print('Local System Type: '+sys.platform)
    print('Local System Time: '+time.ctime())

    # Initiate process
    # if process fails
    # display aborted message
    # for any errors not specifically caught
    if PhotoObj.ProcessFiles():

        PhotoObj.DisplayResults()

        PhotoObj.CsvResultsSave()

        PhotoObj.KmlResultsSave()

        print('\nProgram completed normally')
        # capture end time
        endTime = time.time()
        # calculate duration
        duration = endTime - startTime
        # display elapsed time with 2 decimal places
        print('\nElapsed time:', '{:.2f}'.format(duration)+' seconds\n')

    else:

        print('Process Aborted!')
