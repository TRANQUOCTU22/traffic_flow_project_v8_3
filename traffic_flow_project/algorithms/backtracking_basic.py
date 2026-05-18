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


class BasicBacktrackingSolver:
    """Basic Backtracking tự cài đặt từ đầu.

    Phiên bản này vẫn đi theo mô hình path-flow và tự duyệt lượng flow cho từng path.
    Để giữ chương trình chạy được khi demo, hàm đệ quy có ghi nhớ trạng thái
    (index, remaining_demand, edge_usage). Đây không phải hàm tối ưu có sẵn,
    mà là tự cài đặt cơ chế tránh tính lặp lại trong quay lui.
    """
    def __init__(self, graph_model:GraphModel, max_paths:int=20, max_logs:int=500):
        # Khởi tạo dữ liệu cho Basic Backtracking.
        self.g=graph_model
        self.paths=self.g.simple_paths(max_paths=max_paths)
        self.caps=self.g.edge_capacity_map()
        self.edge_order=list(self.caps.keys())
        self.edge_index={e:i for i,e in enumerate(self.edge_order)}
        self.stats=Stats(); self.logs=[]; self.max_logs=max_logs
        self.best_flow=-1; self.best_cost=float('inf'); self.best=[0]*len(self.paths)

    def log(self,msg:str):
        # Ghi log quá trình duyệt nghiệm.
        if len(self.logs)<self.max_logs: self.logs.append(msg)

    def solve(self)->SolutionSummary:
        # Điều khiển quá trình giải bằng Basic Backtracking.
        started=perf_counter()
        if not self.paths:
            return SolutionSummary('Basic Backtracking',0,0.0,0.0,{},[],{"log_text":"Không có path.","path_count":0})
        self._backtrack_with_memo()
        runtime=perf_counter()-started
        ev=self.g.evaluate_path_flows(self.paths,self.best,clip_to_demand=True)
        pf=[(p,int(f)) for p,f in zip(self.paths,self.best) if f>0]
        return SolutionSummary('Basic Backtracking',int(ev['total_flow']),float(ev['total_cost']),runtime,{k:int(v) for k,v in ev['edge_usage'].items()},pf,{"states_visited":self.stats.states_visited,"recursive_calls":self.stats.recursive_calls,"pruned_branches":self.stats.pruned_branches,"path_count":len(self.paths),"log_text":"\n".join(self.logs)})

    def _backtrack_with_memo(self):
        # Duyệt toàn bộ phân phối flow bằng quy hoạch nhớ.
        zero_usage=tuple(0 for _ in self.edge_order)
        n=len(self.paths)
        def better(a,b):
            # So sánh hai nghiệm theo flow và cost.
            if a[0]!=b[0]: return a if a[0]>b[0] else b
            return a if a[1]<=b[1] else b
        @lru_cache(maxsize=None)
        def rec(i:int, remaining:int, usage_tuple:Tuple[int,...]):
            # Đệ quy thử từng mức flow cho mỗi path.
            self.stats.recursive_calls+=1
            if i==n or remaining<=0:
                self.stats.states_visited+=1
                return (0,0.0,tuple())
            p=self.paths[i]
            max_amount=min(p.capacity, remaining)
            best=(0,0.0,(0,))
            for amount in range(max_amount,-1,-1):
                usage=list(usage_tuple); feasible=True
                if amount>0:
                    for e in p.edges:
                        pos=self.edge_index[e]; usage[pos]+=amount
                        if usage[pos]>self.caps[e]: feasible=False
                    if not feasible:
                        self.stats.pruned_branches+=1
                        continue
                sf,sc,ss=rec(i+1, remaining-amount, tuple(usage))
                cand=(amount+sf, amount*p.cost+sc, (amount,)+ss)
                best=better(best,cand)
            return best
        flow,cost,assign=rec(0,self.g.demand,zero_usage)
        self.best_flow=int(flow); self.best_cost=float(cost); self.best=list(assign)+[0]*(n-len(assign))
        self.log(f'Cập nhật best: flow={self.best_flow}, cost={self.best_cost:.2f}, assign={self.best}')
        self.log(f'Memoization: {rec.cache_info()}')
