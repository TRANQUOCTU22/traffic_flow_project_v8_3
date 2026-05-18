from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QMainWindow,QTabWidget
from models.graph_model import GraphModel,SolutionSummary
from ui.tabs.data_input_tab import DataInputTab
from ui.tabs.graph_view_tab import GraphViewTab
from ui.tabs.backtracking_tab import BacktrackingTab
from ui.tabs.cuckoo_tab import CuckooTab
from ui.tabs.comparison_tab import ComparisonTab
from ui.tabs.report_tab import ReportTab

class MainWindow(QMainWindow):
    def __init__(self):
        # Khởi tạo cửa sổ chính và các tab.
        super().__init__()
        self.graph_model:Optional[GraphModel]=None
        self.results:Dict[str,SolutionSummary]={}
        self.accumulated_logs=''
        self.setWindowTitle('Đồ án AI - Tối ưu Network Flow bằng Backtracking và Cuckoo Search')
        self.resize(1450,850)
        tabs=QTabWidget()
        self.data_tab=DataInputTab(self); self.graph_tab=GraphViewTab(self)
        self.backtracking_tab=BacktrackingTab(self); self.cuckoo_tab=CuckooTab(self)
        self.comparison_tab=ComparisonTab(self); self.report_tab=ReportTab(self)
        for w,n in [(self.data_tab,'Nhập dữ liệu'),(self.graph_tab,'Vẽ mạng'),(self.backtracking_tab,'Backtracking'),(self.cuckoo_tab,'Cuckoo Search'),(self.comparison_tab,'So sánh'),(self.report_tab,'Báo cáo')]:
            tabs.addTab(w,n)
        self.setCentralWidget(tabs)
        self.data_tab.load_sample('small')
        self.statusBar().showMessage('Sẵn sàng')
        self.setStyleSheet('QPushButton{background:#2563eb;color:white;border:0;border-radius:8px;padding:8px 12px} QPushButton:hover{background:#1d4ed8} QGroupBox{font-weight:bold;border:1px solid #cbd5e1;border-radius:8px;margin-top:8px;padding:8px} QLineEdit,QSpinBox,QDoubleSpinBox,QTextEdit,QTableWidget,QComboBox{border:1px solid #cbd5e1;border-radius:6px;padding:3px}')

    def set_graph_model(self,g:GraphModel, reset_results:bool=True):
        # Cập nhật mô hình đồ thị hiện tại.
        self.graph_model=g
        if reset_results:
            self.results={}; self.accumulated_logs=''
        self.graph_tab.draw_current_graph(); self.comparison_tab.refresh(); self.report_tab.refresh_text()
        self.statusBar().showMessage('Đã cập nhật dữ liệu')

    def ensure_graph_ready(self)->bool:
        # Kiểm tra dữ liệu trước khi chạy thuật toán.
        g, errs = self.data_tab.get_valid_graph(show_message=False)
        if errs:
            self.data_tab.show_errors(errs); self.statusBar().showMessage('Dữ liệu chưa hợp lệ'); return False
        # Không xóa kết quả khi chỉ bấm chạy thuật toán khác trên cùng dữ liệu.
        self.graph_model = g
        return True

    def save_result(self,r:SolutionSummary):
        # Lưu kết quả thuật toán vào bảng so sánh.
        self.results[r.algorithm]=r
        self.accumulated_logs += f'[{r.algorithm}]\n{r.extra.get("log_text","")}\n\n'
        self.graph_tab.draw_current_graph(); self.comparison_tab.refresh(); self.report_tab.refresh_text()
        self.statusBar().showMessage(f'Đã chạy xong: {r.algorithm}')
