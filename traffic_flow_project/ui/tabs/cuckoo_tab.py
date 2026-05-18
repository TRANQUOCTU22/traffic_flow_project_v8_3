from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QLabel,QTextEdit,QSpinBox,QDoubleSpinBox,QFormLayout,QGroupBox
from PySide6.QtCore import QCoreApplication
from algorithms.cuckoo_search_flow import CuckooSearchFlowSolver,CuckooConfig
from utils.visualization import MplCanvas,draw_history_on_canvas

class CuckooTab(QWidget):
    def __init__(self,main_window):
        # Khởi tạo tab Cuckoo Search.
        super().__init__(); self.main_window=main_window; self._build()

    def _build(self):
        # Tạo giao diện nhập tham số Cuckoo Search.
        l=QVBoxLayout(self); l.addWidget(QLabel('Chạy Cuckoo Search'))
        box=QGroupBox('Tham số'); f=QFormLayout(box)
        self.max_paths=QSpinBox(); self.max_paths.setRange(1,120); self.max_paths.setValue(12)
        self.nests=QSpinBox(); self.nests.setRange(5,500); self.nests.setValue(25)
        self.iter=QSpinBox(); self.iter.setRange(5,5000); self.iter.setValue(120)
        self.alpha=QDoubleSpinBox(); self.alpha.setRange(.01,10); self.alpha.setValue(.35)
        self.pa=QDoubleSpinBox(); self.pa.setRange(.01,.95); self.pa.setValue(.25)
        self.penalty=QDoubleSpinBox(); self.penalty.setRange(1,10000); self.penalty.setValue(80)
        self.seed=QSpinBox(); self.seed.setRange(0,999999); self.seed.setValue(42)
        self.runs=QSpinBox(); self.runs.setRange(1,100); self.runs.setValue(1)
        for name,w in [('Max paths',self.max_paths),('Nests',self.nests),('Iterations',self.iter),('Alpha',self.alpha),('pa',self.pa),('Penalty',self.penalty),('Seed',self.seed),('Số lần chạy lấy trung bình',self.runs)]:
            f.addRow(name,w)
        l.addWidget(box)
        note=QLabel('Runtime hiển thị là thời gian trung bình của N lần chạy. Kết quả nghiệm lưu lại là nghiệm tốt nhất trong các lần chạy.')
        note.setWordWrap(True); note.setStyleSheet('background:#ecfeff;padding:8px;border-radius:8px')
        l.addWidget(note)
        b=QPushButton('Chạy Cuckoo Search'); b.clicked.connect(self.run); l.addWidget(b)
        self.summary=QLabel('Chưa có kết quả'); self.summary.setWordWrap(True); l.addWidget(self.summary)
        self.canvas=MplCanvas(8,3); l.addWidget(self.canvas)
        self.log=QTextEdit(); self.log.setReadOnly(True); l.addWidget(self.log)

    def run(self):
        # Chạy Cuckoo Search và hiển thị kết quả.
        if not self.main_window.ensure_graph_ready(): return
        n=max(1,self.runs.value())
        results=[]
        for i in range(n):
            # Giữ seed gốc + i để Cuckoo có nhiều lần thử độc lập, nhưng thuật toán không đổi.
            cfg=CuckooConfig(self.nests.value(),self.iter.value(),self.alpha.value(),self.pa.value(),self.penalty.value(),self.seed.value()+i)
            r=CuckooSearchFlowSolver(self.main_window.graph_model,cfg,self.max_paths.value()).solve()
            results.append(r)
            QCoreApplication.processEvents()
        best=max(results,key=lambda x:(x.total_flow,-x.total_cost,x.extra.get('best_fitness',0)))
        avg_runtime=sum(x.runtime_seconds for x in results)/n
        best.runtime_seconds=avg_runtime
        best.extra['benchmark_runs']=n
        best.extra['runtime_runs']=[x.runtime_seconds for x in results]
        best.extra['runtime_avg_seconds']=avg_runtime
        best.extra['runtime_min_seconds']=min(x.runtime_seconds for x in results)
        best.extra['runtime_max_seconds']=max(x.runtime_seconds for x in results)
        best.extra['best_run_seed']=best.extra.get('config',{}).get('seed',self.seed.value())
        self.main_window.save_result(best)
        self.summary.setText(f'<b>Cuckoo Search</b><br>Fitness={best.extra.get("best_fitness",0):.2f} | Flow={best.total_flow} | Cost={best.total_cost:.2f} | Runtime avg={best.runtime_seconds:.6f}s | Runs={n}')
        timing=f'Runtime avg={avg_runtime:.6f}s | min={best.extra["runtime_min_seconds"]:.6f}s | max={best.extra["runtime_max_seconds"]:.6f}s | runs={n}'
        self.log.setPlainText(timing+'\n\n'+'\n'.join(f'- {p.to_text()} | flow={f} | cost={p.cost}' for p,f in best.path_flows)+'\n\n'+str(best.extra.get('log_text','')))
        draw_history_on_canvas(self.canvas,best.extra.get('history',[]),'Lịch sử hội tụ Cuckoo Search')
