import numpy as np
from datetime import date
import pandas as pd

def house_type_categories(df):
    """Make categorical column for building type"""
    mask_apt = df['title'].str.contains("Apartment|apartment|flat|Flat")
    mask_house = df['title'].str.contains("house|House")
    mask_commercial = df['title'].str.contains("commercial|Commercial")
    mask_industrial = df['title'].str.contains("industrial|Industrial")
    
    df['building type'] = np.select([mask_apt,mask_house,mask_commercial,mask_industrial],["apartment",'house','commercial property','industrial property'])
    return df

def available_date_cleaner_ht(df):
    
    full_index = list(df.index)
    now_index = list(df.loc[df['available_from'].str.contains("NOW",na=False),"available_from"].index)
    other_index = set(full_index) - set(now_index)
    
    df["available_from"]= df["available_from"].str.strip(" AVAILABLE:")
    df.loc[now_index,"available_from"] = date.today()
    df.loc[other_index,"available_from"] = df.loc[other_index,"available_from"] + " 2023"
    df.loc[other_index,"available_from"] = pd.to_datetime(df.loc[other_index,"available_from"], format = "%d %b %Y",errors='coerce').dt.date
    return df

def num_column_cleaner(df):
    df.loc[df['priceDescription'].str.contains("POA"), 'priceAdditionalDescriptor'] = df['priceAdditionalDescriptor'] + ' POA'
    # check if this POA was solved in the next iteration, i changed the Nones to be """
    df.loc[df['priceDescription'].str.contains("POA"),'priceDescription'] = "0" 

    df['priceDescription'] = df['priceDescription'].str.replace(" ","")
    df['priceDescription'] = df['priceDescription'].str.replace("R","")
    df['priceDescription'] = df['priceDescription'].str.replace("\nperday","")
    df['priceDescription'] = df['priceDescription'].str.replace("\nperm²","").astype("int",errors="ignore")
    df["number_of_bedrooms"]=pd.to_numeric(df['number_of_bedrooms'], errors='coerce').fillna(0)
    df["number_of_bathrooms"]=pd.to_numeric(df['number_of_bathrooms'], errors='coerce').fillna(0)
    df["number_of_garages"]=pd.to_numeric(df['number_of_garages'], errors='coerce').fillna(0)
    
    df["size"] =df["size"].str.strip(" m²").str.replace(" ","")
    df["size"] = pd.to_numeric(df["size"],errors = "coerce").fillna(0)
    return df

def available_date_cleaner_p24(df)->pd.DataFrame:
    full_index = list(df.index)
    now_index = list(df.loc[df['available_from'].str.contains("NOW",na=False),"available_from"].index)
    other_index = set(full_index) - set(now_index)
    
    df["available_from"]= df["available_from"].str.strip("AVAILABLE:")
    df.loc[now_index,"available_from"] = date.today()
    df.loc[other_index,"available_from"] = df.loc[other_index,"available_from"] + " 2023"
    df.loc[other_index,"available_from"] = pd.to_datetime(df.loc[other_index,"available_from"], format = "%d %b %Y",errors='coerce').dt.date
    return df

def available_date_cleaner_pp(df)->pd.DataFrame:
    full_index = list(df.index)
    now_index = list(df.loc[df['available_from'].str.contains("Now",na=False),"available_from"].index)
    other_index = set(full_index) - set(now_index)
    
    df["available_from"]= df["available_from"].str.strip("AVAILABLE FROM: ")
    df.loc[now_index,"available_from"] = date.today()
    df.loc[other_index,"available_from"] = pd.to_datetime(df.loc[other_index,"available_from"], format = "%d %b %Y",errors='coerce').dt.date
    return df