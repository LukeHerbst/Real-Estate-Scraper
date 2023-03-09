import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import pandas as pd

def go_to_next_url(driver,url):
    """go to url of the next website
    """
    driver.get(url)
    time.sleep(2)
    
    return driver



def property24_search(driver,suburb):
    """Do the search of one suburb and return base url for that specific suburb search
    also click on the search button and cookies button"""
    # find the search bar
    search_bar = driver.find_element(By.XPATH,'//*[@id="token-input-AutoCompleteItems"]')
    time.sleep(2)
    def send_keys_delay(controller,keys,delay=0.1):
        """"send keys one at a time"""
        for key in keys:
            controller.send_keys(key)
            time.sleep(delay)

    # send keys
    send_keys_delay(search_bar,suburb)
    time.sleep(3)
    #click on first option
    driver.find_element(By.XPATH,'//*[@id="SearchBox"]/div/ul/li').click()
    time.sleep(2)
    #Click on search button
    driver.find_element(By.XPATH,'//*[@id="SearchBar"]/div[2]/div[1]/div/form/button').click()
    #Click on cookies button
    try:
        driver.find_element(By.XPATH,'//*[@id="cookieBannerClose"]').click()
    except:
        print("no Cookies button ")
        
    
    time.sleep(4)
    base_url = driver.current_url
    return base_url
    
# got make_soup body already

def count_pages_p24(body_soup):
    """"find the number of listed places in the search to figure out how many pages to crawl on property24"""
    listingcount_options = body_soup.find_all("div",{'class':"pull-right"})
    for i in listingcount_options:
        
        if "Showing" in i.text:
            
            listingcount_string = i 
    split_counts = re.findall('\d+',listingcount_string.text)
    
    this_page = int(split_counts[1])
    total_listings = int(split_counts[-1])
    pages_to_search = -(-total_listings//this_page)
    return pages_to_search 


def subsequent_urls_p24(page_count,base_url):
    """Create the subsequent urls given teh page_count """
    urls_list = []
    for i in range(2,page_count+1):
        # i will be our page numbers to shoot into the url. 
        next_url = base_url + f"/p{i}"
        urls_list.append(next_url) 
    return urls_list # if it doesn't produce any urls, we move on.

def extract_listing_info_p24(driver,soup_body,current_url):
  """ Extract info from all listings on one page of property24.com/to-rent
      
  """
  data = []
  #current_url = driver.current_url 
  print("The Current_url is ",current_url) 


  

  # FIND ALL PRODUCT ITEMS
  info_of_listings = soup_body.find_all(['div',"span","a"],{'class',"p24_content"}) # need to find a waty to get rid of the duplicate 
  image_info = soup_body.find_all(['span','div'],{"class":["js_listingTileImageHolder",'p24_promotedImage']}) # need to find a waty to get rid of the duplicate
  url_info =soup_body.find_all("div",{'class':["p24_regularTile",'p24_promotedTile']}) # still has a duplicate, as with the others, the different one or promoted one only appears on page 1
  # I am assuming that the appearance changes, they proabably sell the space to the propert companies
  print('len(info_of_listings)',len(info_of_listings),"len(image_info)",len(image_info),"len(url_info)",len(url_info))
  print('len(info_of_listings)',len(set(info_of_listings)),"len(image_info)",len(set(image_info)),"len(url_info)",len(set(url_info)))
  # so on page 2 of Greenpoint, suddenly there is one less in the info of listings. 
  # Which means it actually wasn't duplicated for once, but still it causes problems
  # we need to remove the duplicates earlier
  assert len(info_of_listings)== len(image_info)==len(url_info)
  print("BATCH SIZE:", len(info_of_listings))
  

  # Extracting to a dictionary
  counter = 0 
  for i,j,k in zip(info_of_listings,image_info,url_info): 
    # time will tell if the duplicate is giving us problems or if it's the same one every page then we can just delete it at the end 
      d = {'title':'','priceDescription':'','priceAdditionalDescriptor':'', 'suburb':'',
           'number_of_bedrooms':'','number_of_bathrooms':'','number_of_garages':'',"size":"",
           'available_from':'',"url":"",}  
           
      
      # we need an or for the available from or available now flags
      try:
        d['title']                      = i.find(['div','span'],{"class":['p24_title','p24_description']}).text 
        d['priceDescription']           =i.find(['div','span'],{"class":'p24_price'}).text.strip()
        if i.find(['div','span'],{"class":"left rentalTerm p24_rentalTerm"}):
          d['priceAdditionalDescriptor']  = i.find(['div','span'],{"class":"left rentalTerm p24_rentalTerm"}).text
        else: 
          d['priceAdditionalDescriptor'] = ""
          
        d['suburb']                     = i.find('span',{"class":"p24_location"}).text

        if i.find("span",{"class":"p24_featureDetails","title":"Bedrooms"}):
          d['number_of_bedrooms']         = i.find("span",{"class":"p24_featureDetails","title":"Bedrooms"}).text.strip()
        else: 
          d['number_of_bedrooms'] = ""
        
        if i.find("span",{"class":"p24_featureDetails","title":"Bathrooms"}):
          d['number_of_bathrooms']        = i.find("span",{"class":"p24_featureDetails","title":"Bathrooms"}).text.strip()
        else: d['number_of_bathrooms'] = ""
        
        if i.find("span",{"class":"p24_featureDetails","title":"Parking Spaces"}):
          d['number_of_garages']          = i.find("span",{"class":"p24_featureDetails","title":"Parking Spaces"}).text.strip()
        else: d['number_of_garages'] = ""
        
        if i.find("span",{"class":"p24_size"}):
          d['size'] = i.find("span",{"class":"p24_size"}).text.strip() # floor size for apartments and houses, commerical property sometimes has
                                                                      #floor size and sometimes has gross-lettable-area. could split in future if needed
        else:
          d["size"] = "" 

        if j.find('li',{"class":"p24_availableBadge"}):
          d['available_from']   = j.find('li',{"class":"p24_availableBadge"}).text
        
        else:
          d['available_from'] = ""
        
        

        
        
        d['url']              = current_url + "/" + k['data-listing-number']
         
        
      except: 
        print("exception")
      
      data.append(d) 
      counter +=1  
  return data 


  
def main_p24():
    #steps
    all_data = []
    # go to url and get throught the cookie
    driver  = go_to_next_url("https://www.property24.com/to-rent/")
    # choose the suburb from a list 
    suburbs= ("Sea Point",'Green Point',"Gardens")
    for suburb in suburbs:
        base_url = property24_search(driver,suburb)
        soup_body = make_soup(driver) 
        number_of_pages_to_search = number_of_pages(soup_body)
        other_urls_list = make_subsequent_urls(number_of_pages_to_search,base_url)

        #get info from one page 
        data = extract_listing_info(driver, soup_body)
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = make_soup(driver)
            data_next = extract_listing_info(driver,next_soup_body)
            all_data.extend(data_next)
        # go bac to the search page 
        time.sleep(5)
        driver.get('https://www.property24.com/to-rent')
        search_bar = driver.find_element(By.XPATH,'//*[@id="token-input-AutoCompleteItems"]')
        search_bar.click()
        search_bar.send_keys(Keys.BACKSPACE)
        
    driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    
    return df


