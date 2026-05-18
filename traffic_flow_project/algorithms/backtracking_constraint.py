from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, List, Tuple
from functools import lru_cache
from models.graph_model import GraphModel, PathData, SolutionSummary

@dataclass
class Stats:
    states_visited:int=0
    recursive_calls:int=0
    pruned_branches:int=0


class ConstraintPropagationBacktrackingSolver:
    """Constraint Propagation tự cài đặt từ đầu.

    Ở mỗi bước, thuật toán cập nhật miền giá trị khả thi của path hiện tại
    dựa trên residual capacity của các cạnh và demand còn lại.
    """
    def __init__(self, graph_model:GraphModel, max_paths:int=20, max_logs:int=500):
        # Khởi tạo dữ liệu cho Constraint Propagation.
        self.g=graph_model; self.paths=self.g.simple_paths(max_paths=max_paths); self.caps=self.g.edge_capacity_map()
        self.stats=Stats(); self.logs=[]; self.max_logs=max_logs; self.best_flow=-1; self.best_cost=float('inf'); self.best=[0]*len(self.paths)
    def log(self,msg:str):
        # Ghi log quá trình lan truyền ràng buộc.
        if len(self.logs)<self.max_logs: self.logs.append(msg)
    def better(self,f:
        # Kiểm tra nghiệm mới có tốt hơn nghiệm hiện tại.
        int,c:float)->bool: return f>self.best_flow or (f==self.best_flow and c<self.best_cost)
    def max_feasible(self,p:PathData,usage:Dict[Tuple[str,str],int],remaining:int)->int:
        # Cập nhật miền flow khả thi theo capacity còn lại.
        if remaining<=0: return 0
        return max(0,min([remaining]+[self.caps[e]-usage.get(e,0) for e in p.edges]))
    def solve(self)->SolutionSummary:
        # Điều khiển quá trình giải bằng Constraint Propagation.
        started=perf_counter(); assign=[0]*len(self.paths); usage:Dict[Tuple[str,str],int]={}
        if not self.paths: return SolutionSummary('Constraint Propagation',0,0.0,0.0,{},[],{"log_text":"Không có path.","path_count":0})
        self._backtrack(0,0,0.0,assign,usage)
        runtime=perf_counter()-started
        if self.best_flow<0: self.best_flow=0; self.best_cost=0.0; self.best=[0]*len(self.paths)
        ev=self.g.evaluate_path_flows(self.paths,self.best,clip_to_demand=True); pf=[(p,int(f)) for p,f in zip(self.paths,self.best) if f>0]
        return SolutionSummary('Constraint Propagation',int(ev['total_flow']),float(ev['total_cost']),runtime,{k:int(v) for k,v in ev['edge_usage'].items()},pf,{"states_visited":self.stats.states_visited,"recursive_calls":self.stats.recursive_calls,"pruned_branches":self.stats.pruned_branches,"path_count":len(self.paths),"log_text":"\n".join(self.logs)})
    def _backtrack(self,i:int,flow:int,cost:float,assign:List[int],usage:Dict[Tuple[str,str],int]):
        # Đệ quy với miền giá trị đã được thu hẹp.
        self.stats.recursive_calls+=1
        if flow>self.g.demand: self.stats.pruned_branches+=1; return
        if i==len(self.paths) or flow==self.g.demand:
            self.stats.states_visited+=1
            if self.better(flow,cost): self.best_flow=flow; self.best_cost=cost; self.best=assign.copy(); self.log(f'Cập nhật best: flow={flow}, cost={cost:.2f}, assign={assign}')
            return
        p=self.paths[i]; max_amount=self.max_feasible(p,usage,self.g.demand-flow)
        for amount in range(max_amount,-1,-1):
            if amount>0:
                for e in p.edges: usage[e]=usage.get(e,0)+amount
            assign[i]=amount
            self._backtrack(i+1,flow+amount,cost+amount*p.cost,assign,usage)
            assign[i]=0
            if amount>0:
                for e in p.edges:
                    usage[e]-=amount
                    if usage[e]==0: usage.pop(e)
