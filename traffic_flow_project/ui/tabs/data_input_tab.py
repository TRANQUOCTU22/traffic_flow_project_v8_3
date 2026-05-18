from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtGui import QColor

from models.graph_model import EdgeData, GraphModel


class DataInputTab(QWidget):
    def __init__(self, main_window):
        # Khởi tạo tab nhập dữ liệu.
        super().__init__()
        self.main_window = main_window
        self._loading_sample = False
        self._build()

    def _build(self):
        # Tạo các ô nhập và bảng cạnh.
        layout = QVBoxLayout(self)
        title = QLabel('Nhập dữ liệu mạng giao thông')
        title.setStyleSheet('font-size:18px;font-weight:600')
        layout.addWidget(title)

        box = QGroupBox('Thông tin bài toán')
        form = QFormLayout(box)
        self.source = QLineEdit('S')
        self.sink = QLineEdit('T')
        self.demand = QSpinBox()
        self.demand.setRange(1, 10000)
        self.demand.setValue(8)
        self.demand_warning = QLabel('')
        self.demand_warning.setWordWrap(True)
        self.demand_warning.setStyleSheet('color:#dc2626;font-weight:600;')

        form.addRow('Source:', self.source)
        form.addRow('Sink:', self.sink)
        form.addRow('Demand:', self.demand)
        form.addRow('', self.demand_warning)
        layout.addWidget(box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['from', 'to', 'capacity', 'cost'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        buttons = [
            ('Thêm cạnh', self.add_edge),
            ('Xóa cạnh', self.del_edge),
            ('Kiểm tra dữ liệu', self.validate_and_update_main),
            ('Mẫu nhỏ', lambda: self.load_sample('small')),
            ('Mẫu trung bình', lambda: self.load_sample('medium')),
            ('Mẫu lớn', lambda: self.load_sample('large')),
            ('Import JSON', self.import_json),
            ('Export JSON', self.export_json),
        ]
        for text, fn in buttons:
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        layout.addLayout(row)

        self.demand.valueChanged.connect(self.check_demand_immediately)
        self.source.textChanged.connect(self.check_demand_immediately)
        self.sink.textChanged.connect(self.check_demand_immediately)
        self.table.itemChanged.connect(self.check_demand_immediately)

    def add_edge(self, vals=None):
        # Thêm một dòng cạnh vào bảng.
        vals = vals or ['', '', 1, 1.0]
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, v in enumerate(vals):
            self.table.setItem(r, c, QTableWidgetItem(str(v)))

    def del_edge(self):
        # Xóa các cạnh đang được chọn.
        for r in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(r)
        self.check_demand_immediately()

    def graph_from_table(self):
        # Chuyển dữ liệu bảng thành GraphModel.
        edges = []
        for r in range(self.table.rowCount()):
            f_item = self.table.item(r, 0)
            t_item = self.table.item(r, 1)
            cap_item = self.table.item(r, 2)
            cost_item = self.table.item(r, 3)
            if not all([f_item, t_item, cap_item, cost_item]):
                raise ValueError(f'Dòng {r + 1} chưa nhập đủ from/to/capacity/cost.')
            f = f_item.text().strip()
            t = t_item.text().strip()
            cap = int(float(cap_item.text()))
            cost = float(cost_item.text())
            edges.append(EdgeData(f, t, cap, cost))
        return GraphModel(edges, self.source.text(), self.sink.text(), self.demand.value())

    def get_valid_graph(self, show_message=True):
        # Lấy graph và danh sách lỗi nếu có.
        try:
            g = self.graph_from_table()
            errs = g.validate()
        except Exception as e:
            return None, [str(e)]
        return g, errs

    def check_demand_immediately(self):
        # Báo ngay nếu demand vượt khả năng vận chuyển.
        if self._loading_sample:
            return
        self.demand_warning.setText('')
        try:
            g = self.graph_from_table()
            base_errors = []
            if not g.edges or not g.source or not g.sink or g.source == g.sink:
                return
            for e in g.edges:
                if not e.from_node or not e.to_node or e.capacity < 0 or e.cost < 0:
                    base_errors.append('invalid')
            if base_errors or g.source not in g.nodes or g.sink not in g.nodes:
                return
            max_flow = g.max_possible_flow()
            if max_flow > 0 and g.demand > max_flow:
                self.demand_warning.setText(
                    f'⚠ Demand = {g.demand} vượt luồng tối đa mạng có thể vận chuyển = {max_flow}. '
                    f'Hãy giảm demand hoặc tăng capacity/thêm cạnh.'
                )
        except Exception:
            return

    def show_errors(self, errs):
        # Hiển thị hộp thoại lỗi dữ liệu.
        QMessageBox.warning(self, 'Dữ liệu chưa hợp lệ', '\n'.join(errs))

    def validate_and_update_main(self):
        # Kiểm tra dữ liệu và cập nhật graph chính.
        g, errs = self.get_valid_graph()
        if errs:
            self.show_errors(errs)
            return False
        self.main_window.set_graph_model(g, reset_results=True)
        QMessageBox.information(self, 'OK', 'Dữ liệu hợp lệ.')
        return True

    def set_graph(self, g):
        # Đổ dữ liệu graph lên giao diện.
        self._loading_sample = True
        self.source.setText(g.source)
        self.sink.setText(g.sink)
        self.demand.setValue(g.demand)
        self.table.setRowCount(0)
        for e in g.edges:
            self.add_edge([e.from_node, e.to_node, e.capacity, e.cost])
        self._loading_sample = False
        self.check_demand_immediately()
        self.main_window.set_graph_model(g)

    def load_sample(self, kind='small'):
        # Nạp dữ liệu mẫu theo kích thước.
        path = Path(__file__).resolve().parents[2] / 'data' / f'sample_network_{kind}.json'
        self.set_graph(GraphModel.load_json(path))

    def import_json(self):
        # Nhập dữ liệu mạng từ file JSON.
        p, _ = QFileDialog.getOpenFileName(self, 'Import JSON', '', 'JSON (*.json)')
        if p:
            self.set_graph(GraphModel.load_json(p))

    def export_json(self):
        # Xuất dữ liệu mạng ra file JSON.
        p, _ = QFileDialog.getSaveFileName(self, 'Export JSON', 'network.json', 'JSON (*.json)')
        if p:
            self.graph_from_table().save_json(p)
