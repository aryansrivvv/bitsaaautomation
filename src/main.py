#!/usr/bin/env python3

import os , re , time , json , datetime , random 
import openai ,  anthropic 



from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException , ElementClickInterceptedException
from selenium.webdriver.common.by import By

from config import *
from sheets_setup import *
from driver_setup import initialise_driver
import whatsapp_scraper
import linkedin_scraper

def print_current_date_time(sheets):
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    statement = "Scanning @ "+ formatted_time
    time_values = [[statement]]
    send_data_to_sheets(time_values ,  sheets ,id = SPREADSHEET1_ID)
    print("time printed to sheet")


def main():
    print("----SCRIPT STARTS----")
    print("Setting Driver")
    print("Whatsapp Scraping Starts")
    whatsapp_scraper.main()
    print("whatsapp scraper over , starting Linkedin Scraper")
    linkedin_scraper.main()
    print("----SCRIPT ENDS----")



