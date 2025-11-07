"""
Visualizer - creates charts for unified ZERA price history
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict
import config
import os


def plot_candlesticks(ax, df, color='#4ECDC4', alpha=0.8):
    """
    Plot candlestick chart on given axes

    Args:
        ax: Matplotlib axes object
        df: DataFrame with columns: date, open, high, low, close
        color: Base color for candlesticks
        alpha: Transparency
    """
    # Calculate candlestick width based on data density
    if len(df) > 1:
        avg_timedelta = (df['date'].iloc[-1] - df['date'].iloc[0]) / len(df)
        candle_width = avg_timedelta * 0.6  # 60% of period for candle body
    else:
        candle_width = timedelta(days=0.6)

    for idx, row in df.iterrows():
        date = row['date']
        open_price = row['open']
        high = row['high']
        low = row['low']
        close = row['close']

        # Determine if bullish (green) or bearish (red)
        is_bullish = close >= open_price
        body_color = '#26a69a' if is_bullish else '#ef5350'  # Green/Red

        # Draw high-low wick (thin line)
        ax.plot([date, date], [low, high],
                color=body_color, linewidth=1, alpha=alpha, zorder=1)

        # Draw body (rectangle from open to close)
        body_height = abs(close - open_price)
        body_bottom = min(open_price, close)

        if body_height > 0:
            rect = Rectangle((mdates.date2num(date) - candle_width.total_seconds()/(2*86400), body_bottom),
                           candle_width.total_seconds()/86400, body_height,
                           facecolor=body_color, edgecolor=body_color,
                           alpha=alpha, linewidth=0.5, zorder=2)
            ax.add_patch(rect)
        else:
            # Doji (open == close) - draw thin horizontal line
            ax.plot([mdates.date2num(date) - candle_width.total_seconds()/(2*86400),
                    mdates.date2num(date) + candle_width.total_seconds()/(2*86400)],
                   [close, close], color=body_color, linewidth=1.5, alpha=alpha, zorder=2)


def find_local_peaks(df: pd.DataFrame, window=5, prominence_threshold=0.1):
    """
    Find significant local peaks in the price data

    Args:
        df: DataFrame with 'high' and 'date' columns
        window: Window size for peak detection
        prominence_threshold: Relative prominence threshold (0-1)

    Returns:
        List of (date, high_price) tuples for peaks
    """
    if len(df) < window * 2:
        return []

    peaks = []
    highs = df['high'].values
    dates = df['date'].values

    # Calculate relative prominence threshold
    price_range = highs.max() - highs.min()
    min_prominence = price_range * prominence_threshold

    for i in range(window, len(highs) - window):
        # Check if current point is higher than neighbors
        is_peak = all(highs[i] >= highs[i-window:i]) and all(highs[i] >= highs[i+1:i+window+1])

        if is_peak:
            # Check prominence (how much higher than surrounding area)
            left_min = min(highs[max(0, i-window):i])
            right_min = min(highs[i+1:min(len(highs), i+window+1)])
            prominence = highs[i] - max(left_min, right_min)

            if prominence >= min_prominence:
                peaks.append((dates[i], highs[i]))

    return peaks


def create_price_chart(df: pd.DataFrame, output_path: str = None):
    """
    Create a comprehensive price chart with migration markers

    Args:
        df: Unified DataFrame with price history
        output_path: Path to save the chart (optional)
    """
    # Set up the figure with multiple subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10),
                                     gridspec_kw={'height_ratios': [3, 1]})
    fig.suptitle('ZERA Token - Complete Price History (M0N3Y → ZERA)',
                 fontsize=16, fontweight='bold')

    # Color mapping for different pools
    pool_colors = {
        'mon3y': '#FF6B6B',      # Red for M0N3Y
        'zera_Raydium': '#4ECDC4', # Teal for ZERA Raydium
        'zera_Meteora': '#45B7D1'  # Blue for ZERA Meteora
    }

    # Migration timestamps for filtering
    migration_1 = datetime.fromtimestamp(config.MIGRATION_DATES['mon3y_to_zera'])
    migration_2 = datetime.fromtimestamp(config.MIGRATION_DATES['zera_Raydium_to_Meteora'])

    # Plot 1: Candlestick chart
    # Plot each pool's real data as candlesticks
    real_df = df[~df.get('is_interpolated', False)].copy()

    # Track which pools were plotted for legend
    plotted_pools = []

    for pool_name in real_df['pool_name'].unique():
        pool_df = real_df[real_df['pool_name'] == pool_name].copy()

        # Cut off old pools BEFORE migration (new pools start AT migration)
        if pool_name == 'mon3y':
            # M0N3Y ends BEFORE ZERA Raydium starts (exclude migration date)
            pool_df = pool_df[pool_df['date'] < migration_1]
        elif pool_name == 'zera_Raydium':
            # ZERA Raydium starts at migration_1, ends BEFORE Meteora starts
            pool_df = pool_df[pool_df['date'] < migration_2]
        # Meteora has no cutoff (it's current, starts at migration_2)

        if len(pool_df) > 0:
            # Plot candlesticks for this pool
            plot_candlesticks(ax1, pool_df, color=pool_colors.get(pool_name, '#333333'), alpha=0.9)
            plotted_pools.append((pool_name, pool_colors.get(pool_name, '#333333')))

            # Find and mark local peaks (highs) for this pool
            peaks = find_local_peaks(pool_df, window=5, prominence_threshold=0.15)
            for peak_date, peak_high in peaks:
                # Add arrow pointing to the peak
                ax1.annotate('', xy=(peak_date, peak_high),
                           xytext=(peak_date, peak_high * 1.08),
                           arrowprops=dict(arrowstyle='->', color='#FF4444',
                                         lw=1.5, alpha=0.7),
                           zorder=10)
                # Add price label
                ax1.text(peak_date, peak_high * 1.10, f'${peak_high:.4f}',
                        ha='center', va='bottom', fontsize=7, color='#FF4444',
                        weight='bold', alpha=0.8)

    # Add migration markers with transition labels
    for event_name, timestamp in config.MIGRATION_DATES.items():
        migration_date = datetime.fromtimestamp(timestamp)
        ax1.axvline(x=migration_date, color='#666666', linestyle='--',
                   linewidth=1, alpha=0.6, zorder=0)

        # Create transition label from event name
        if 'mon3y_to_zera' in event_name:
            label = 'MON3Y → Raydium'
        elif 'Raydium_to_Meteora' in event_name:
            label = 'Raydium → Meteora'
        else:
            label = event_name.replace('_', ' → ')

        # Place label at top of chart, centered on line
        ax1.text(migration_date, ax1.get_ylim()[1] * 0.98, label,
                ha='center', va='top', fontsize=8, color='#666666',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor='#666666', alpha=0.8, linewidth=0.5))

    # Create custom legend with simple names
    legend_elements = []

    # Simple label mapping
    simple_labels = {
        'mon3y': 'MON3Y',
        'zera_Raydium': 'Raydium',
        'zera_Meteora': 'Meteora'
    }

    # Add legend entries for each plotted pool
    for pool_name, color in plotted_pools:
        label = simple_labels.get(pool_name, pool_name)
        legend_elements.append(Line2D([0], [0], color=color, linewidth=8,
                                     label=label))

    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.set_title('OHLC Candlestick Chart', fontsize=14)
    ax1.legend(handles=legend_elements, loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Set x-axis limits with padding to ensure all data fits
    date_range = real_df['date'].max() - real_df['date'].min()
    padding = date_range * 0.02  # 2% padding on each side
    ax1.set_xlim(real_df['date'].min() - padding, real_df['date'].max() + padding)

    # Plot 2: Volume over time (with cutoffs at migrations)
    # Only plot real data (skip interpolated points)
    real_df = df[~df.get('is_interpolated', False)].copy()

    for pool_name in real_df['pool_name'].unique():
        pool_df = real_df[real_df['pool_name'] == pool_name].copy()

        # Cut off old pools BEFORE migration (new pools start AT migration)
        if pool_name == 'mon3y':
            pool_df = pool_df[pool_df['date'] < migration_1]
        elif pool_name == 'zera_Raydium':
            pool_df = pool_df[pool_df['date'] < migration_2]

        if len(pool_df) > 0:
            label = simple_labels.get(pool_name, pool_name)
            ax2.bar(pool_df['date'], pool_df['volume'],
                   label=label,
                   color=pool_colors.get(pool_name, '#333333'),
                   alpha=0.6, width=0.8)

    # Add migration markers to volume chart (matching price chart style)
    for event_name, timestamp in config.MIGRATION_DATES.items():
        migration_date = datetime.fromtimestamp(timestamp)
        ax2.axvline(x=migration_date, color='#666666', linestyle='--',
                   linewidth=1, alpha=0.6, zorder=0)

    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Volume (USD)', fontsize=12)
    ax2.set_title('Trading Volume Over Time', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Set x-axis limits with padding to match price chart
    volume_df = df[~df.get('is_interpolated', False)].copy()
    date_range_vol = volume_df['date'].max() - volume_df['date'].min()
    padding_vol = date_range_vol * 0.02
    ax2.set_xlim(volume_df['date'].min() - padding_vol, volume_df['date'].max() + padding_vol)

    plt.tight_layout()

    # Save or show
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n✓ Chart saved to: {output_path}")
    else:
        plt.show()

    plt.close()


def create_comparison_chart(df: pd.DataFrame, output_path: str = None):
    """
    Create a comparison chart showing key metrics across pools

    Args:
        df: Unified DataFrame with price history
        output_path: Path to save the chart (optional)
    """
    # Filter out interpolated data for accurate statistics
    real_df = df[~df.get('is_interpolated', False)].copy()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('ZERA Token - Pool Comparison Metrics',
                 fontsize=16, fontweight='bold')

    pool_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    # Simple label mapping
    simple_labels = {
        'mon3y': 'MON3Y',
        'zera_Raydium': 'Raydium',
        'zera_Meteora': 'Meteora'
    }

    # 1. Average Price by Pool
    avg_prices = real_df.groupby('pool_name')['close'].mean()
    ax1.bar(range(len(avg_prices)), avg_prices.values, color=pool_colors)
    ax1.set_xticks(range(len(avg_prices)))
    ax1.set_xticklabels([simple_labels.get(p, p) for p in avg_prices.index],
                         rotation=15, ha='right')
    ax1.set_ylabel('Average Price (USD)')
    ax1.set_title('Average Price by Pool')
    ax1.grid(True, alpha=0.3, axis='y')

    # 2. Total Volume by Pool
    total_volumes = real_df.groupby('pool_name')['volume'].sum()
    ax2.bar(range(len(total_volumes)), total_volumes.values, color=pool_colors)
    ax2.set_xticks(range(len(total_volumes)))
    ax2.set_xticklabels([simple_labels.get(p, p) for p in total_volumes.index],
                         rotation=15, ha='right')
    ax2.set_ylabel('Total Volume (USD)')
    ax2.set_title('Total Volume by Pool')
    ax2.grid(True, alpha=0.3, axis='y')

    # 3. Price Volatility (std dev) by Pool
    volatility = real_df.groupby('pool_name')['close'].std()
    ax3.bar(range(len(volatility)), volatility.values, color=pool_colors)
    ax3.set_xticks(range(len(volatility)))
    ax3.set_xticklabels([simple_labels.get(p, p) for p in volatility.index],
                         rotation=15, ha='right')
    ax3.set_ylabel('Price Std Dev (USD)')
    ax3.set_title('Price Volatility by Pool')
    ax3.grid(True, alpha=0.3, axis='y')

    # 4. Days Active by Pool
    days_active = real_df.groupby('pool_name').size()
    ax4.bar(range(len(days_active)), days_active.values, color=pool_colors)
    ax4.set_xticks(range(len(days_active)))
    ax4.set_xticklabels([simple_labels.get(p, p) for p in days_active.index],
                         rotation=15, ha='right')
    ax4.set_ylabel('Days')
    ax4.set_title('Days Active by Pool')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save or show
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Comparison chart saved to: {output_path}")
    else:
        plt.show()

    plt.close()


if __name__ == "__main__":
    # Test the visualizer
    from fetcher import fetch_all_pools
    from consolidator import create_unified_dataframe, add_migration_markers

    print("Testing visualizer...")
    all_data = fetch_all_pools()
    df = create_unified_dataframe(all_data)
    df = add_migration_markers(df)

    # Create charts
    create_price_chart(df, f"{config.OUTPUT_DIR}/{config.CHART_FILENAME}")
    create_comparison_chart(df, f"{config.OUTPUT_DIR}/zera_comparison_chart.png")
