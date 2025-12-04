"""
Helper module for quantitative finance and algorithmic trading.
Provides utilities for data processing, risk management, and portfolio analytics.

Updated for Python 3.10+ compatibility with modern best practices.
"""

import pandas as pd
import numpy as np
import os
import tempfile
import zipfile
import glob
from tqdm import tqdm
import math
import requests
from typing import Union, Tuple, Optional


color_scheme = {
    'index': '#B6B2CF',
    'etf': '#2D3ECF',
    'tracking_error': '#6F91DE',
    'df_header': 'silver',
    'df_value': 'white',
    'df_line': 'silver',
    'heatmap_colorscale': [(0, '#6F91DE'), (0.5, 'grey'), (1, 'red')],
    'background_label': '#9dbdd5',
    'low_value': '#B6B2CF',
    'high_value': '#2D3ECF',
    'y_axis_2_text_color': 'grey',
    'shadow': 'rgba(0, 0, 0, 0.75)',
    'major_line': '#2D3ECF',
    'minor_line': '#B6B2CF',
    'main_line': 'black'}


def download_quandl_dataset(quandl_api_key, database, dataset, save_path, columns, tickers, start_date, end_date):
    """
    Download a dataset from Quandl and save it to `save_path`.
    Filter by columns, tickers, and date
    :param quandl_api_key: The Quandl API key
    :param database: The Quandl database to download from
    :param dataset: The dataset to download
    :param save_path: The path to save the dataset
    :param columns: The columns to save
    :param tickers: The tickers to save
    :param start_date: The rows to save that are older than this date
    :param end_date: The rows to save that are younger than this date
    """
    scrape_url = 'https://www.quandl.com/api/v3/datatables/{}/{}?qopts.export=true&api_key={}'\
        .format(database, dataset, quandl_api_key)
    scrape_request = requests.get(scrape_url)
    bulk_download_url = scrape_request.json()['datatable_bulk_download']['file']['link']

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_wiki_file = tmp_dir + 'tmp.zip'

        bulk_download_request = requests.get(bulk_download_url, stream=True, cookies=scrape_request.cookies)
        total_size = int(bulk_download_request.headers.get('content-length', 0));
        block_size = 1024 * 1024
        with open(tmp_wiki_file, 'wb') as f:
            for data in tqdm(
                    bulk_download_request.iter_content(block_size),
                    total=math.ceil(total_size // block_size),
                    unit='MB',
                    unit_scale=True,
                    desc='Downloading Data'):
                f.write(data)

        with tqdm(total=5, desc='Transforming Data', unit='Action') as pbar:
            # Unzip downloaded data
            zip_ref = zipfile.ZipFile(tmp_wiki_file, 'r')
            zip_ref.extractall(tmp_dir)
            zip_ref.close()
            pbar.update(1)

            # Check if the zip file only contains one csv file
            #   We're assuming that Quandl will always give us the data in a single csv file.
            #   If it's different, we want to throw an error.
            csv_files = glob.glob(os.path.join(tmp_dir, '*.csv'))
            assert len(csv_files) == 1,\
                'Bulk download of Quandl Wiki data failed. Wrong number of csv files found. Found {} file(s).'\
                    .format(len(csv_files))
            tmp_csv_file = csv_files[0]

            tmp_df = pd.read_csv(tmp_csv_file)
            pbar.update(1)
            tmp_df['date'] = pd.to_datetime(tmp_df['date'])
            pbar.update(1)

            # Remove unused data and save
            tmp_df = tmp_df[tmp_df['date'].isin(pd.date_range(start_date, end_date))]  # Filter unused dates
            tmp_df = tmp_df[tmp_df['ticker'].isin(tickers)]  # Filter unused tickers
            pbar.update(1)
            tmp_df.to_csv(save_path, columns=columns, index=False)  # Filter unused columns and save
            pbar.update(1)



def generate_config():
    """Generate configuration for Plotly visualizations."""
    return {'showLink': False, 'displayModeBar': False, 'showAxisRangeEntryBoxes': True}


# ==================== Risk Management Functions ====================

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 12
) -> float:
    """
    Calculate the Sharpe ratio for a returns series.
    
    Parameters
    ----------
    returns : pd.Series
        Time series of returns
    risk_free_rate : float, default=0.0
        Annual risk-free rate
    periods_per_year : int, default=12
        Number of periods per year (12 for monthly, 252 for daily)
    
    Returns
    -------
    float
        Annualized Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())


def calculate_max_drawdown(returns: pd.Series) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
    """
    Calculate maximum drawdown from returns series.
    
    Parameters
    ----------
    returns : pd.Series
        Time series of returns
    
    Returns
    -------
    tuple
        (max_drawdown, peak_date, trough_date)
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    
    max_dd = drawdown.min()
    trough_date = drawdown.idxmin()
    
    # Find the peak before the trough
    peak_date = cumulative.loc[:trough_date].idxmax()
    
    return max_dd, peak_date, trough_date


