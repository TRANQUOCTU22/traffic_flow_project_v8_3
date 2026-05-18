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


class BackwardCheckingBacktrackingSolver:
    """BC - Backward Checking .

    Ý tưởng lý thuyết: sinh phương án rồi kiểm tra ràng buộc ở cuối. Để demo không bị treo,
    thuật toán vẫn tự cài memoization trên trạng thái còn lại giống quay lui có ghi nhớ.
    Phần kiểm tra hợp lệ nghiệm được thực hiện qua usage/capacity trong quá trình đánh giá trạng thái.
    """
    def __init__(self, graph_model:GraphModel, max_paths:int=20, max_logs:int=500):
        # Khởi tạo dữ liệu cho Backward Checking.
        self.g=graph_model; self.paths=self.g.simple_paths(max_paths=max_paths); self.caps=self.g.edge_capacity_map()
        self.edge_order=list(self.caps.keys()); self.edge_index={e:i for i,e in enumerate(self.edge_order)}
        self.stats=Stats(); self.logs=[]; self.max_logs=max_logs; self.best_flow=-1; self.best_cost=float('inf'); self.best=[0]*len(self.paths)
    def log(self,msg:str):
        # Ghi log quá trình sinh và kiểm tra nghiệm.
        if len(self.logs)<self.max_logs: self.logs.append(msg)
    def solve(self)->SolutionSummary:
        # Điều khiển quá trình giải bằng Backward Checking.
        started=perf_counter()
        if not self.paths: return SolutionSummary('BC',0,0.0,0.0,{},[],{"log_text":"Không có path.","path_count":0})
        self._enumerate_with_memo()
        runtime=perf_counter()-started
        ev=self.g.evaluate_path_flows(self.paths,self.best,clip_to_demand=True); pf=[(p,int(f)) for p,f in zip(self.paths,self.best) if f>0]
        return SolutionSummary('BC',int(ev['total_flow']),float(ev['total_cost']),runtime,{k:int(v) for k,v in ev['edge_usage'].items()},pf,{"states_visited":self.stats.states_visited,"recursive_calls":self.stats.recursive_calls,"pruned_branches":self.stats.pruned_branches,"path_count":len(self.paths),"log_text":"\n".join(self.logs)})
    def _enumerate_with_memo(self):
        # Sinh nghiệm trước rồi kiểm tra ràng buộc sau.
        zero_usage=tuple(0 for _ in self.edge_order); n=len(self.paths)
        def better(a,b):
            # So sánh hai nghiệm theo flow và cost.
            if a[0]!=b[0]: return a if a[0]>b[0] else b
            return a if a[1]<=b[1] else b
        @lru_cache(maxsize=None)
        def rec(i:int, remaining:int, usage_tuple:Tuple[int,...]):
            # Đệ quy sinh phân phối flow cho các path.
            self.stats.recursive_calls+=1
            if i==n or remaining<=0:
                self.stats.states_visited+=1; return (0,0.0,tuple())
            p=self.paths[i]; best=(0,0.0,(0,))
            for amount in range(min(p.capacity,remaining),-1,-1):
                usage=list(usage_tuple); feasible=True
                # Backward-style baseline: amount được sinh trước, sau đó kiểm tra toàn bộ edge của path.
                for e in p.edges:
                    pos=self.edge_index[e]; usage[pos]+=amount
                    if usage[pos]>self.caps[e]: feasible=False
                if not feasible:
                    self.stats.pruned_branches+=1; continue
                sf,sc,ss=rec(i+1,remaining-amount,tuple(usage))
                best=better(best,(amount+sf,amount*p.cost+sc,(amount,)+ss))
            return best
        f,c,a=rec(0,self.g.demand,zero_usage)
        self.best_flow=int(f); self.best_cost=float(c); self.best=list(a)+[0]*(n-len(a))
        self.log(f'Cập nhật best: flow={self.best_flow}, cost={self.best_cost:.2f}, assign={self.best}')
        self.log(f'Memoization: {rec.cache_info()}')
