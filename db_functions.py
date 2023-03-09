# I will first send it to a local postgres:
# let's see how we did that in the other project.
from sqlalchemy import create_engine
from prefect import task
import time
import pandas as pd
from datetime import timedelta
from prefect_gcp.cloud_storage import GcsBucket



@task(retries=3,log_prints=True)
def setup_connection(params,df_final):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    print(engine)
    
    df_final.to_sql(name=table_name, con=engine, if_exists='replace')



@task(retries=3,log_prints=True,cache_result_in_memory=True,cache_expiration=timedelta(days=1))
def write_locally(df_final,clean_or_raw):
    """write to a localpath"""
    
    timestr = time.strftime("%Y%m%d")
    path =f"D:\Real estate data engineering project\saved_files\Full_{clean_or_raw}_Scrape{timestr}.parquet" # this is a local file path
    df_final.to_parquet(path)
    return path

@task(retries=3,log_prints=True)
def write_to_gcp(paths:list):

    gcp_cloud_storage_bucket_block = GcsBucket.load("realeatatepush")
    
    for path in paths:
        gcp_cloud_storage_bucket_block.upload_from_path(path)