def calculate_volatility(
    prices: pd.DataFrame,
    window: int = 20,
    method: str = 'std'
) -> pd.DataFrame:
    """
    Calculate rolling volatility using different methods.
    
    Parameters
    ----------
    prices : pd.DataFrame
        Price data
    window : int, default=20
        Rolling window size
    method : str, default='std'
        Method to use: 'std' for standard deviation, 'atr' for Average True Range
    
    Returns
    -------
    pd.DataFrame
        Rolling volatility estimates
    """
    if method == 'std':
        returns = np.log(prices / prices.shift(1))
        return returns.rolling(window=window).std()
    elif method == 'atr':
        # Simplified ATR (assumes we have close prices only)
        high_low = prices.rolling(window=2).max() - prices.rolling(window=2).min()
        return high_low.rolling(window=window).mean()
    else:
        raise ValueError(f"Unknown method: {method}")


def dynamic_position_sizing(
    volatility: pd.DataFrame,
    target_vol: float = 0.15,
    max_leverage: float = 2.0
) -> pd.DataFrame:
    """
    Calculate dynamic position sizes based on volatility targeting.
    
    Parameters
    ----------
    volatility : pd.DataFrame
        Volatility estimates for each asset
    target_vol : float, default=0.15
        Target volatility level
    max_leverage : float, default=2.0
        Maximum allowed leverage
    
    Returns
    -------
    pd.DataFrame
        Position sizing multipliers
    """
    position_sizes = target_vol / (volatility + 1e-8)  # Add small epsilon to avoid division by zero
    position_sizes = position_sizes.clip(upper=max_leverage)
    return position_sizes


def calculate_rolling_metrics(
    returns: pd.Series,
    window: int = 12
) -> pd.DataFrame:
    """
    Calculate rolling performance metrics.
    
    Parameters
    ----------
    returns : pd.Series
        Time series of returns
    window : int, default=12
        Rolling window size
    
    Returns
    -------
    pd.DataFrame
        DataFrame with rolling metrics (mean, std, sharpe)
    """
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()
    rolling_sharpe = np.sqrt(12) * rolling_mean / (rolling_std + 1e-8)
    
    metrics = pd.DataFrame({
        'rolling_mean': rolling_mean,
        'rolling_std': rolling_std,
        'rolling_sharpe': rolling_sharpe
    })
    
    return metrics


# ==================== Factor Analysis Functions ====================

