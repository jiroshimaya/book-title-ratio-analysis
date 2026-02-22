#!/usr/bin/env python
"""
有向グラフから循環を検出するスクリプト

CSVファイルからデータを読み込み、正規化して有向グラフを作成し、
循環するパスを検出して可視化します。
"""

import csv
from collections import defaultdict
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


def build_graph(aggregated_data: dict[tuple[str, str], float]) -> nx.DiGraph:
    """
    集計されたデータから有向グラフを構築する
    
    Args:
        aggregated_data: (a, b) -> c_valueの辞書
    
    Returns:
        有向グラフ
    """
    G = nx.DiGraph()
    for (a, b), weight in aggregated_data.items():
        G.add_edge(a, b, weight=weight)
    return G


def find_all_cycles(G: nx.DiGraph) -> list[list[str]]:
    """
    有向グラフからすべての単純循環を検出する
    
    Args:
        G: 有向グラフ
    
    Returns:
        循環のリスト（各循環はノードのリスト）
    """
    try:
        # networkxのsimple_cyclesを使用
        cycles = list(nx.simple_cycles(G))
        return cycles
    except Exception as e:
        print(f"循環検出中にエラー: {e}")
        return []


def visualize_cycles(
    G: nx.DiGraph, cycles: list[list[str]], output_path: Path
) -> None:
    """
    検出された循環を可視化する
    
    Args:
        G: 有向グラフ
        cycles: 循環のリスト
        output_path: 出力ファイルのパス
    """
    if not cycles:
        print("循環が見つかりませんでした。")
        return
    
    # 日本語フォントの設定（macOS）
    plt.rcParams["font.sans-serif"] = [
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Arial Unicode MS",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    
    # 循環に含まれるノードとエッジを抽出
    cycle_nodes = set()
    cycle_edges = set()
    
    for cycle in cycles:
        # 循環をノードリストからエッジリストに変換
        for i in range(len(cycle)):
            node1 = cycle[i]
            node2 = cycle[(i + 1) % len(cycle)]
            cycle_nodes.add(node1)
            cycle_nodes.add(node2)
            cycle_edges.add((node1, node2))
    
    # 循環に関連するノードとエッジのみを含むサブグラフを作成
    subgraph = G.subgraph(cycle_nodes).copy()
    
    # 可視化の設定
    plt.figure(figsize=(14, 10))
    
    # レイアウトの計算（循環構造が見やすい配置）
    pos = nx.spring_layout(subgraph, k=2, iterations=100, seed=42)
    
    # エッジの太さを重みに応じて設定
    edges = subgraph.edges()
    weights = [subgraph[u][v]["weight"] for u, v in edges]
    max_weight = max(weights) if weights else 1
    # 重みを2〜8の範囲に正規化
    normalized_widths = [2 + (w / max_weight) * 6 for w in weights]
    
    # 循環に含まれるエッジとそうでないエッジを分ける
    cycle_edge_list = [(u, v) for u, v in edges if (u, v) in cycle_edges]
    non_cycle_edge_list = [(u, v) for u, v in edges if (u, v) not in cycle_edges]
    
    cycle_edge_widths = [
        2 + (subgraph[u][v]["weight"] / max_weight) * 6 for u, v in cycle_edge_list
    ]
    non_cycle_edge_widths = [
        2 + (subgraph[u][v]["weight"] / max_weight) * 6
        for u, v in non_cycle_edge_list
    ]
    
    # ノードの描画（すべて同じ色）
    nx.draw_networkx_nodes(
        subgraph, pos, node_color="lightcoral", node_size=3000, alpha=0.9
    )
    
    # 循環に含まれるエッジを強調（赤）
    if cycle_edge_list:
        nx.draw_networkx_edges(
            subgraph,
            pos,
            edgelist=cycle_edge_list,
            width=cycle_edge_widths,
            alpha=0.9,
            edge_color="red",
            arrows=True,
            arrowsize=25,
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1",
        )
    
    # その他のエッジ（グレー）
    if non_cycle_edge_list:
        nx.draw_networkx_edges(
            subgraph,
            pos,
            edgelist=non_cycle_edge_list,
            width=non_cycle_edge_widths,
            alpha=0.5,
            edge_color="gray",
            arrows=True,
            arrowsize=25,
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1",
        )
    
    # ラベルの描画
    nx.draw_networkx_labels(subgraph, pos, font_size=11, font_weight="bold")
    
    # エッジの重みをラベルとして表示
    edge_labels = {
        (u, v): f"{subgraph[u][v]['weight']:.1f}" for u, v in subgraph.edges()
    }
    nx.draw_networkx_edge_labels(
        subgraph, pos, edge_labels, font_size=8, label_pos=0.3
    )
    
    plt.title(
        f"検出された循環 ({len(cycles)}個の循環, {len(cycle_nodes)}個のノード)",
        fontsize=16,
        fontweight="bold",
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"循環グラフを保存しました: {output_path}")
    plt.close()


def print_cycle_details(cycles: list[list[str]], G: nx.DiGraph) -> None:
    """
    循環の詳細を出力する
    
    Args:
        cycles: 循環のリスト
        G: 有向グラフ
    """
    print(f"\n検出された循環: {len(cycles)}個")
    print("=" * 60)
    
    for i, cycle in enumerate(cycles, 1):
        print(f"\n循環 {i} (長さ: {len(cycle)})")
        print("-" * 40)
        
        # 循環のパスを表示
        path_str = " -> ".join(cycle)
        path_str += f" -> {cycle[0]}"  # 始点に戻る
        print(f"パス: {path_str}")
        
        # 各エッジの重みを表示
        print("エッジの重み:")
        for j in range(len(cycle)):
            node1 = cycle[j]
            node2 = cycle[(j + 1) % len(cycle)]
            weight = G[node1][node2]["weight"]
            print(f"  {node1} -> {node2}: {weight:.1f}")


def main():
    """メイン処理"""
    # パスの設定
    csv_path = Path("local/titles_extracted.csv")
    output_path = Path("local/charts/cycles_graph.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"CSVファイルを読み込んでいます: {csv_path}")
    data = load_csv_data(csv_path)
    print(f"読み込み完了: {len(data)}件のデータ")
    
    print("\nデータを正規化して集計しています...")
    aggregated_data = aggregate_normalized_data(data)
    print(f"集計完了: {len(aggregated_data)}個のユニークなエッジ")
    
    print("\n有向グラフを構築しています...")
    G = build_graph(aggregated_data)
    print(f"グラフ構築完了: {G.number_of_nodes()}個のノード, {G.number_of_edges()}個のエッジ")
    
    print("\n循環を検出しています...")
    cycles = find_all_cycles(G)
    
    if cycles:
        # 循環の詳細を出力
        print_cycle_details(cycles, G)
        
        # 循環を可視化
        print("\n循環を可視化しています...")
        visualize_cycles(G, cycles, output_path)
    else:
        print("\n循環は見つかりませんでした。")


if __name__ == "__main__":
    main()
