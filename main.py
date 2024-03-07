from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from pypdf import PdfReader
import re
from datetime import datetime, timedelta

import time
import urllib.request

from icalendar import Calendar, Event

options = Options()
options.add_argument('--headless')
driver = webdriver.Firefox(options)

wait = WebDriverWait(driver, 10)
driver.get("https://www.bathnes.gov.uk/webforms/waste/collectionday/")
wait.until(EC.presence_of_element_located((By.ID, "PCInputp1")))
postcodeInput = driver.find_element(by=By.ID, value = "PCInputp1")
pc = input("Enter a postcode: ")
postcodeInput.send_keys(pc)

print("\n")

wait.until(EC.presence_of_element_located((By.ID, "PCFindButtonp1")))
postcodeFindButton = driver.find_element(by=By.ID, value = "PCFindButtonp1")
postcodeFindButton.click()

wait.until(EC.presence_of_element_located((By.ID, "PCSelectp1")))
housePicker = driver.find_element(by=By.ID, value = "PCSelectp1")
housePicker.click()

housePickerSelection = Select(housePicker)
print("Please pick a number")
for index, option in enumerate(housePickerSelection.options[1:]):
    print(str(index) + ": " + option.accessible_name)
sel = int(input("Selection: "))
housePickerSelection.select_by_index(sel+1)

wait.until(EC.presence_of_element_located((By.ID, "nextBtn")))
driver.find_element(by=By.ID, value = "nextBtn").click()
wait.until(EC.presence_of_element_located((By.ID, "calendarLinkp2")))
urllib.request.urlretrieve(driver.find_element(by=By.ID, value="calendarLinkp2").get_attribute('href'), "tmp.pdf")

reader = PdfReader("tmp.pdf")
page = reader.pages[0]
collection_text = page.extract_text()

def getRecyclingText(text):
    # Find the index of "Recycling –"
    matchRecycling = re.search(r"\bRecycling -\b", text)
    recyclingStartIndex = matchRecycling.start() if matchRecycling else None

    # Find the index of "Garden waste –"
    matchGardenWaste = re.search(r"\bGarden waste -", text)
    GardenWasteStartIndex = matchGardenWaste.start() if matchGardenWaste else None

    RecyclingText = text[recyclingStartIndex:GardenWasteStartIndex]
    matchMonthDate = re.search(r"Month Date", RecyclingText)
    datesStart = matchMonthDate.end() + 2 if matchMonthDate else None
    RecyclingText = RecyclingText[datesStart:].replace(',', '')
    return RecyclingText

def getGardenWasteText(text):
    # Find the index of "Garden waste –"
    matchGardenWaste = re.search(r"\bGarden waste -", text)
    GardenWasteStartIndex = matchGardenWaste.start() if matchGardenWaste else None

    # Find the index of "Recycling –"
    matchRubbish = re.search(r"\bRubbish bin", text)
    rubbishStartIndex = matchRubbish.start() if matchRubbish else None

    gardenWasteText = text[GardenWasteStartIndex: rubbishStartIndex]
    matchMonthDate = re.search(r"Month Date", gardenWasteText)
    datesStart = matchMonthDate.end() + 2 if matchMonthDate else None
    gardenWasteText = gardenWasteText[datesStart:].replace(',', '')
    return gardenWasteText

def getRubbishText(text):
    # Find the index of "Rubbish "
    matchRubbish = re.search(r"\bRubbish bin", text)
    rubbishStartIndex = matchRubbish.start() if matchRubbish else None

    # Find the index of "Christmas tree –"
    matchXmasTree = re.search(r"Christmas tree", text)
    xmastreeStartIndex = matchXmasTree.start() if matchXmasTree else None

    rubbishText = text[rubbishStartIndex:xmastreeStartIndex]
    matchMonthDate = re.search(r"Month Date", rubbishText)
    datesStart = matchMonthDate.end() + 2 if matchMonthDate else None
    rubbishText = rubbishText[datesStart:].replace(',', '')
    return rubbishText


RecyclingText = getRecyclingText(collection_text)
GardenWasteText = getGardenWasteText(collection_text)
RubbishText = getRubbishText(collection_text)

def isRecyclingOnThisDay(day, month, year):
    for line in RecyclingText.splitlines():
        if str(year) in line and month in line:
            pattern = re.compile(r'\b{}\b'.format(day))
            match = re.search(pattern, line)
            if(match is not None):
                return True
    return False

def isGardenWasteOnThisDay(day, month, year):
    for line in GardenWasteText.splitlines():
        if str(year) in line and month in line:
            pattern = re.compile(r'\b{}\b'.format(day))
            match = re.search(pattern, line)
            if(match is not None):
                return True
    return False

def isRubbishOnThisDay(day, month, year):
    for line in RubbishText.splitlines():
        if str(year) in line and month in line:
            pattern = re.compile(r'\b{}\b'.format(day))
            match = re.search(pattern, line)
            if(match is not None):
                return True
    return False

def generate_dates(start_date, end_date):
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    current_datetime = start_datetime.replace(hour=7, minute=0, second=0)

    while current_datetime <= end_datetime:
        year = current_datetime.year
        month = current_datetime.strftime('%B')  # Full month name as a string
        day = current_datetime.day

        yield year, month, day, current_datetime

        current_datetime += timedelta(days=1)

# Example usage
start_date = "2023-11-01"
end_date = "2024-11-30"

cal = Calendar()
f = open("bins.ical", "wb")

def display(cal):
   return cal.to_ical().decode("utf-8").replace('\r\n', '\n').strip()

def add_bin_event(cal, bintypes, dt):
    event = Event()
    event.add('dtstart', dt)
    event['dtstart'].to_ical()
    binstr = "Put out the " + ' , '.join(bintypes) + " bins today!"
    event.add('summary', binstr)
    cal.add_component(event)


for year, month, day, dt in generate_dates(start_date, end_date):
    bins = []
    if(isRecyclingOnThisDay(day, month, year)):
        bins.append("recycling")
    if(isGardenWasteOnThisDay(day, month, year)):
        bins.append("garden Waste")
    if(isRubbishOnThisDay(day, month, year)):
        bins.append("rubbish")
    if bins != []:
        add_bin_event(cal, bins, dt)


f.write(cal.to_ical())
f.close()