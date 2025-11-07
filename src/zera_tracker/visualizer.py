"""
Visualizer - creates charts for unified ZERA price history
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
from typing import Dict
import config
import os


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
        'zera_pool2': '#4ECDC4', # Teal for ZERA Raydium
        'zera_pool3': '#45B7D1'  # Blue for ZERA Meteora
    }

    # Migration timestamps for filtering
    migration_1 = datetime.fromtimestamp(config.MIGRATION_DATES['mon3y_to_zera'])
    migration_2 = datetime.fromtimestamp(config.MIGRATION_DATES['zera_pool2_to_pool3'])

    # Plot 1: Price over time
    # Plot each pool's real data
    real_df = df[~df.get('is_interpolated', False)].copy()

    for pool_name in real_df['pool_name'].unique():
        pool_df = real_df[real_df['pool_name'] == pool_name].copy()

        # Cut off old pools BEFORE migration (new pools start AT migration)
        if pool_name == 'mon3y':
            # M0N3Y ends BEFORE ZERA Raydium starts (exclude migration date)
            pool_df = pool_df[pool_df['date'] < migration_1]
        elif pool_name == 'zera_pool2':
            # ZERA Raydium starts at migration_1, ends BEFORE Meteora starts
            pool_df = pool_df[pool_df['date'] < migration_2]
        # Meteora has no cutoff (it's current, starts at migration_2)

        if len(pool_df) > 0:
            ax1.plot(pool_df['date'], pool_df['close'],
                    label=config.POOLS[pool_name]['name'],
                    color=pool_colors.get(pool_name, '#333333'),
                    linewidth=2, alpha=0.8)

    # Plot interpolated segments (each gap separately)
    interp_df = df[df.get('is_interpolated', False)].copy()
    if len(interp_df) > 0:
        # Group by pool_name to separate the two migration gaps
        interp_groups = interp_df.groupby('pool_name')

        legend_added = False
        for pool_name, interp_segment in interp_groups:
            # Sort by timestamp
            interp_segment = interp_segment.sort_values('timestamp')

            # Plot this gap's interpolated points only
            if not legend_added:
                ax1.plot(interp_segment['date'], interp_segment['close'],
                        color='#888888',
                        linewidth=1.5, alpha=0.5, linestyle='--',
                        label='Interpolated (Migration Gaps)')
                legend_added = True
            else:
                ax1.plot(interp_segment['date'], interp_segment['close'],
                        color='#888888',
                        linewidth=1.5, alpha=0.5, linestyle='--')

    # Add migration markers
    for event_name, timestamp in config.MIGRATION_DATES.items():
        migration_date = datetime.fromtimestamp(timestamp)
        ax1.axvline(x=migration_date, color='red', linestyle='--',
                   linewidth=1.5, alpha=0.7)
        ax1.text(migration_date, ax1.get_ylim()[1] * 0.95,
                event_name.replace('_', '\n').title(),
                rotation=0, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
                fontsize=8)

    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.set_title('Closing Price Over Time', fontsize=14)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Set x-axis limits to remove whitespace
    ax1.set_xlim(df['date'].min(), df['date'].max())

    # Plot 2: Volume over time (with cutoffs at migrations)
    # Only plot real data (skip interpolated points)
    real_df = df[~df.get('is_interpolated', False)].copy()

    for pool_name in real_df['pool_name'].unique():
        pool_df = real_df[real_df['pool_name'] == pool_name].copy()

        # Cut off old pools BEFORE migration (new pools start AT migration)
        if pool_name == 'mon3y':
            pool_df = pool_df[pool_df['date'] < migration_1]
        elif pool_name == 'zera_pool2':
            pool_df = pool_df[pool_df['date'] < migration_2]

        if len(pool_df) > 0:
            ax2.bar(pool_df['date'], pool_df['volume'],
                   label=config.POOLS[pool_name]['name'],
                   color=pool_colors.get(pool_name, '#333333'),
                   alpha=0.6, width=0.8)

    # Add migration markers to volume chart
    for event_name, timestamp in config.MIGRATION_DATES.items():
        migration_date = datetime.fromtimestamp(timestamp)
        ax2.axvline(x=migration_date, color='red', linestyle='--',
                   linewidth=1.5, alpha=0.7)

    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Volume (USD)', fontsize=12)
    ax2.set_title('Trading Volume Over Time', fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Set x-axis limits to remove whitespace
    ax2.set_xlim(df['date'].min(), df['date'].max())

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

    # 1. Average Price by Pool
    avg_prices = real_df.groupby('pool_name')['close'].mean()
    ax1.bar(range(len(avg_prices)), avg_prices.values, color=pool_colors)
    ax1.set_xticks(range(len(avg_prices)))
    ax1.set_xticklabels([config.POOLS[p]['name'] for p in avg_prices.index],
                         rotation=15, ha='right')
    ax1.set_ylabel('Average Price (USD)')
    ax1.set_title('Average Price by Pool')
    ax1.grid(True, alpha=0.3, axis='y')

    # 2. Total Volume by Pool
    total_volumes = real_df.groupby('pool_name')['volume'].sum()
    ax2.bar(range(len(total_volumes)), total_volumes.values, color=pool_colors)
    ax2.set_xticks(range(len(total_volumes)))
    ax2.set_xticklabels([config.POOLS[p]['name'] for p in total_volumes.index],
                         rotation=15, ha='right')
    ax2.set_ylabel('Total Volume (USD)')
    ax2.set_title('Total Volume by Pool')
    ax2.grid(True, alpha=0.3, axis='y')

    # 3. Price Volatility (std dev) by Pool
    volatility = real_df.groupby('pool_name')['close'].std()
    ax3.bar(range(len(volatility)), volatility.values, color=pool_colors)
    ax3.set_xticks(range(len(volatility)))
    ax3.set_xticklabels([config.POOLS[p]['name'] for p in volatility.index],
                         rotation=15, ha='right')
    ax3.set_ylabel('Price Std Dev (USD)')
    ax3.set_title('Price Volatility by Pool')
    ax3.grid(True, alpha=0.3, axis='y')

    # 4. Days Active by Pool
    days_active = real_df.groupby('pool_name').size()
    ax4.bar(range(len(days_active)), days_active.values, color=pool_colors)
    ax4.set_xticks(range(len(days_active)))
    ax4.set_xticklabels([config.POOLS[p]['name'] for p in days_active.index],
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
