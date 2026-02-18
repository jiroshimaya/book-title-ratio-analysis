import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Arial Unicode MS'  # 日本語対応

# CSVファイルを読み込む
df = pd.read_csv('local/titles_extracted.csv')

# c_value列のヒストグラムを作成
plt.figure(figsize=(10, 6))
# 整数を棒の真ん中に配置するため、binsを0.5刻みで設定
bins = [i + 0.5 for i in range(-1, 10)]  # [-0.5, 0.5, 1.5, ..., 9.5]
n, bins_edges, patches = plt.hist(df['c_value'], bins=bins, edgecolor='black', alpha=0.7)

# 各棒の上に数値を表示
for i, count in enumerate(n):
    if count > 0:  # 0の場合は表示しない
        plt.text(i, count, str(int(count)), ha='center', va='bottom', fontsize=10)

plt.xlabel('c（割）', fontsize=12)
plt.ylabel('頻度', fontsize=12)
plt.title('「aはbがc割」系の書籍タイトルの「c」のヒストグラム', fontsize=14)
plt.xticks(range(0, 11))
plt.grid(axis='y', alpha=0.3)

# グラフを保存
plt.tight_layout()
plt.savefig('local/c_value_histogram.png', dpi=150)
print(f"ヒストグラムを local/c_value_histogram.png に保存しました")

# 統計情報を表示
print(f"\n統計情報:")
print(f"データ数: {len(df)}")
print(f"c_valueの範囲: {df['c_value'].min()} - {df['c_value'].max()}")
print(f"平均値: {df['c_value'].mean():.2f}")
print(f"中央値: {df['c_value'].median():.2f}")
print(f"\nc_valueの分布:")
print(df['c_value'].value_counts().sort_index())

plt.show()
