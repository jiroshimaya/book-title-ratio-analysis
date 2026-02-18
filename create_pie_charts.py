import json
import matplotlib.pyplot as plt
from pathlib import Path


def create_pie_charts():
    """a_ranking.jsonから各aごとにbの割合を示す円グラフを作成する"""
    # JSONファイルを読み込む
    with open("a_ranking.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 出力ディレクトリを作成
    output_dir = Path("charts")
    output_dir.mkdir(exist_ok=True)
    
    # 各aについて円グラフを作成
    for idx, ranking in enumerate(data["rankings"]):
        a = ranking["a"]
        b_breakdown = ranking["b_breakdown"]
        
        # bの名前とc_sumを抽出
        labels = [item["b"] for item in b_breakdown]
        sizes = [item["c_sum"] for item in b_breakdown]
        
        # c_sumの大きい順にソート
        sorted_data = sorted(zip(sizes, labels))
        sizes, labels = zip(*sorted_data)
        sizes = list(sizes)
        labels = list(labels)
        
        # 円グラフを作成
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 日本語フォント設定（macOSの場合）
        plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic']
        plt.rcParams['axes.unicode_minus'] = False
        
        # ラベルと割合表示のカスタマイズ
        total = sum(sizes)
        cumulative = 0
        label_mapping = []
        
        # 各セグメントの累積パーセンテージを計算
        for i, size in enumerate(sizes):
            pct = size / total * 100
            cumulative += pct
            label_mapping.append({
                'label': labels[i],
                'size': size,
                'pct': pct,
                'cumulative': cumulative
            })
        
        def make_label_func(label_data, total_val):
            # カウンターを使って順番に処理
            counter = {'index': 0}
            
            def label_func(pct):
                idx = counter['index']
                if idx >= len(label_data):
                    return ""
                
                data = label_data[idx]
                label = data['label']
                val = int(data['size'])
                                
                counter['index'] += 1
                return f'{label}\n{val}割'
            
            return label_func
        
        # 円グラフの描画
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,  # ラベルは円の中に表示
            autopct=make_label_func(label_mapping, total),
            startangle=90,
            textprops={'fontsize': 24, 'fontweight': 'bold', 'color': 'white'}
        )
        
        # タイトル設定
        ax.set_title(f'「{a}」の構成要素 (全体: {ranking["c_sum"]:.0f}割)', fontsize=36, fontweight='bold', pad=20)
        
        # 均等な円にする
        ax.axis('equal')
        
        # 保存
        output_path = output_dir / f"{str(idx).zfill(3)}_{a}_pie_chart.png"
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"作成しました: {output_path}")


if __name__ == "__main__":
    create_pie_charts()
    print("\n全ての円グラフを作成しました。chartsフォルダを確認してください。")
