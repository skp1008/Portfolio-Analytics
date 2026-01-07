"""
ETL Pipeline: Fetch, Clean, and Store Stock Data in Azure SQL Database
This script fetches stock data from yfinance, cleans it, and stores it in Azure SQL Database.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pyodbc
import os
from config import AZURE_SERVER, AZURE_DATABASE, AZURE_USERNAME, AZURE_PASSWORD


def fetch_multiple_stocks(ticker_list, start_date="2010-01-01"):
    """
    Fetch and clean stock data for multiple tickers using yfinance.
    
    Parameters:
    - ticker_list: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
    - start_date: Start date in YYYY-MM-DD format (default: "2010-01-01")
    
    Returns:
    - Combined long-form DataFrame with columns: Ticker, Date, Open, High, Low, Close, Volume
    """
    all_data = []
    
    for ticker_name in ticker_list:
        try:
            # Fetch stock data
            ticker = yf.Ticker(ticker_name)
            uncleaned_stock_data = ticker.history(start=start_date, end=None)
            
            if uncleaned_stock_data.empty:
                print(f"Warning: No data found for {ticker_name}")
                continue
            
            # Select only the columns we need: Open, High, Low, Close, Volume
            cleaned_data = uncleaned_stock_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            
            # Reset index to make Date a column
            cleaned_data = cleaned_data.reset_index()
            
            # Format date to YYYY-MM-DD
            cleaned_data['Date'] = cleaned_data['Date'].dt.strftime('%Y-%m-%d')
            
            # Add Ticker column
            cleaned_data['Ticker'] = ticker_name
            
            # Reorder columns: Ticker, Date, Open, High, Low, Close, Volume
            cleaned_data = cleaned_data[['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Reset index to remove default integer index
            cleaned_data = cleaned_data.reset_index(drop=True)
            
            all_data.append(cleaned_data)
            print(f"Successfully fetched {len(cleaned_data)} records for {ticker_name}")
            
        except Exception as e:
            print(f"Error fetching data for {ticker_name}: {str(e)}")
            continue
    
    if not all_data:
        print("No data was fetched for any ticker")
        return pd.DataFrame()
    
    # Combine all dataframes
    combined_data = pd.concat(all_data, ignore_index=True)
    
    return combined_data


def get_azure_connection():
    """
    Create and return a connection to Azure SQL Database.
    """
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={AZURE_SERVER};"
        f"Database={AZURE_DATABASE};"
        f"Uid={AZURE_USERNAME};"
        f"Pwd={AZURE_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to Azure SQL Database: {str(e)}")
        raise


def create_stock_data_table(conn):
    """
    Create the stock_data table if it doesn't exist.
    """
    cursor = conn.cursor()
    
    create_table_query = """
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[stock_data]') AND type in (N'U'))
    BEGIN
        CREATE TABLE stock_data (
            id INT IDENTITY(1,1) PRIMARY KEY,
            Ticker NVARCHAR(10) NOT NULL,
            Date DATE NOT NULL,
            Open FLOAT NOT NULL,
            High FLOAT NOT NULL,
            Low FLOAT NOT NULL,
            Close FLOAT NOT NULL,
            Volume BIGINT NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            UNIQUE(Ticker, Date)
        );
        CREATE INDEX idx_ticker_date ON stock_data(Ticker, Date);
    END
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    print("Table 'stock_data' is ready")


def store_data_in_azure(df, conn):
    """
    Store cleaned stock data in Azure SQL Database.
    Uses MERGE to update existing records or insert new ones.
    """
    if df.empty:
        print("No data to store")
        return
    
    cursor = conn.cursor()
    
    # Prepare data for bulk insert
    records = []
    for _, row in df.iterrows():
        records.append((
            row['Ticker'],
            row['Date'],
            float(row['Open']),
            float(row['High']),
            float(row['Low']),
            float(row['Close']),
            int(row['Volume'])
        ))
    
    # Use MERGE to handle duplicates
    merge_query = """
    MERGE stock_data AS target
    USING (VALUES (?, ?, ?, ?, ?, ?, ?)) AS source (Ticker, Date, Open, High, Low, Close, Volume)
    ON target.Ticker = source.Ticker AND target.Date = source.Date
    WHEN MATCHED THEN
        UPDATE SET 
            Open = source.Open,
            High = source.High,
            Low = source.Low,
            Close = source.Close,
            Volume = source.Volume
    WHEN NOT MATCHED THEN
        INSERT (Ticker, Date, Open, High, Low, Close, Volume)
        VALUES (source.Ticker, source.Date, source.Open, source.High, source.Low, source.Close, source.Volume);
    """
    
    try:
        cursor.executemany(merge_query, records)
        conn.commit()
        print(f"Successfully stored/updated {len(records)} records in Azure SQL Database")
    except Exception as e:
        conn.rollback()
        print(f"Error storing data: {str(e)}")
        raise
    finally:
        cursor.close()


def run_etl_pipeline(ticker_list=None, start_date="2010-01-01"):
    """
    Main ETL pipeline function.
    Fetches data, cleans it, and stores it in Azure SQL Database.
    """
    # Default ticker list if none provided
    if ticker_list is None:
        ticker_list = ["AMZN", "AAPL", "META", "NVDA", "GOOGL", "MSFT", "TSLA", "NFLX", "ADBE", "ORCL"]
    
    print(f"Starting ETL pipeline for {len(ticker_list)} tickers...")
    print(f"Tickers: {', '.join(ticker_list)}")
    
    # Step 1: Fetch and clean data
    print("\nStep 1: Fetching and cleaning stock data...")
    stock_data = fetch_multiple_stocks(ticker_list, start_date)
    
    if stock_data.empty:
        print("No data was fetched. Exiting pipeline.")
        return
    
    print(f"Total records fetched: {len(stock_data)}")
    
    # Step 2: Connect to Azure and create table
    print("\nStep 2: Connecting to Azure SQL Database...")
    conn = get_azure_connection()
    create_stock_data_table(conn)
    
    # Step 3: Store data in Azure
    print("\nStep 3: Storing data in Azure SQL Database...")
    store_data_in_azure(stock_data, conn)
    
    # Close connection
    conn.close()
    print("\nETL pipeline completed successfully!")


if __name__ == "__main__":
    # Run the ETL pipeline
    run_etl_pipeline()

