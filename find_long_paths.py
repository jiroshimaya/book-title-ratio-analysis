#!/usr/bin/env python
"""
有向グラフから長いパスを検出するスクリプト

CSVファイルからデータを読み込み、正規化して有向グラフを作成し、
長いパス（依存関係の連鎖）を検出して可視化します。
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


def find_longest_path(G: nx.DiGraph) -> list[str]:
    """
    有向非巡回グラフから最長パスを検出する
    
    Args:
        G: 有向グラフ
    
    Returns:
        最長パスのノードリスト
    """
    try:
        # DAGの最長パスを検出
        longest_path = nx.dag_longest_path(G)
        return longest_path
    except Exception as e:
        print(f"最長パス検出中にエラー: {e}")
        return []


def find_all_long_paths(G: nx.DiGraph, min_length: int = 3) -> list[list[str]]:
    """
    指定した長さ以上のパスをすべて検出する
    
    Args:
        G: 有向グラフ
        min_length: 検出する最小パス長（ノード数）
    
    Returns:
        長いパスのリスト
    """
    long_paths = []
    
    # すべてのノードペアについて単純パスを探索
    nodes = list(G.nodes())
    
    for source in nodes:
        for target in nodes:
            if source == target:
                continue
            
            try:
                # sourceからtargetへのすべての単純パスを検出
                paths = list(nx.all_simple_paths(G, source, target))
                for path in paths:
                    if len(path) >= min_length:
                        long_paths.append(path)
            except nx.NetworkXNoPath:
                continue
    
    # 重複を削除（パスを文字列化して比較）
    unique_paths = []
    seen = set()
    for path in long_paths:
        path_str = "->".join(path)
        if path_str not in seen:
            seen.add(path_str)
            unique_paths.append(path)
    
    # 長さでソート（長い順）
    unique_paths.sort(key=len, reverse=True)
    
    return unique_paths


def visualize_long_paths(
    G: nx.DiGraph, paths: list[list[str]], output_path: Path, max_paths: int = 10
) -> None:
    """
    検出された長いパスを横並びのフロー形式で可視化する
    
    Args:
        G: 有向グラフ
        paths: パスのリスト
        output_path: 出力ファイルのパス
        max_paths: 可視化する最大パス数
    """
    if not paths:
        print("指定された長さ以上のパスが見つかりませんでした。")
        return
    
    # 日本語フォントの設定（macOS）
    plt.rcParams["font.sans-serif"] = [
        "Hiragino Sans",
        "Hiragino Kaku Gothic ProN",
        "Arial Unicode MS",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    
    # 可視化するパスを制限
    vis_paths = paths[:max_paths]
    
    # 最長パスの長さを取得
    max_path_length = max(len(p) for p in vis_paths)
    
    # 図のサイズを設定（横長）
    fig, ax = plt.subplots(figsize=(max_path_length * 3.5, max_paths * 1.2 + 1))
    
    # 各パスを描画
    for path_idx, path in enumerate(vis_paths):
        y_position = max_paths - path_idx  # 上から順に描画
        
        # パス内の各ノードを描画
        for node_idx, node in enumerate(path):
            x_position = node_idx * 3 + 1
            
            # ノードの色を決定
            if node_idx == 0:
                color = "lightgreen"  # 始点
            elif node_idx == len(path) - 1:
                color = "lightcoral"  # 終点
            else:
                color = "lightyellow"  # 中間ノード
            
            # ボックスを描画
            from matplotlib.patches import FancyBboxPatch
            box = FancyBboxPatch(
                (x_position - 0.8, y_position - 0.3),
                1.6,
                0.6,
                boxstyle="round,pad=0.05",
                facecolor=color,
                edgecolor="black",
                linewidth=2,
                alpha=0.9,
            )
            ax.add_patch(box)
            
            # ノード名を描画
            ax.text(
                x_position,
                y_position,
                node,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                wrap=True,
            )
            
            # 矢印を描画（最後のノード以外）
            if node_idx < len(path) - 1:
                next_node = path[node_idx + 1]
                weight = G[node][next_node]["weight"]
                
                # 矢印の描画
                arrow_start_x = x_position + 0.8
                arrow_end_x = x_position + 3 - 0.8
                
                ax.annotate(
                    "",
                    xy=(arrow_end_x, y_position),
                    xytext=(arrow_start_x, y_position),
                    arrowprops=dict(
                        arrowstyle="->",
                        lw=2,
                        color="darkblue",
                        alpha=0.8,
                    ),
                )
                
                # 重みを矢印の上に表示
                ax.text(
                    (arrow_start_x + arrow_end_x) / 2,
                    y_position + 0.15,
                    f"{int(weight)}割",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color="darkblue",
                    fontweight="bold",
                )
    
    # 軸の設定
    ax.set_xlim(-0.5, max_path_length * 3 + 0.5)
    ax.set_ylim(0.3, max_paths + 0.7)
    ax.axis("off")
    
    # タイトル
    max_len = max(len(p) for p in vis_paths)
    plt.title(
        f"検出された長いパス (最長: {max_len}ノード, 表示: {len(vis_paths)}パス)",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"長いパスのグラフを保存しました: {output_path}")
    plt.close()


def print_path_details(paths: list[list[str]], G: nx.DiGraph, max_display: int = 20) -> None:
    """
    パスの詳細を出力する
    
    Args:
        paths: パスのリスト
        G: 有向グラフ
        max_display: 詳細表示する最大パス数
    """
    print(f"\n検出された長いパス: {len(paths)}個")
    print("=" * 80)
    
    for i, path in enumerate(paths[:max_display], 1):
        print(f"\nパス {i} (長さ: {len(path)}ノード)")
        print("-" * 60)
        
        # パスを表示
        path_str = " -> ".join(path)
        print(f"経路: {path_str}")
        
        # 各エッジの重みを表示
        print("エッジの重み:")
        total_weight = 0
        for j in range(len(path) - 1):
            node1 = path[j]
            node2 = path[j + 1]
            weight = G[node1][node2]["weight"]
            total_weight += weight
            print(f"  {node1} -> {node2}: {int(weight)}割")
        print(f"  合計重み: {total_weight:.1f}")
    
    if len(paths) > max_display:
        print(f"\n... 他 {len(paths) - max_display}個のパス")


def main():
    """メイン処理"""
    # パスの設定
    csv_path = Path("local/titles_extracted.csv")
    output_path = Path("local/long_paths_flow.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 検出する最小パス長（ノード数）
    min_path_length = 2
    # 可視化する最大パス数
    max_vis_paths = 15
    
    print(f"CSVファイルを読み込んでいます: {csv_path}")
    data = load_csv_data(csv_path)
    print(f"読み込み完了: {len(data)}件のデータ")
    
    print("\nデータを正規化して集計しています...")
    aggregated_data = aggregate_normalized_data(data)
    print(f"集計完了: {len(aggregated_data)}個のユニークなエッジ")
    
    print("\n有向グラフを構築しています...")
    G = build_graph(aggregated_data)
    print(f"グラフ構築完了: {G.number_of_nodes()}個のノード, {G.number_of_edges()}個のエッジ")
    
    # グラフがDAGかチェック
    if nx.is_directed_acyclic_graph(G):
        print("✓ グラフは有向非巡回グラフ（DAG）です")
    else:
        print("✗ グラフには循環が含まれています")
    
    print(f"\n最長パスを検出しています...")
    longest_path = find_longest_path(G)
    
    if longest_path:
        print(f"最長パス: {len(longest_path)}ノード")
        print(f"経路: {' -> '.join(longest_path)}")
    
    print(f"\n長さ{min_path_length}以上のすべてのパスを検出しています...")
    long_paths = find_all_long_paths(G, min_length=min_path_length)
    
    if long_paths:
        # パスの詳細を出力
        print_path_details(long_paths, G, max_display=20)
        
        # パスを可視化
        print(f"\n上位{max_vis_paths}個のパスを可視化しています...")
        visualize_long_paths(G, long_paths, output_path, max_paths=max_vis_paths)
    else:
        print(f"\n長さ{min_path_length}以上のパスは見つかりませんでした。")


if __name__ == "__main__":
    main()