def calculate_market_cap_proxy(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Create a simple market cap proxy based on average price levels.
    
    In practice, you would use actual market cap data, but this provides
    a reasonable proxy for demonstration purposes based on the idea that
    larger companies tend to have higher absolute stock prices (though 
    this is imperfect due to stock splits, etc.).
    
    Parameters
    ----------
    prices : pd.DataFrame
        Price data for stocks
    
    Returns
    -------
    pd.DataFrame
        Market cap proxy (using average price as a simple proxy)
    """
    # Use rolling average price as a simple proxy
    return prices.rolling(window=60, min_periods=30).mean()


def calculate_book_to_market_proxy(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Create a simple book-to-market proxy based on inverse of past returns.
    
    The intuition: stocks with poor past performance (low returns) tend to have
    higher book-to-market ratios (value stocks), while growth stocks have lower B/M.
    
    Parameters
    ----------
    prices : pd.DataFrame
        Price data
    returns : pd.DataFrame
        Returns data
    
    Returns
    -------
    pd.DataFrame
        Book-to-market proxy
    """
    # Use inverse of cumulative returns over past year as proxy
    cumulative_returns = (1 + returns).rolling(window=12, min_periods=6).apply(lambda x: x.prod())
    # Higher values = value stocks (lower past returns)
    return 1 / (cumulative_returns + 0.1)  # Add small constant to avoid division issues


def calculate_fama_french_factors(
    returns: pd.DataFrame,
    prices: pd.DataFrame,
    n_quantiles: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Calculate Fama-French style factors: Market, SMB (Size), HML (Value).
    
    Parameters
    ----------
    returns : pd.DataFrame
        Returns for all stocks
    prices : pd.DataFrame
        Prices for all stocks
    n_quantiles : int, default=3
        Number of quantiles for sorting (3 = terciles)
    
    Returns
    -------
    tuple of pd.DataFrame
        (market_factor, smb_factor, hml_factor)
    """
    # Market factor: simple equal-weighted market return
    market_factor = returns.mean(axis=1)
    
    # SMB (Small Minus Big): Size factor
    size_proxy = calculate_market_cap_proxy(prices)
    smb_factor = pd.Series(index=returns.index, dtype=float)
    
    for date in returns.index:
        if date in size_proxy.index:
            sizes = size_proxy.loc[date].dropna()
            if len(sizes) > n_quantiles:
                small_threshold = sizes.quantile(1/n_quantiles)
                big_threshold = sizes.quantile(1 - 1/n_quantiles)
                
                small_stocks = sizes[sizes <= small_threshold].index
                big_stocks = sizes[sizes >= big_threshold].index
                
                if len(small_stocks) > 0 and len(big_stocks) > 0:
                    small_return = returns.loc[date, small_stocks].mean()
                    big_return = returns.loc[date, big_stocks].mean()
                    smb_factor.loc[date] = small_return - big_return
    
    # HML (High Minus Low): Value factor
    bm_proxy = calculate_book_to_market_proxy(prices, returns)
    hml_factor = pd.Series(index=returns.index, dtype=float)
    
    for date in returns.index:
        if date in bm_proxy.index:
            values = bm_proxy.loc[date].dropna()
            if len(values) > n_quantiles:
                value_threshold = values.quantile(1 - 1/n_quantiles)
                growth_threshold = values.quantile(1/n_quantiles)
                
                value_stocks = values[values >= value_threshold].index
                growth_stocks = values[values <= growth_threshold].index
                
                if len(value_stocks) > 0 and len(growth_stocks) > 0:
                    value_return = returns.loc[date, value_stocks].mean()
                    growth_return = returns.loc[date, growth_stocks].mean()
                    hml_factor.loc[date] = value_return - growth_return
    
    return (
        market_factor.to_frame('Market'),
        smb_factor.to_frame('SMB'),
        hml_factor.to_frame('HML')
    )


# ==================== Feature Engineering Functions ====================

def create_momentum_features(
    returns: pd.DataFrame,
    windows: list = [1, 3, 6, 12]
) -> pd.DataFrame:
    """
    Create momentum features at multiple time horizons.
    
    Parameters
    ----------
    returns : pd.DataFrame
        Returns data
    windows : list, default=[1, 3, 6, 12]
        List of lookback windows in periods
    
    Returns
    -------
    pd.DataFrame
        Feature matrix with momentum at different horizons
    """
    features = pd.DataFrame(index=returns.index)
    
    for window in windows:
        # Cumulative return over window
        cum_return = (1 + returns).rolling(window=window, min_periods=max(1, window//2)).apply(
            lambda x: x.prod() - 1, raw=False
        )
        features[f'momentum_{window}m'] = cum_return.mean(axis=1)
    
    return features


def create_technical_features(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Create technical analysis features from price data.
    
    Parameters
    ----------
    prices : pd.DataFrame
        Price data
    
    Returns
    -------
    pd.DataFrame
        Technical features
    """
    features = pd.DataFrame(index=prices.index)
    
    # Moving average crossovers
    sma_20 = prices.rolling(window=20).mean()
    sma_60 = prices.rolling(window=60).mean()
    features['ma_signal'] = ((sma_20 > sma_60).sum(axis=1) / len(prices.columns)).fillna(0)
    
    # Volatility
    returns = np.log(prices / prices.shift(1))
    features['volatility'] = returns.rolling(window=20).std().mean(axis=1)
    
    # Price momentum
    features['price_momentum'] = (prices / prices.shift(20) - 1).mean(axis=1)
    
    return features


# ==================== Transaction Cost Modeling ====================

def apply_transaction_costs(
    returns: pd.Series,
    positions: pd.DataFrame,
    cost_per_trade: float = 0.001,
    slippage: float = 0.0005
) -> pd.Series:
    """
    Apply transaction costs and slippage to returns.
    
    Parameters
    ----------
    returns : pd.Series
        Gross returns
    positions : pd.DataFrame
        Position indicators (for detecting trades)
    cost_per_trade : float, default=0.001
        Transaction cost as fraction of trade value (10 bps default)
    slippage : float, default=0.0005
        Slippage as fraction of trade value (5 bps default)
    
    Returns
    -------
    pd.Series
        Net returns after costs
    """
    # Calculate position changes (trades)
    position_changes = positions.diff().abs()
    
    # Total trading activity for each period
    trading_activity = position_changes.sum(axis=1)
    
    # Total costs
    total_costs = trading_activity * (cost_per_trade + slippage)
    
    # Apply costs to returns
    net_returns = returns - total_costs
    
    return net_returns
