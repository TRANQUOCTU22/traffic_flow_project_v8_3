from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QTextEdit,QSpinBox,QComboBox,QFormLayout,QGroupBox,QMessageBox
from PySide6.QtCore import QCoreApplication
from algorithms.backtracking_basic import BasicBacktrackingSolver
from algorithms.backtracking_forward import ForwardCheckingBacktrackingSolver
from algorithms.backtracking_backward import BackwardCheckingBacktrackingSolver
from algorithms.backtracking_branch_bound import BranchBoundBacktrackingSolver
from algorithms.backtracking_heuristic import HeuristicBacktrackingSolver
from algorithms.backtracking_constraint import ConstraintPropagationBacktrackingSolver
from algorithms.backtracking_full import FullOptimizationBacktrackingSolver

SOLVERS={
    'Basic Backtracking':BasicBacktrackingSolver,
    'FC':ForwardCheckingBacktrackingSolver,
    'BC':BackwardCheckingBacktrackingSolver,
    'BnB':BranchBoundBacktrackingSolver,
    'Heuristic':HeuristicBacktrackingSolver,
    'Constraint Propagation':ConstraintPropagationBacktrackingSolver,
    'Full Optimization':FullOptimizationBacktrackingSolver,
}

class BacktrackingTab(QWidget):
    def __init__(self,main_window):
        # Khởi tạo tab chạy các thuật toán Backtracking.
        super().__init__(); self.main_window=main_window; self._build()

    def _build(self):
        # Tạo giao diện cấu hình Backtracking.
        l=QVBoxLayout(self); l.addWidget(QLabel('Chạy các biến thể Backtracking'))
        box=QGroupBox('Cấu hình'); f=QFormLayout(box)
        self.alg=QComboBox(); self.alg.addItems(SOLVERS.keys())
        self.max_paths=QSpinBox(); self.max_paths.setRange(1,120); self.max_paths.setValue(12)
        self.runs=QSpinBox(); self.runs.setRange(1,100); self.runs.setValue(1)
        f.addRow('Thuật toán:',self.alg)
        f.addRow('Max paths:',self.max_paths)
        f.addRow('Số lần chạy lấy trung bình:',self.runs)
        l.addWidget(box)

        note=QLabel('Runtime hiển thị là thời gian trung bình của N lần chạy. Thuật toán giữ nguyên; chương trình chỉ chạy lặp lại để đo hiệu năng ổn định hơn.')
        note.setWordWrap(True); note.setStyleSheet('background:#fff7ed;padding:8px;border-radius:8px')
        l.addWidget(note)

        row=QHBoxLayout()
        b=QPushButton('Chạy Backtracking'); b.clicked.connect(self.run_one); row.addWidget(b)
        b2=QPushButton('Chạy tất cả Backtracking'); b2.clicked.connect(self.run_all); row.addWidget(b2)
        l.addLayout(row)
        self.summary=QLabel('Chưa có kết quả'); self.summary.setWordWrap(True); l.addWidget(self.summary)
        self.log=QTextEdit(); self.log.setReadOnly(True); l.addWidget(self.log)

    def run_solver(self,cls):
        # Chạy solver Backtracking được chọn.
        g=self.main_window.graph_model
        n=max(1,self.runs.value())
        results=[]
        for i in range(n):
            r=cls(g,self.max_paths.value()).solve()
            results.append(r)
            QCoreApplication.processEvents()
        # Giữ nghiệm tốt nhất theo flow/cost, nhưng runtime là trung bình nhiều lần.
        best=max(results,key=lambda x:(x.total_flow,-x.total_cost))
        avg_runtime=sum(x.runtime_seconds for x in results)/n
        best.runtime_seconds=avg_runtime
        best.extra['benchmark_runs']=n
        best.extra['runtime_runs']=[x.runtime_seconds for x in results]
        best.extra['runtime_avg_seconds']=avg_runtime
        best.extra['runtime_min_seconds']=min(x.runtime_seconds for x in results)
        best.extra['runtime_max_seconds']=max(x.runtime_seconds for x in results)
        self.main_window.save_result(best)
        return best

    def show(self,r):
        # Hiển thị kết quả Backtracking lên giao diện.
        paths='\n'.join(f'- {p.to_text()} | flow={f} | cost={p.cost}' for p,f in r.path_flows) or 'Không chọn path'
        n=r.extra.get('benchmark_runs',1)
        self.summary.setText(
            f'<b>{r.algorithm}</b><br>'
            f'Flow={r.total_flow} | Cost={r.total_cost:.2f} | Runtime avg={r.runtime_seconds:.6f}s | Runs={n}<br>'
            f'States={r.extra.get("states_visited",0)} | Calls={r.extra.get("recursive_calls",0)} | Pruned={r.extra.get("pruned_branches",0)}'
        )
        timing=f'Runtime avg={r.extra.get("runtime_avg_seconds",r.runtime_seconds):.6f}s | min={r.extra.get("runtime_min_seconds",r.runtime_seconds):.6f}s | max={r.extra.get("runtime_max_seconds",r.runtime_seconds):.6f}s | runs={n}'
        self.log.setPlainText(timing+'\n\n'+paths+'\n\n'+str(r.extra.get('log_text','')))

    def run_one(self):
        # Chạy một thuật toán Backtracking đang chọn.
        if not self.main_window.ensure_graph_ready(): return
        r=self.run_solver(SOLVERS[self.alg.currentText()]); self.show(r)

    def run_all(self):
        # Chạy lần lượt tất cả thuật toán Backtracking.
        if not self.main_window.ensure_graph_ready(): return
        if self.max_paths.value()>18:
            QMessageBox.information(self,'Lưu ý thời gian','Khi chạy tất cả với Max paths lớn, Basic/Backward có thể chạy lâu vì ít hoặc không cắt tỉa.')
        last=None
        order=[FullOptimizationBacktrackingSolver,BranchBoundBacktrackingSolver,HeuristicBacktrackingSolver,ConstraintPropagationBacktrackingSolver,ForwardCheckingBacktrackingSolver,BasicBacktrackingSolver,BackwardCheckingBacktrackingSolver]
        for cls in order:
            last=self.run_solver(cls)
            self.show(last)
            QCoreApplication.processEvents()
        if last: self.show(last)
