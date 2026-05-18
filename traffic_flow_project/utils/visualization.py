from __future__ import annotations
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx
import math

class MplCanvas(FigureCanvas):
    def __init__(self, width=7, height=5, dpi=100):
        # Khởi tạo khung vẽ matplotlib trong PySide6.
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)


def _edge_usage(solution):
    # Lấy dữ liệu sử dụng cạnh từ nghiệm.
    return solution.edge_usage if solution else {}


def _layered_spread_layout(G: nx.DiGraph, source: str, sink: str):
    # Sắp xếp node theo tầng để tránh thẳng hàng.
    """Layout tự viết: source bên trái, sink bên phải, node trung gian dàn đều theo lớp."""
    try:
        dist = nx.single_source_shortest_path_length(G, source)
    except Exception:
        dist = {}
    max_layer = max(dist.values()) if dist else 1
    if sink in dist:
        max_layer = max(max_layer, dist[sink])
    max_layer = max(max_layer, 2)

    layers = {}
    for n in G.nodes:
        if n == source:
            layer = 0
        elif n == sink:
            layer = max_layer
        else:
            layer = dist.get(n, max_layer // 2)
            layer = min(max(layer, 1), max_layer - 1)
        layers.setdefault(layer, []).append(n)

    pos = {}
    for layer in sorted(layers):
        nodes = sorted(layers[layer])
        count = len(nodes)
        x = layer * 3.2
        if count == 1:
            ys = [0.0]
        else:
            gap = 2.2
            start = (count - 1) * gap / 2
            ys = [start - i * gap for i in range(count)]
        for n, y in zip(nodes, ys):
            pos[n] = (x, y)

    # Nếu bố cục quá thẳng hàng, thêm lệch nhẹ cho node trung gian để dễ nhìn.
    for i, n in enumerate(sorted(G.nodes)):
        if n not in (source, sink):
            x, y = pos[n]
            pos[n] = (x, y + (0.35 if i % 2 == 0 else -0.35))
    return pos


def draw_graph_on_canvas(canvas, graph_model, solution=None):
    # Vẽ mạng giao thông với mũi tên, capacity và cost.
    """Vẽ đồ thị rõ hơn: node dàn đều, mũi tên tách node, nhãn cap/cost trên cạnh, highlight luồng."""
    ax = canvas.ax
    ax.clear()
    G = nx.DiGraph()
    for n in graph_model.nodes:
        G.add_node(n)
    for e in graph_model.edges:
        G.add_edge(e.from_node, e.to_node, capacity=e.capacity, cost=e.cost)

    pos = _layered_spread_layout(G, graph_model.source, graph_model.sink)

    usage = _edge_usage(solution)
    used_edges = {e for e, v in usage.items() if v > 0}

    node_colors = []
    for n in G.nodes:
        if n == graph_model.source:
            node_colors.append('#16a34a')
        elif n == graph_model.sink:
            node_colors.append('#dc2626')
        else:
            node_colors.append('#60a5fa')

    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=1050, node_color=node_colors,
        edgecolors='white', linewidths=2.5
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=11, font_weight='bold')

    normal_edges = [e for e in G.edges if e not in used_edges]
    highlighted_edges = [e for e in G.edges if e in used_edges]

    # Mũi tên có margin để không dính sát node.
    common_edge_args = dict(
        ax=ax,
        arrows=True,
        arrowstyle='-|>',
        arrowsize=24,
        min_source_margin=18,
        min_target_margin=24,
        connectionstyle='arc3,rad=0.10',
    )
    nx.draw_networkx_edges(
        G, pos, edgelist=normal_edges, width=1.7,
        edge_color='#64748b', **common_edge_args
    )
    nx.draw_networkx_edges(
        G, pos, edgelist=highlighted_edges, width=4.0,
        edge_color='#f97316', arrowsize=30,
        ax=ax, arrows=True, arrowstyle='-|>', min_source_margin=18,
        min_target_margin=26, connectionstyle='arc3,rad=0.10'
    )

    edge_labels = {}
    for e in graph_model.edges:
        key = (e.from_node, e.to_node)
        if solution:
            edge_labels[key] = f'flow={int(usage.get(key,0))}/{e.capacity}\ncost={e.cost}'
        else:
            edge_labels[key] = f'cap={e.capacity}\ncost={e.cost}'
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax, font_size=8,
        label_pos=0.55, rotate=False,
        bbox=dict(boxstyle='round,pad=.25', fc='white', ec='#cbd5e1', alpha=.95)
    )

    title = 'Mạng giao thông'
    if solution:
        title += f' — {solution.algorithm}: flow={solution.total_flow}, cost={solution.total_cost:.2f}'
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_axis_off()
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    ax.set_xlim(min(xs)-1.7, max(xs)+1.7)
    ax.set_ylim(min(ys)-1.7, max(ys)+1.7)
    canvas.fig.tight_layout()
    canvas.draw()


def draw_history_on_canvas(canvas, history, title='Fitness history'):
    # Vẽ biểu đồ lịch sử fitness của Cuckoo Search.
    ax = canvas.ax
    ax.clear()
    ax.plot(list(range(len(history))), history, linewidth=1.8)
    ax.set_title(title)
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Best fitness')
    ax.grid(True, alpha=.35)
    canvas.fig.tight_layout()
    canvas.draw()
