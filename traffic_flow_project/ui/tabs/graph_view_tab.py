from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
from utils.visualization import MplCanvas,draw_graph_on_canvas
class GraphViewTab(QWidget):
    def __init__(self,main_window):
        # Khởi tạo tab vẽ mạng giao thông.
        super().__init__(); self.main_window=main_window; l=QVBoxLayout(self); l.addWidget(QLabel('Trực quan mạng giao thông')); self.canvas=MplCanvas(9,6); l.addWidget(self.canvas)
    def draw_current_graph(self):
        # Vẽ đồ thị hiện tại và highlight luồng đã chọn.
        if self.main_window.graph_model:
            sol=next(reversed(self.main_window.results.values()),None) if self.main_window.results else None
            draw_graph_on_canvas(self.canvas,self.main_window.graph_model,sol)
