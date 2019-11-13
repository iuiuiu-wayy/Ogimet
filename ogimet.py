import requests, csv
import numpy as np
from lxml import html
from calendar import monthrange
from dateutil.rrule import rrule, MONTHLY, DAILY
from datetime import datetime
import os
from sys import argv

class Downloader():
    """docstring for Downloader."""

    def __init__(self):
        if os.getcwd().__contains__("\\"):
            self.sep = "\\"
        else:
            self.sep = "/"

        self.comb = {}

        try:
            os.mkdir('weather')
        except:
            pass


    def month_iter(self, start_month, start_year, end_month, end_year):
        start = datetime(start_year, start_month, 1)
        end = datetime(end_year, end_month, 1)
        return ((d.month, d.year) for d in rrule(MONTHLY, dtstart=start, until=end))

    def tryGetTable(self, tree, year, month, attempt=10):
        if attempt == 0:
            return "Fail"
        try:
            return tree.xpath('//table[@border="0"]')[0]
        except:
            tree = self.requestData(self.linkConstructor(year, month))
            self.tryGetTable(tree, year, month, attempt=attempt-1)

    def requestData(self,link, attempt=10):
        if attempt == 0:
            return "Fail"
        page = requests.get(link)
        if any( [page.status_code != 200, not page.content.__str__().__contains__('summary')]):
            requestData(link, attempt=attempt-1)
        tree = html.fromstring(page.content)
        return tree

    def running_all(self, end_year, end_month, start_year=2000, start_month=1, stationid="97240", location=os.getcwd()):
        self.stationid = stationid
        self.location = location + self.sep + "weather"
        for m in self.month_iter(start_month, start_year, end_month, end_year):
            print("running " + m[1].__str__() + "-" + m[0].__str__() )
            #print(m[0])
            #print(m[1])
            self.completeRun(m[1], m[0])

    def linkConstructor(self, year, month):
        link = "https://www.ogimet.com/cgi-bin/gsynres?lang=en&ind="+ self.stationid +"&ndays=" + monthrange(year, month)[1].__str__() + "&ano=" + year.__str__() + "&mes=" + "%02d" % month + "&day=" + "%02d" % monthrange(year, month)[1] + "&hora=00&ord=REV&Send=Send"
        return link

    def requestData(self,link, attempt=10):
        if attempt == 0:
            return "Fail"
        page = requests.get(link)
        if any( [page.status_code != 200, not page.content.__str__().__contains__('summary')]):
            requestData(link, attempt=attempt-1)
        tree = html.fromstring(page.content)
        return tree

    def completeRun(self, year, month):
        link = self.linkConstructor(year, month)
        print(link)
        data = self.requestData(link)
        self.writeData(data, year, month, self.location, '')

    def failDetector(self, year, month):
        with open('report.log', 'a') as report:
            report.write(year.__str__() + "-" + month.__str__() + "\n")

    def writeData(self,tree, year, month, location, basename=''):

        if tree == "Fail":
            self.failDetector(year, month)
            return 0
        table = self.tryGetTable(tree, year, month)
        if table == "Fail":
            self.failDetector(year, month)
            return 0
        caption = table.getchildren()[0]
        tr = table.getchildren()[2:monthrange(year, month)[1] + 2]
        for a in tr[::-1]:
            data = {}
            data['date'] = a.getchildren()[0].text_content() # bulan/tanggal
            data['maxtmp'] = a.getchildren()[1].text_content() # max temp
            data['mintmp'] = a.getchildren()[2].text_content() # min temp
            data['avgtmp'] = a.getchildren()[3].text_content() # avg temp
            data['tdavg'] = a.getchildren()[4].text_content() # Td avg
            data['Hravg'] = a.getchildren()[5].text_content() # Hr. avg
            data['wnddir'] = a.getchildren()[6].text_content() # wind direction
            data['wndspd'] = a.getchildren()[7].text_content() # wind speed
            data['sfcprs'] = a.getchildren()[8].text_content() # surface pressure
            data['prec'] = a.getchildren()[9].text_content() # prec
            data['TotClOct'] = a.getchildren()[10].text_content() # Tot Cl Oct
            data['LowClOct'] = a.getchildren()[11].text_content() # low Cl Oct
            data['SunDuration'] = a.getchildren()[12].text_content() # sun duration in hr
            data['visibility'] = a.getchildren()[13].text_content() # visibility in km
            try:
                data['weather3'] = a.getchildren()[14].getchildren()[0].attrib # weather 03 utc
                data['weather6'] = a.getchildren()[15].getchildren()[0].attrib # 06
                data['weather9'] = a.getchildren()[16].getchildren()[0].attrib # 09
                data['weather12'] = a.getchildren()[17].getchildren()[0].attrib # 12
                data['weather15'] = a.getchildren()[18].getchildren()[0].attrib # 15
                data['weather18'] = a.getchildren()[19].getchildren()[0].attrib # 18
                data['weather21'] = a.getchildren()[20].getchildren()[0].attrib # 21
                data['weather24'] = a.getchildren()[21].getchildren()[0].attrib # 00
            except:
                data['weather3'] = 'No Data'
                data['weather6'] = 'No Data'
                data['weather9'] = 'No Data'
                data['weather12'] = 'No Data'
                data['weather15'] = 'No Data'
                data['weather18'] = 'No Data'
                data['weather21'] = 'No Data'
                data['weather24'] = 'No Data'


            #print(data)
            #np.save(location + 'data' + data['date'].split("/")[0] + '-' + data['date'].split("/")[1] + '.npy', data)
            name = self.sep + basename + 'data' + year.__str__() + '-' + "%02d" % month + '-' + data['date'].split("/")[1] + '.csv'
            self.comb[name]=data

            for key, value in data.items():
                timestamp = year.__str__() + "-%02d-" % month + data['date'].split("/")[1]
                self.writecsv(key, timestamp , value)

    def writecsv(self, key, timestamp, val):
        #self.comb[filename] = dict
        filename = self.location + self.sep + key + ".csv"
        with open(filename, 'a') as csv_file:
            if any ( [val == '----' , val == 'No data']):
                val = 'NA'
            if val == 'Tr':
                val = 0
            csv_file.write("%s,%s\n" % (timestamp, val))

if __name__ == '__main__':
    cont = True
    try:
        script, yend, mend, ystart, mstart, stationid = argv
    except:
        print("usage >>>> python ogimet.py (end-year) (end-month) (start-year) (start-month) (stationid)")
        print("example >>>>> python ogimet.py 2019 5 2019 1 97240")
        print(" WARNING!!!!: DO NOT OPEN THE FILE WHILE DOWNLOADED!!!!")
        cont = False
    if cont:
        D = Downloader()
        #D.running_all(2019, 5, start_year=2019, start_month=1, stationid="97240")
        D.running_all(int(yend), int(mend), int(ystart), int(mstart), stationid)
