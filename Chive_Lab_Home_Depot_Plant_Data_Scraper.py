import os, logging, re
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright
from time import sleep

##
#Script to crawl a Lawn & Garden subcategry and list the common and botanical names of each plant.
##


#Path to CSV output:
downloadPath = r"C:\Some-Download-Folder"

##Logging:
#Create timestamp:
startTime = datetime.now().strftime("%m-%d-%Y-%I-%M-%S%p")

fullLogPath = Path(f"{downloadPath}\logs-{startTime}.txt")
fullOutputCSVPath = Path(f"{downloadPath}\List_of_Common_and_Botanical_Plant_Names_Sold_by_HomeDepot-{startTime}.csv")

with open(fullOutputCSVPath, mode="w", newline="", encoding="UTF-8") as outputCSV:
	outputCSV.write("Product Name, Common Name, Botanical Name\n")
with open(fullLogPath, mode="w", newline="", encoding="UTF-8") as outputLog:
	outputLog.write(f"Logs for Chive_Lab_Home_Depot_Plant_Data_Scraper.py started on {startTime}:\n\n")

PRODUCT_THUMBNAIL_LINKS = f"#browse-search-pods-1 > div:nth-child(\[0-9]\) > div > a > div > img.product-image--secondary-image--dmvgq.stretchy"
#PRODUCT_THUMBNAIL_LINKS = f"#browse-search-pods-1 > div:nth-child(\\)"

PLANT_NAMES_LISTED = []

def writeLog(content: str):
	"""Writes its content param to the log file. For any custom messages not created by logging library."""
	with open(fullLogPath, mode="a", newline="", encoding="UTF-8") as outputTXT:
		outputTXT.write(f"\n{content}\n")
	return None
logging.basicConfig(filename=fullLogPath, filemode='a', format='%(name)s - %(levelname)s - %(message)s')


#Browswer automation:
#Change invisible to True to "run in background":
invisible = False
base_url = fr"https://www.homedepot.com"
browserUserData = f"{downloadPath}\Playwright_Data"

#nextPageSelector = "[aria-label=\"Next\"]"
nextPageNumber = 2

def waitForNetworkIdle(playwright: Playwright, integer: int)-> None:
	"""Pauses execution for the number of seconds given as integer then checks/waits for an idle network; returns None."""
	#Used to pause web browsing to give more time for pages to load or other events.
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	sleep(integer)
	try:
		homeDepotPage.wait_for_load_state("networkidle", timeout=10000)
	except Exception as skipIt:
		#homeDepotPage.reload()#Haven't tried reloading yet.
		sleep(5)
	sleep(1)
	return None

def openHomeDepot(playwright: Playwright) -> None:
	"""Opens a browser then goes to the designated home depot page."""
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	browser = playwright.chromium.launch_persistent_context(browserUserData, args = ["--start-fullscreen" ,"--start-maximized"], base_url = base_url, downloads_path=downloadPath, accept_downloads=True, headless=invisible)
	# Open new page
	homeDepotPage = browser.new_page()
	#sleep(1)
	# Go to about:base_url
	
	try:
		#URL of specific sub category to scrape
		homeDepotPage.goto(fr"https://www.homedepot.com/b/Outdoors-Garden-Center-Outdoor-Plants-Garden-Flowers/N-5yc1vZ2fkp97o", timeout=0)
		waitForNetworkIdle(playwright, 1)
		sleep(1)
	except Exception as authenticationError:
		#writeLog(f"\n{authenticationError}")
		logging.error("Unable to log in. Log-in page may have been skipped or there may have been an error.", exc_info=False)	
	return None

def copyPlantProductData(playwright: Playwright, productName) -> None:
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	waitForNetworkIdle(playwright, 1)
	sleep(1)
	homeDepotPage.click("#product-section-key-feat div[role=\"button\"]:has-text(\"Specifications\")", timeout=0)
	sleep(1)
	botanicalNameSelector = "th:has-text(\"Botanical Name\")+td"
	botanicalName = homeDepotPage.locator(botanicalNameSelector).text_content() if homeDepotPage.query_selector(botanicalNameSelector) else "Botanical Name NOT Found"
	commonNameSelector = "th:has-text(\"Common Name\")+td"
	commonName = homeDepotPage.locator(commonNameSelector).text_content() if homeDepotPage.query_selector(commonNameSelector) else "Common Name NOT Found"
	print(f"{productName}, {botanicalName}, {commonName}")
	with open(fullOutputCSVPath, mode="a", newline="", encoding="UTF-8") as outputCSV:
		outputCSV.write(f'"'+productName+'"' + "," + '"'+commonName+'"' + "," + '"'+botanicalName+'"' + "\n")
	return None

