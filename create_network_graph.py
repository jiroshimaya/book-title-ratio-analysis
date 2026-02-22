#!/usr/bin/env python
"""
ネットワークグラフを作成するスクリプト

CSVファイルからデータを読み込み、正規化して有向グラフを作成します。
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from book_title_ratio_analysis.network_graph import aggregate_normalized_data


def load_csv_data(csv_path: Path) -> list[dict]:
    """
    CSVファイルからデータを読み込む

    Args:
        csv_path: CSVファイルのパス

    Returns:
        a_raw, b_raw, c_valueを含む辞書のリスト
    """
    data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(
                {
                    "a_raw": row["a_raw"],
                    "b_raw": row["b_raw"],
                    "c_value": float(row["c_value"]),
                }
            )
    return data


def create_network_graph(
    aggregated_data: dict[tuple[str, str], float], output_path: Path
) -> None:
    """
    有向グラフを作成して保存する

    Args:
        aggregated_data: (a, b) -> c_valueの辞書
        output_path: 出力ファイルのパス
    """
    # 日本語フォントの設定（macOS）
    plt.rcParams["font.sans-serif"] = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    # グラフの作成（c_valueが5以上のエッジのみ）
    G = nx.DiGraph()

    for (a, b), weight in aggregated_data.items():
        if weight >= 5.0:
            G.add_edge(a, b, weight=weight)

    # 小さな孤立コンポーネント（2ノード以下）を除去
    weak_components = list(nx.weakly_connected_components(G))
    small_components = [comp for comp in weak_components if len(comp) <= 2]
    for comp in small_components:
        G.remove_nodes_from(comp)

    # 可視化の設定
    plt.figure(figsize=(16, 12))

    # レイアウトの計算
    pos = nx.spring_layout(G, k=0.4, iterations=100, seed=42)

    # エッジの太さを重みに応じて設定
    edges = G.edges()
    weights = [G[u][v]["weight"] for u, v in edges]
    max_weight = max(weights) if weights else 1
    # 重みを1〜10の範囲に正規化
    normalized_widths = [1 + (w / max_weight) * 9 for w in weights]

    # aに由来するノード（エッジの始点として出現）を特定
    a_nodes = set(u for u, v in G.edges())
    b_only_nodes = set(G.nodes()) - a_nodes

    # ノードとエッジの描画
    # aに由来するノードを強調（オレンジ系）
    if a_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=list(a_nodes), node_color="coral", node_size=2000, alpha=0.9)
    # bのみのノードは薄い色
    if b_only_nodes:
        nx.draw_networkx_nodes(G, pos, nodelist=list(b_only_nodes), node_color="lightblue", node_size=2000, alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=9)
    nx.draw_networkx_edges(
        G,
        pos,
        width=normalized_widths,
        alpha=0.6,
        edge_color="gray",
        arrows=True,
        arrowsize=20,
        arrowstyle="->",
        connectionstyle="arc3,rad=0.1",
    )

    # エッジラベル（重み）の描画
    # 10割以上のラベル（大きいフォント）
    edge_labels_large = {(u, v): f"{int(w)}割" for u, v, w in G.edges(data="weight") if w >= 10}
    nx.draw_networkx_edge_labels(G, pos, edge_labels_large, font_size=16)

    # 9割以下のラベル（小さいフォント）
    edge_labels_small = {(u, v): f"{int(w)}割" for u, v, w in G.edges(data="weight") if w < 10}
    nx.draw_networkx_edge_labels(G, pos, edge_labels_small, font_size=8)

    plt.title("「aはbがc割」系書籍タイトルにおけるaとbの関係性ネットワーク（正規化版）", fontsize=16, pad=20)
    plt.axis("off")
    plt.tight_layout()

    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"ネットワークグラフを保存しました: {output_path}")
    print(f"ノード数: {G.number_of_nodes()}")
    print(f"エッジ数: {G.number_of_edges()}")


def main():
    """メイン処理"""
    # 入力・出力パスの設定
    csv_path = Path("local/titles_extracted.csv")
    output_path = Path("local/network_graph.png")

    # データの読み込み
    print("CSVファイルを読み込んでいます...")
    data = load_csv_data(csv_path)
    print(f"読み込んだデータ数: {len(data)}")

    # データの正規化と集計
    print("データを正規化して集計しています...")
    aggregated_data = aggregate_normalized_data(data)
    print(f"集計後のエッジ数: {len(aggregated_data)}")

    # ネットワークグラフの作成
    print("ネットワークグラフを作成しています...")
    create_network_graph(aggregated_data, output_path)


if __name__ == "__main__":
    main()
