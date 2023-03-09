import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import argparse
import pandas as pd
import Property24 as p24
import privateproperty as pp
import hometraders as ht
from db_functions import setup_connection,write_locally
from prefect import task, flow
from prefect.tasks import task_input_hash
import cleaning_functions as clean 
from db_functions import write_to_gcp



@task(retries=3,log_prints=True,cache_key_fn=task_input_hash)
def main_privatep(driver):
    #steps
    all_data = []
    # go to url and get throught the cookie
    # driver  = pp.setup_driver()
    driver = pp.privatep_search(driver)
    # choose the suburb from a list 
    suburbs= ("Sea Point",'Green Point',"Gardens")
    for suburb in suburbs:
        
        base_url,driver = pp.search_privatep(driver,suburb)
        soup_body = pp.make_soup_body(driver) 
        number_of_pages_to_search = pp.count_pages_privatep(soup_body)
        other_urls_list = pp.subsequent_urls_privatep(number_of_pages_to_search,base_url)

        #get info from one page 
        data = pp.extract_listing_info_privatep(soup_body)
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = pp.make_soup_body(driver)
            data_next = pp.extract_listing_info_privatep(next_soup_body)
            all_data.extend(data_next)
        # go bac to the search page 
        time.sleep(5)
        driver.get('https://www.privateproperty.co.za/to-rent')
    #driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    print("The shape of the df",df.shape)
    print("The drivertype: ",type(driver))
    return df

@task(retries=3,log_prints=True,cache_key_fn=task_input_hash)
def main_p24(driver):
    #steps
    all_data = []
    # go to url and get throught the cookie
    driver  = p24.go_to_next_url(driver,"https://www.property24.com/to-rent")
    # choose the suburb from a list 
    suburbs= ("Sea Point",'Green Point',"Gardens")
    for suburb in suburbs:
        base_url = p24.property24_search(driver,suburb)
        soup_body = pp.make_soup_body(driver) 
        number_of_pages_to_search = p24.count_pages_p24(soup_body)
        other_urls_list = p24.subsequent_urls_p24(number_of_pages_to_search,base_url)

        #get info from one page 
        data = p24.extract_listing_info_p24(driver, soup_body,base_url)
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = pp.make_soup_body(driver)
            data_next = p24.extract_listing_info_p24(driver,next_soup_body,base_url)
            all_data.extend(data_next)
        # go back to the search page 
        time.sleep(5)
        driver.get('https://www.property24.com/to-rent')
        search_bar = driver.find_element(By.XPATH,'//*[@id="token-input-AutoCompleteItems"]')
        search_bar.click()
        search_bar.send_keys(Keys.BACKSPACE)
        
    #driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    
    return df

@task(retries=3,log_prints=True,cache_key_fn=task_input_hash)
def main_ht(driver):
    #steps
    all_data = []
    
    
     
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
        soup_body = pp.make_soup_body(driver) 
        number_of_pages_to_search = ht.number_of_pages_ht(soup_body)
        other_urls_list = ht.make_subsequent_urls_ht(number_of_pages_to_search,base_url)

        #get info from one page 
        data = ht.extract_listing_info_ht(soup_body)
        all_data.extend(data)
        
        for url in other_urls_list:
            driver.get(url)
            next_soup_body  = pp.make_soup_body(driver)
            data_next = ht.extract_listing_info_ht(next_soup_body)
            all_data.extend(data_next)
        
        time.sleep(5)
        
        
    driver.close()
    df = pd.DataFrame(all_data,index = range(len(all_data)))
    
    return df
@flow()
def main_flow():

    driver = pp.setup_driver()
    df1 = main_privatep(driver)
    df2 =   main_p24(driver)
    df3 = main_ht(driver)
    print("DF1HEAD:",df1.head(),"DF2HEAD:",df2.head(),"DF3HEAD:",df3.head())
    # clean pp
    pp_clean = clean.house_type_categories(df1)
    pp_clean = clean.num_column_cleaner(pp_clean)  
    pp_clean = clean.available_date_cleaner_pp(pp_clean)
    # clean p24
    p24_clean = clean.house_type_categories(df2)
    p24_clean = clean.num_column_cleaner(p24_clean)  
    p24_clean = clean.available_date_cleaner_pp(p24_clean)
    # clean HT
    ht_clean = clean.house_type_categories(df3)
    ht_clean = clean.num_column_cleaner(ht_clean)
    ht_clean = clean.available_date_cleaner_ht(ht_clean)
    
    frames = [pp_clean, p24_clean, ht_clean]
    raw_frames = [df1,df2,df3]
    raw_df = pd.concat(raw_frames)
    final_df = pd.concat(frames)

    parser = argparse.ArgumentParser(description='Ingest Api data to Postgres')

    parser.add_argument('--user', required=True, help='user name for postgres')
    parser.add_argument('--password', required=True, help='password for postgres')
    parser.add_argument('--host', required=True, help='host for postgres')
    parser.add_argument('--port', required=True, help='port for postgres')
    parser.add_argument('--db', required=True, help='database name for postgres')
    parser.add_argument('--table_name', required=True, help='name of the table where we will write the results to')
    
    # could also make a block for this on prefect
    # def postrges_credentials():

    args = parser.parse_args()

    setup_connection(args,final_df)
    path_raw = write_locally(raw_df,'raw')
    path_clean = write_locally(final_df,'clean')
    write_to_gcp([path_raw,path_clean])

if __name__ == "__main__":
    main_flow()
    

#this command is used in the command line 
#python final_scraper.py --user=root --password=root --host=localhost --port=5432 --db=real_estate --table_name=first_try

 

 



