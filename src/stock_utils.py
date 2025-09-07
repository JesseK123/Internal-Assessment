"""
Stock-related utility functions
"""

import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from urllib.parse import quote
from constants import STOCK_SYMBOLS_BY_COUNTRY


def preprocess_stock_dataframe(data):
    """Standardize stock dataframe preprocessing"""
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    return data


def get_company_news_link(symbol):
    """Get Google News search link for a company"""
    try:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            company_name = info.get('longName', symbol)
        except:
            company_name = symbol
        
        search_query = f"{company_name} {symbol} stock"
        encoded_query = quote(search_query)
        google_news_url = f"https://news.google.com/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        return {
            'company_name': company_name,
            'symbol': symbol,
            'search_query': search_query,
            'news_url': google_news_url
        }
        
    except Exception as e:
        st.error(f"Error generating news link: {str(e)}")
        return None


@st.cache_data(ttl=86400)
def get_stock_data(symbol, days):
    """Fetch stock data with caching"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        data = preprocess_stock_dataframe(data)
        
        return data
    except Exception as e:
        st.error(f"Failed to fetch data for {symbol}: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=86400)
def get_historical_stock_data(symbol, start_year=2000):
    """Fetch long-term historical stock data from specified start year"""
    try:
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now()
        
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        data = preprocess_stock_dataframe(data)
        
        return data
    except Exception as e:
        st.error(f"Failed to fetch historical data for {symbol}: {str(e)}")
        return pd.DataFrame()


def get_stock_info_with_history(symbol):
    """Get stock info including historical data from 2000s"""
    try:
        ticker = yf.Ticker(symbol)
        
        info = ticker.info
        
        historical_data = get_historical_stock_data(symbol, 2000)
        
        recent_data = ticker.history(period="2d")
        
        stock_info = {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "historical_data": historical_data,
            "info": info
        }
        
        if not recent_data.empty and len(recent_data) >= 2:
            current_price = float(recent_data['Close'].iloc[-1])
            previous_price = float(recent_data['Close'].iloc[-2])
            change = current_price - previous_price
            
            stock_info.update({
                "price": current_price,
                "change": change,
                "previous_price": previous_price
            })
        
        return stock_info
        
    except Exception as e:
        st.error(f"Failed to fetch complete info for {symbol}: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def get_stocks_for_search(country):
    """Fetch current stock data for search results"""
    if country not in STOCK_SYMBOLS_BY_COUNTRY:
        return []
    
    symbols = STOCK_SYMBOLS_BY_COUNTRY[country]
    stock_data = []
    
    try:
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_string = " ".join(batch)
            
            try:
                tickers = yf.Tickers(batch_string)
                
                for symbol in batch:
                    try:
                        ticker = tickers.tickers[symbol]
                        info = ticker.info
                        hist = ticker.history(period="2d")
                        
                        if not hist.empty and len(hist) >= 2:
                            current_price = float(hist['Close'].iloc[-1])
                            previous_price = float(hist['Close'].iloc[-2])
                            change = current_price - previous_price
                            
                            stock_data.append({
                                "symbol": symbol,
                                "name": info.get('longName', info.get('shortName', symbol)),
                                "price": current_price,
                                "change": change,
                                "country": country
                            })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
                
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
    
    return stock_data


@st.cache_data(ttl=86400)
def get_multiple_stocks_data(symbols, days):
    """Fetch data for multiple stocks"""
    stock_data = {}
    for symbol in symbols:
        try:
            data = get_stock_data(symbol, days)
            if isinstance(data, pd.DataFrame) and not data.empty:
                stock_data[symbol] = data
        except Exception as e:
            continue
    return stock_data