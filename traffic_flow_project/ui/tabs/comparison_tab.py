from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QHeaderView,QPushButton

class ComparisonTab(QWidget):
    def __init__(self,main_window):
        # Khởi tạo tab so sánh kết quả.
        super().__init__(); self.main_window=main_window; self._build()
    def _build(self):
        # Tạo bảng so sánh hiệu năng.
        l=QVBoxLayout(self)
        l.addWidget(QLabel('Bảng so sánh hiệu năng'))
        self.table=QTableWidget(0,10)
        self.table.setHorizontalHeaderLabels(['Algorithm','Flow','Cost','Runtime avg','Runs','States','Calls','Pruned','Path count','Relative flow error %'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.table)
        b=QPushButton('Làm mới'); b.clicked.connect(self.refresh); l.addWidget(b)
        self.remark=QLabel('Chưa có kết quả.'); self.remark.setWordWrap(True); l.addWidget(self.remark)
    def build_comparison_text(self):
        # Sinh nhận xét tự động từ kết quả thuật toán.
        rs=list(self.main_window.results.values())
        if not rs:
            return 'Chưa chạy thuật toán nào nên chưa có nhận xét/kết luận.'
        ref=self.main_window.results.get('Full Optimization') or self.main_window.results.get('BnB') or max(rs,key=lambda r:(r.total_flow,-r.total_cost))
        fastest=min(rs,key=lambda r:r.runtime_seconds)
        best=max(rs,key=lambda r:(r.total_flow,-r.total_cost))
        lines=[
            f'Nghiệm tham chiếu: {ref.algorithm} với flow={ref.total_flow}, cost={ref.total_cost:.2f}.',
            f'Thuật toán nhanh nhất theo runtime trung bình: {fastest.algorithm} ({fastest.runtime_seconds:.6f}s).',
            f'Thuật toán có nghiệm tốt nhất: {best.algorithm}.'
        ]
        basic=self.main_window.results.get('Basic Backtracking')
        bb=self.main_window.results.get('BnB')
        if basic and bb and basic.extra.get('states_visited',0):
            red=(1-bb.extra.get('states_visited',0)/basic.extra.get('states_visited',1))*100
            lines.append(f'Branch and Bound giảm khoảng {red:.2f}% số trạng thái so với Basic.')
        cs=self.main_window.results.get('Cuckoo Search')
        if cs and ref.total_flow>0:
            lines.append(f'Cuckoo Search sai số luồng so với tham chiếu: {abs(ref.total_flow-cs.total_flow)/ref.total_flow*100:.2f}%.')
        return '\n'.join(lines)
    def refresh(self):
        # Cập nhật lại bảng so sánh.
        rs=list(self.main_window.results.values())
        ref=self.main_window.results.get('Full Optimization') or self.main_window.results.get('BnB') or (max(rs,key=lambda r:(r.total_flow,-r.total_cost)) if rs else None)
        self.table.setRowCount(len(rs))
        for row,r in enumerate(rs):
            err=abs(ref.total_flow-r.total_flow)/ref.total_flow*100 if ref and ref.total_flow else 0
            vals=[
                r.algorithm,
                r.total_flow,
                f'{r.total_cost:.2f}',
                f'{r.runtime_seconds:.6f}',
                r.extra.get('benchmark_runs',1),
                r.extra.get('states_visited','-'),
                r.extra.get('recursive_calls','-'),
                r.extra.get('pruned_branches','-'),
                r.extra.get('path_count','-'),
                f'{err:.2f}'
            ]
            for c,v in enumerate(vals):
                self.table.setItem(row,c,QTableWidgetItem(str(v)))
        self.remark.setText(self.build_comparison_text().replace('\n','<br>'))
