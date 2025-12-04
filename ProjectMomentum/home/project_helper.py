"""
Project helper module for visualization and display functions.
Updated with modern Plotly visualizations and interactive charts.

Compatible with Python 3.10+ and Plotly 5.x
"""

import helper
import plotly.graph_objs as go
import plotly.offline as offline_py
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

offline_py.init_notebook_mode(connected=True)


def _generate_stock_trace(prices):
    return go.Scatter(
        name='Index',
        x=prices.index,
        y=prices,
        line={'color': helper.color_scheme['major_line']})


def _generate_traces(name_df_color_data):
    traces = []

    for name, df, color in name_df_color_data:
        traces.append(go.Scatter(
            name=name,
            x=df.index,
            y=df,
            mode='line',
            line={'color': color}))

    return traces


def plot_stock(prices, title):
    config = helper.generate_config()
    layout = go.Layout(title=title)

    stock_trace = _generate_stock_trace(prices)

    offline_py.iplot({'data': [stock_trace], 'layout': layout}, config=config)


def print_dataframe(df, n_rows=10, n_columns=3):
    missing_val_str = '...'
    config = helper.generate_config()

    formatted_df = df.iloc[:n_rows, :n_columns]
    formatted_df = formatted_df.applymap('{:.3f}'.format)

    if len(df.columns) > n_columns:
        formatted_df[missing_val_str] = [missing_val_str]*len(formatted_df.index)
    if len(df.index) > n_rows:
        formatted_df.loc[missing_val_str] = [missing_val_str]*len(formatted_df.columns)

    trace = go.Table(
        type='table',
        columnwidth=[1, 3],
        header={
            'values': [''] + list(formatted_df.columns.values),
            'line': {'color': helper.color_scheme['df_line']},
            'fill': {'color': helper.color_scheme['df_header']},
            'font': {'size': 13}},
        cells={
            'values': formatted_df.reset_index().values.T,
            'line': {'color': helper.color_scheme['df_line']},
            'fill': {'color': [helper.color_scheme['df_header'], helper.color_scheme['df_value']]},
            'font': {'size': 13}})

    offline_py.iplot([trace], config=config)


def plot_resampled_prices(df_resampled, df, title):
    config = helper.generate_config()
    layout = go.Layout(title=title)

    traces = _generate_traces([
        ('Monthly Close', df_resampled, helper.color_scheme['major_line']),
        ('Close', df, helper.color_scheme['minor_line'])])

    offline_py.iplot({'data': traces, 'layout': layout}, config=config)


def plot_returns(returns, title):
    config = helper.generate_config()
    layout = go.Layout(title=title)

    traces = _generate_traces([
        ('Returns', returns, helper.color_scheme['major_line'])])

    offline_py.iplot({'data': traces, 'layout': layout}, config=config)


def plot_shifted_returns(df_shited, df, title):
    config = helper.generate_config()
    layout = go.Layout(title=title)

    traces = _generate_traces([
        ('Shifted Returns', df_shited, helper.color_scheme['major_line']),
        ('Returns', df, helper.color_scheme['minor_line'])])

    offline_py.iplot({'data': traces, 'layout': layout}, config=config)



def print_top(df, name, top_n=10):
    """Print top N stocks by a given criterion."""
    print('{} Most {}:'.format(top_n, name))
    print(', '.join(df.sum().sort_values(ascending=False).index[:top_n].values.tolist()))


# ==================== Modern Visualization Functions ====================

def plot_drawdown(returns, title='Portfolio Drawdown'):
    """
    Plot cumulative returns with drawdown visualization.
    
    Parameters
    ----------
    returns : pd.Series
        Time series of returns
    title : str
        Chart title
    """
    config = helper.generate_config()
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Cumulative Returns', 'Drawdown'),
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4]
    )
    
    # Cumulative returns
    fig.add_trace(
        go.Scatter(
            x=cumulative.index,
            y=cumulative,
            name='Cumulative Returns',
            line=dict(color=helper.color_scheme['major_line'], width=2)
        ),
        row=1, col=1
    )
    
    # Drawdown
    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown * 100,
            name='Drawdown %',
            fill='tozeroy',
            line=dict(color='red', width=1)
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Cumulative Return", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    offline_py.iplot(fig, config=config)


def plot_rolling_metrics(metrics_df, title='Rolling Performance Metrics'):
    """
    Plot rolling performance metrics (Sharpe, volatility, returns).
    
    Parameters
    ----------
    metrics_df : pd.DataFrame
        DataFrame with rolling metrics
    title : str
        Chart title
    """
    config = helper.generate_config()
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Rolling Returns', 'Rolling Volatility', 'Rolling Sharpe Ratio'),
        vertical_spacing=0.08,
        row_heights=[0.33, 0.33, 0.34]
    )
    
    # Rolling returns
    if 'rolling_mean' in metrics_df.columns:
        fig.add_trace(
            go.Scatter(
                x=metrics_df.index,
                y=metrics_df['rolling_mean'] * 100,
                name='Mean Return %',
                line=dict(color=helper.color_scheme['major_line'], width=2)
            ),
            row=1, col=1
        )
    
    # Rolling volatility
    if 'rolling_std' in metrics_df.columns:
        fig.add_trace(
            go.Scatter(
                x=metrics_df.index,
                y=metrics_df['rolling_std'] * 100,
                name='Volatility %',
                line=dict(color='orange', width=2)
            ),
            row=2, col=1
        )
    
    # Rolling Sharpe
    if 'rolling_sharpe' in metrics_df.columns:
        fig.add_trace(
            go.Scatter(
                x=metrics_df.index,
                y=metrics_df['rolling_sharpe'],
                name='Sharpe Ratio',
                line=dict(color='green', width=2)
            ),
            row=3, col=1
        )
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=3, col=1)
    
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Return %", row=1, col=1)
    fig.update_yaxes(title_text="Volatility %", row=2, col=1)
    fig.update_yaxes(title_text="Sharpe Ratio", row=3, col=1)
    
    fig.update_layout(
        title=title,
        height=800,
        showlegend=False,
        hovermode='x unified'
    )
    
    offline_py.iplot(fig, config=config)


