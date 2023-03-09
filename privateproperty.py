from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import bs4
import re
import pandas as pd




# driver = webdriver.Chrome(ChromeDriverManager().install())


# okay, we need a way to combine all of our scrapers and include the Prefect
# first let's get all the scrapers into one script.

# 
def setup_driver():
    """"start the chrome driver """
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.implicitly_wait(10)
    
    return driver
def privatep_search(driver):
    """go to privateproperty.co.za
    and click on the allow cookies pop_up"""
    
    driver.get('https://www.privateproperty.co.za/to-rent')
    time.sleep(2)
    driver.find_element(By.XPATH,'//*[@id="consentManager"]/div/div/button[2]').click()
    return driver

def search_privatep(driver,suburb):
    """Fill in the search bar and get base url for that suburb"""
    # find the search bar
    search_bar = driver.find_element(By.XPATH,'//*[@id="homePageAutoComplete"]/div/div/div/div[2]/form/div/input[1]')
    time.sleep(2)
    def send_keys_delay(controller,keys,delay=0.1):
        """"send keys one at a time"""
        for key in keys:
            controller.send_keys(key)
            time.sleep(delay)

    send_keys_delay(search_bar,suburb)
    time.sleep(3)
    first_search = driver.find_element(By.XPATH,'//*[@id="homePageAutoComplete"]/div/div/div/div[2]/form/div/div/div[1]').click()
    base_url = driver.current_url
    return base_url,driver

def make_soup_body(driver):
    
    soup = BeautifulSoup(driver.page_source,"html.parser")
    body_soup = soup.body
    return body_soup

def count_pages_privatep(body_soup:bs4.element.Tag) -> int:
    """"find the number of listed places in the current  search to figure out how many pages to crawl on privateproperty.co.za"""
    listingcount = body_soup.find('div', {'class':'listingCount'})
    if listingcount:
      string1 = listingcount.text
    
      split_counts = re.findall('\d+',string1)
    
      this_page = int(split_counts[1])
      total_listings = int(split_counts[-1])
      pages_to_search = -(-total_listings//this_page)
    else: pages_to_search = 1
    return pages_to_search 

def subsequent_urls_privatep(page_count,base_url):
    """creates a list of the urls to search after searching page 1"""
    urls_list = []
    for i in range(2,page_count+1):
        # i will be our page numbers to shoot into the url. 
        next_url = base_url + f"?page={i}"
        urls_list.append(next_url) 
    return urls_list # if it doesn't produce any urls, we moce on.


def extract_listing_info_privatep(soup_body):
  """ Extract info from all listings on one page of privateproperty.co.za"""
  data = []

  

  # Find relevant info for each listing
  info_of_listings = soup_body.find_all('div',{'class':"infoHolder"}) 
  image_info = soup_body.find_all('div',{'class':"imageHolder"})
  overall_content =soup_body.find_all('a',{'class':"listingResult row"})
  assert len(info_of_listings)== len(image_info)==len(overall_content)
  print("BATCH SIZE:", len(info_of_listings))
  
  
  # Extracting to a dictionary
  counter = 0 
  for i,j,k in zip(info_of_listings,image_info,overall_content): # use i for all the info and j for the image info
      # Extraction dictionary
      d = {'title':'','priceDescription':'','priceAdditionalDescriptor':'', 'suburb':'',
           'number_of_bedrooms':'','number_of_bathrooms':'','number_of_garages':'',"size":"",
           'available_from':'',"url":""}
      try:
        d['title']                      = i.find("div",{'class':"title"}).text
        d['priceDescription']           =i.find("div",{'class':"priceDescription"}).text
        d['priceAdditionalDescriptor']  = i.find("div",{'class':"priceAdditionalDescriptor"}).text
         
        d['suburb']                     = i.find("div",{'class':"suburb"}).text
        if i.find("div",{'class':"icon bedroom"}):
          d['number_of_bedrooms']         = i.find("div",{'class':"icon bedroom"}).find_previous_sibling().text
        else:
          d['number_of_bedrooms']        = ""
        if i.find("div",{'class':"icon bathroom"}):
          d['number_of_bathrooms']        = i.find("div",{'class':"icon bathroom"}).find_previous_sibling().text
        else: d['number_of_bathrooms'] = ""
        if i.find("div",{'class':"icon garage"}):
          d['number_of_garages']          = i.find("div",{'class':"icon garage"}).find_previous_sibling().text
        else: d['number_of_garages'] = ""
        d["size"]                     = "Unknown" # could get the size, but would have to go to each individual listing url
        if j.find("div",{'class':"statusFlag flagAvailableNow"}):
          d['available_from']   = "Now"
        elif j.find("div",{'class':"statusFlag flagAvailableFrom"}):
          d['available_from']   = j.find("div",{'class':"statusFlag flagAvailableFrom"}).text
        else:
          d['available_from'] = ""
        
        

        
        
        d['url']              = "https://www.privateproperty.co.za"+ k['href']
         
         
      except Exception as e: 
        print(e)
      data.append(d)
      
      counter +=1  
  return data 

def main_privatep():
    #steps
    all_data = []
    # go to url and get throught the cookie
    driver  = setup_driver()
    driver = privatep_search(driver)
    # choose the suburb from a list 
    suburbs= ("Sea Point",'Green Point',"Gardens")
    for suburb in suburbs:
        
        base_url,driver = search_privatep(driver,suburb)
        soup_body = make_soup_body(driver) 
        number_of_pages_to_search = count_pages_privatep(soup_body)
        other_urls_list = subsequent_urls_privatep(number_of_pages_to_search,base_url)

        #get info from one page 
        data = extract_listing_info_privatep(soup_body)
        
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = make_soup_body(driver)
            data_next = extract_listing_info_privatep(next_soup_body)
            all_data.extend(data_next)
            
        # go bac to the search page 
        time.sleep(5)
        driver.get('https://www.privateproperty.co.za/to-rent')
    #driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    print("The shape of the df",df.shape)
    print("The drivertype: ",type(driver))
    return df, driver


df,driver = main_privatep()

print(df.head(50))

