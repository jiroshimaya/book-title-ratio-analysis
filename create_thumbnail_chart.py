#!/usr/bin/env python
"""
サムネイル用のパイチャートを作成するスクリプト

「人」のチャートをサムネ向けに最適化：
- タイトルを短く
- ラベルを3つに絞る
- 54割を強調
"""

import matplotlib.pyplot as plt
from pathlib import Path


def create_thumbnail_chart():
    """「人」のサムネイル用パイチャートを作成（note横長サムネ対応）"""
    
    # データ準備（その他、聞き方、見た目、話し方の順 - 話し方が右に来る）
    labels = ["その他", "聞き方", "見た目", "話し方"]
    sizes = [36, 18, 18, 54]  # その他 = 9×4
    
    # 色設定：話し方を強調（濃い青）、他は淡め
    colors = ["#E3F2FD", "#90CAF9", "#90CAF9", "#2196F3"]
    
    # 図の作成（note用横長レイアウト: 1280x670 ≒ 19:10）
    fig = plt.figure(figsize=(19, 10), facecolor='white')
    
    # 円グラフ用の軸を右側に配置（左に寄せて間隔を詰める）
    ax = fig.add_axes([0.28, 0.05, 0.70, 0.9])
    
    # 日本語フォント設定
    plt.rcParams["font.sans-serif"] = [
        "Hiragino Sans",
        "Yu Gothic",
        "Meirio",
        "Takao",
        "IPAexGothic",
        "IPAPGothic",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    
    # 話し方だけ飛び出させる（最後の要素）
    explode = (0, 0, 0, 0.15)
    
    # カスタムラベル関数
    def make_label_func():
        counter = {"index": 0}
        data = [
            ("その他", 36),
            ("聞き方", 18),
            ("見た目", 18),
            ("話し方", 54),
        ]
        
        def label_func(pct):
            idx = counter["index"]
            if idx >= len(data):
                return ""
            
            label, val = data[idx]
            counter["index"] += 1
            
            # 話し方だけ特大フォント
            if idx == 3:
                return f"{label}\n{val}割"
            else:
                return f"{label}\n{val}割"
        
        return label_func
    
    # 円グラフの描画
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=make_label_func(),
        startangle=90,
        colors=colors,
        explode=explode,
        textprops={"fontsize": 20, "fontweight": "bold", "color": "white"},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    
    # 話し方のテキストだけ特大に（最後の要素）
    autotexts[3].set_fontsize(48)
    autotexts[3].set_color("white")
    
    # タイトルを左側に配置（横長レイアウト用・間隔を詰める）
    # 「人は話し方が」
    fig.text(
        0.08, 0.65,
        "人は話し方が",
        fontsize=72,
        fontweight="bold",
        color="#2C3E50",
        ha="left",
        va="center",
    )
    # 「54」を特大で
    fig.text(
        0.08, 0.42,
        "54",
        fontsize=120,
        fontweight="bold",
        color="#1E88E5",
        ha="left",
        va="center",
    )
    # 「割」
    fig.text(
        0.24, 0.42,
        "割",
        fontsize=72,
        fontweight="bold",
        color="#2C3E50",
        ha="left",
        va="center",
    )
    
    # 均等な円にする
    ax.axis("equal")
    
    # 保存（note推奨サイズ）
    output_path = Path("local/人_thumbnail.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"サムネイル用チャートを作成しました: {output_path}")


if __name__ == "__main__":
    create_thumbnail_chart()
