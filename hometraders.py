import re
import pandas as pd
import time 


suburbs_url_dict = {
                    "Sea Point":"https://www.sahometraders.co.za/property-to-rent-in-sea-point-s11021",
                    "Gardens":"https://www.sahometraders.co.za/property-to-rent-in-gardens-s9145",
                    "Green Point": "https://www.sahometraders.co.za/property-to-rent-in-green-point-s11017"
                    }


def number_of_pages_ht(body_soup):
    """"find the number of listed places in the search to figure out how many pages to crawl"""
    listingcount_options = body_soup.find("div",{'class':"sc_pageText"})
    
    
    split_counts = re.findall('\d+',listingcount_options.text)
    
    this_page = int(split_counts[1])
    total_listings = int(split_counts[-1])
    pages_to_search = -(-total_listings//this_page)
    return pages_to_search



def make_subsequent_urls_ht(page_count,base_url):
    urls_list = []
    for i in range(2,page_count+1):
        # i will be our page numbers to shoot into the url. 
        next_url = base_url + f"?Page={i}"
        urls_list.append(next_url) 
    return urls_list




def extract_listing_info_ht(soup_body):
  """ Extract info from all listings on one page of hometraders
      
  """
  data = []
    

  # FIND ALL listings 
  info_of_listings = soup_body.find_all(['div',"span","a"],{'class',"p24_content"}) # seems to be only span, but will just leave the divs and a there 
  image_info = soup_body.find_all(['span','div'],{"class":"js_listingTileImageHolder"}) # need to find a waty to get rid of the duplicate
  url_info =soup_body.find_all("div",{'class':"p24_regularTile"}) # get the href out of there
  # so far no promoted tiles, unlike P24
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
        d['title']                      = i.find(['span'],{"class":'p24_propertyTitle'}).text 
        d['priceDescription']           =i.find('span',{"class":'p24_price'}).text.strip()
        if i.find('span',{"class":"left rentalTerm p24_rentalTerm"}): 
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
        
        

        
        
        d['url']              = "https://www.sahometraders.co.za" + k.find('a')["href"]
         
        
      except Exception as e: 
        print(e)
      data.append(d) 
      counter +=1  
  return data 


def main_ht():
    #steps
    all_data = []
    # go to url and get throught the cookie
    driver  = setup_driver()
    # choose the suburb from a list 
    suburbs= ("Sea Point",'Green Point',"Gardens")
    suburbs_url_dict = {
                    "Sea Point":"https://www.sahometraders.co.za/property-to-rent-in-sea-point-s11021",
                    "Gardens":"https://www.sahometraders.co.za/property-to-rent-in-gardens-s9145",
                    "Green Point": "https://www.sahometraders.co.za/property-to-rent-in-green-point-s11017"
                    }
    for suburb in suburbs:
        base_url = suburbs_url_dict[suburb]
        time.sleep(4)
        driver.get(base_url)
        soup_body = make_soup(driver) 
        number_of_pages_to_search = number_of_pages_ht(soup_body)
        other_urls_list = make_subsequent_urls_ht(number_of_pages_to_search,base_url)

        #get info from one page 
        data = extract_listing_info_ht(soup_body)
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = make_soup(driver)
            data_next = extract_listing_info_ht(next_soup_body)
            all_data.extend(data_next)
        
        time.sleep(5)
        
        
    driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    
    return df