def plot_factor_comparison(factor_returns, title='Factor Performance Comparison'):
    """
    Compare performance of different factors.
    
    Parameters
    ----------
    factor_returns : dict
        Dictionary of {factor_name: returns_series}
    title : str
        Chart title
    """
    config = helper.generate_config()
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Date'),
        yaxis=dict(title='Cumulative Return'),
        hovermode='x unified'
    )
    
    traces = []
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for idx, (name, returns) in enumerate(factor_returns.items()):
        cumulative = (1 + returns).cumprod()
        traces.append(go.Scatter(
            name=name,
            x=cumulative.index,
            y=cumulative,
            mode='lines',
            line=dict(color=colors[idx % len(colors)], width=2)
        ))
    
    offline_py.iplot({'data': traces, 'layout': layout}, config=config)


def plot_feature_importance(importances, feature_names, title='Feature Importance'):
    """
    Plot feature importance from ML model.
    
    Parameters
    ----------
    importances : array-like
        Feature importance values
    feature_names : list
        Names of features
    title : str
        Chart title
    """
    config = helper.generate_config()
    
    # Sort by importance
    indices = np.argsort(importances)[::-1]
    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]
    
    fig = go.Figure(data=[
        go.Bar(
            x=sorted_importances,
            y=sorted_features,
            orientation='h',
            marker=dict(
                color=sorted_importances,
                colorscale='Viridis',
                showscale=True
            )
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title='Importance',
        yaxis_title='Feature',
        height=max(400, len(feature_names) * 30),
        showlegend=False
    )
    
    offline_py.iplot(fig, config=config)


def plot_returns_distribution(returns, title='Returns Distribution'):
    """
    Plot distribution of returns with statistical annotations.
    
    Parameters
    ----------
    returns : pd.Series
        Returns series
    title : str
        Chart title
    """
    config = helper.generate_config()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Histogram', 'Q-Q Plot vs Normal'),
        column_widths=[0.6, 0.4]
    )
    
    # Histogram
    fig.add_trace(
        go.Histogram(
            x=returns,
            name='Returns',
            nbinsx=50,
            marker=dict(color=helper.color_scheme['major_line']),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add normal distribution overlay
    from scipy import stats
    mu, sigma = returns.mean(), returns.std()
    x = np.linspace(returns.min(), returns.max(), 100)
    y = stats.norm.pdf(x, mu, sigma) * len(returns) * (returns.max() - returns.min()) / 50
    
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            name='Normal Distribution',
            line=dict(color='red', dash='dash')
        ),
        row=1, col=1
    )
    
    # Q-Q plot
    qq_data = stats.probplot(returns.dropna(), dist="norm")
    fig.add_trace(
        go.Scatter(
            x=qq_data[0][0],
            y=qq_data[0][1],
            mode='markers',
            name='Q-Q Plot',
            marker=dict(color=helper.color_scheme['major_line']),
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Add reference line for Q-Q plot
    fig.add_trace(
        go.Scatter(
            x=qq_data[0][0],
            y=qq_data[1][0] * qq_data[0][0] + qq_data[1][1],
            mode='lines',
            name='Reference Line',
            line=dict(color='red', dash='dash'),
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="Returns", row=1, col=1)
    fig.update_xaxes(title_text="Theoretical Quantiles", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_yaxes(title_text="Sample Quantiles", row=1, col=2)
    
    fig.update_layout(
        title=title,
        height=400,
        showlegend=True
    )
    
    offline_py.iplot(fig, config=config)


def plot_portfolio_comparison(portfolios_dict, title='Portfolio Comparison'):
    """
    Compare multiple portfolio strategies.
    
    Parameters
    ----------
    portfolios_dict : dict
        Dictionary of {strategy_name: returns_series}
    title : str
        Chart title
    """
    config = helper.generate_config()
    
    traces = []
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    for idx, (name, returns) in enumerate(portfolios_dict.items()):
        cumulative = (1 + returns).cumprod()
        traces.append(go.Scatter(
            name=name,
            x=cumulative.index,
            y=cumulative,
            mode='lines',
            line=dict(color=colors[idx % len(colors)], width=2),
            hovertemplate='%{y:.4f}<extra></extra>'
        ))
    
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Date'),
        yaxis=dict(title='Cumulative Return', tickformat='.2f'),
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    offline_py.iplot({'data': traces, 'layout': layout}, config=config)
