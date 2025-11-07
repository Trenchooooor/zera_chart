import pandas as pd

df = pd.read_csv('output/zera_unified_price_history.csv')
real_df = df[df['is_interpolated'] == False]

print('M0N3Y (Original Pool):')
mon3y = real_df[real_df['pool_name']=='mon3y']
print(f'  Average price: ${mon3y["close"].mean():.6f}')
print(f'  Max price: ${mon3y["close"].max():.6f}')

print('\nZERA Pool 2:')
pool2 = real_df[real_df['pool_name']=='zera_pool2']
if len(pool2) > 0:
    print(f'  Average price: ${pool2["close"].mean():.6f}')
    print(f'  Max price: ${pool2["close"].max():.6f}')

print('\nZERA Pool 3:')
pool3 = real_df[real_df['pool_name']=='zera_pool3']
if len(pool3) > 0:
    print(f'  Average price: ${pool3["close"].mean():.6f}')
    print(f'  Current price: ${pool3["close"].iloc[-1]:.6f}')

print('\n' + '='*60)
print('If these are USD values, the axis labels need updating!')
