from PySide6.QtWidgets import QWidget,QVBoxLayout,QTextEdit,QHBoxLayout,QPushButton,QFileDialog,QMessageBox
from utils.exporter import build_report_text,export_txt,export_csv,export_docx
class ReportTab(QWidget):
    def __init__(self,main_window):
        # Khởi tạo tab báo cáo.
        super().__init__(); self.main_window=main_window; self._build()
    def _build(self):
        # Tạo giao diện xem và xuất báo cáo.
        l=QVBoxLayout(self); row=QHBoxLayout()
        for text,fn in [('Export TXT',self.txt),('Export CSV',self.csv),('Export DOCX',self.docx)]: b=QPushButton(text); b.clicked.connect(fn); row.addWidget(b)
        l.addLayout(row); self.text=QTextEdit(); l.addWidget(self.text)
    def refresh_text(self):
        # Cập nhật nội dung báo cáo hiển thị.
        if not self.main_window.graph_model: self.text.setPlainText('Chưa có dữ liệu.'); return
        self.text.setPlainText(build_report_text(self.main_window.graph_model,self.main_window.results,self.main_window.comparison_tab.build_comparison_text()))
    def txt(self):
        # Xuất báo cáo dạng TXT.
        p,_=QFileDialog.getSaveFileName(self,'Export TXT','report.txt','Text (*.txt)')
        if p: export_txt(p,self.main_window.graph_model,self.main_window.results,self.main_window.comparison_tab.build_comparison_text())
    def csv(self):
        # Xuất bảng kết quả dạng CSV.
        p,_=QFileDialog.getSaveFileName(self,'Export CSV','comparison.csv','CSV (*.csv)')
        if p: export_csv(p,self.main_window.graph_model,self.main_window.results)
    def docx(self):
        # Xuất báo cáo dạng DOCX.
        p,_=QFileDialog.getSaveFileName(self,'Export DOCX','report.docx','Word (*.docx)')
        if p: export_docx(p,self.main_window.graph_model,self.main_window.results,self.main_window.comparison_tab.build_comparison_text())