#Change name and extend func: After getting list, loop click names and exectute a TBD func to grab the data and .go_back().
def listEachPlantOnProductCategoryPage(playwright: Playwright) -> None:
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	""""""
	homeDepotPage.mouse.wheel(0,3000)
	sleep(1)
	elementHandle = ".product-image__wrapper--dmvgq>img"
	productSeachResultSelector = homeDepotPage.query_selector_all(elementHandle) # .product-image, .browse-search__pod, [data-testid=\"product-pod\"],
	plantProductPages = []#Temp list to use to loop click products and get data
	for product in productSeachResultSelector:
		productAltText = product.get_attribute("alt")
		print(f"{productAltText}")
		if productAltText not in PLANT_NAMES_LISTED:
			PLANT_NAMES_LISTED.append(productAltText)
			plantProductPages.append(productAltText)
	for num, product in enumerate(plantProductPages):
		###Disable the conditional statement below if starting a new category.
		#Add a specific plant name here to pick up after a crash or what ever:
		plantToRestartAt = "Rainbow of Roses Landscape Assortment, Dormant Bare Root Rose Bushes (5-Pack)"
		if plantToRestartAt not in plantProductPages:
			print(f"{plantToRestartAt} not found. Skipping to next product search results page.")
			break
		###
		textSelector = f"text={product}"
		homeDepotPage.click(textSelector, timeout=0)
		sleep(1)
		waitForNetworkIdle(playwright, 1)
		#sleep(3)
		##Open plant specs and copy data
		copyPlantProductData(playwright, product)
		homeDepotPage.go_back()
		#waitForNetworkIdle(playwright, 1)
		sleep(2)
		homeDepotPage.mouse.wheel(0,3000)
		sleep(2)
		#if num == 3:#Disable when done testing.
			#break#Disable when done testing.
	sleep(1)
	#print(PLANT_NAMES_LISTED)
	return PLANT_NAMES_LISTED

def goToNextPage(playwright: Playwright, functionToExecute) -> None:
	# Go to next page of search result.
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	nextPageSelector =  f"nav[role=\"navigation\"] >> text={nextPageNumber}"
	if homeDepotPage.query_selector(nextPageSelector):
		homeDepotPage.click(nextPageSelector)
		print(f"Done with page # {nextPageNumber}. Clicked Next Button.")
		waitForNetworkIdle(playwright, 1)
		sleep(1)
		functionToExecute
		nextPageNumber += 1
	return None


def navigateHomeDepotCategory(playwright: Playwright) -> None:
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	print("Navigating homeDepotPage")
	nextPageNumber = 2
	nextPageSelector =  f"nav[role=\"navigation\"] >> text={nextPageNumber}"
	homeDepotPage.mouse.wheel(0,3000)
	listEachPlantOnProductCategoryPage(playwright)
	sleep(1)
	while (homeDepotPage.query_selector(nextPageSelector)):
		goToNextPage(playwright, listEachPlantOnProductCategoryPage(playwright))
	if (homeDepotPage.query_selector(f"nav[role=\"navigation\"] >> text={nextPageNumber + 1}")):
		try:
			print("Clicking the last page?")
			goToNextPage(playwright, listEachPlantOnProductCategoryPage(playwright))
		except Exception as e:
			print(f"End of the list?:\n{e}")
		
	#ReNav and copy data after getting list of titles to click through. Reset page numbering:
	#nextPageNumber = 2


def closeHomeDepotplaywright(playwright: Playwright) -> None:
	# Close page/browser.
	global homeDepotPage, browser, PLANT_NAMES_LISTED, nextPageNumber, nextPageSelector
	homeDepotPage.close()
	browser.close()
	PLANT_NAMES_LISTED = list(set(PLANT_NAMES_LISTED))
	#print([f"{plant}\n" for plant in PLANT_NAMES_LISTED])
	return None

def runAllAndCrawlHomeDepot(playwright: Playwright) -> None:
	openHomeDepot(playwright)
	navigateHomeDepotCategory(playwright)
	closeHomeDepotplaywright(playwright)
	writeLog("\n\nExecution Successfull")
	return None

try:
	with sync_playwright() as playwright:
		runAllAndCrawlHomeDepot(playwright)
except Exception as mainFunctionError:
	#writeLog(f"\n{mainFunctionError}")
	writeLog(f"\n###End of Success Logs###\n\n")#Just add some verticle/blank space between list of downloaded files and fatal error:
	print(f"\n{mainFunctionError}")
	logging.error("Exception occurred:\n", exc_info=True)