from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, List, Tuple
import math, random
from models.graph_model import GraphModel, PathData, SolutionSummary
@dataclass
class CuckooConfig:
    nests:int=25; iterations:int=120; alpha:float=0.35; pa:float=0.25; penalty:float=80.0; seed:int=42; w_flow:float=10000.0; w_cost:float=1.0
class CuckooSearchFlowSolver:
    def __init__(self,graph_model:GraphModel,config:CuckooConfig|None=None,max_paths:int=30):
        # Khởi tạo tham số và quần thể cho Cuckoo Search.
        self.g=graph_model; self.config=config or CuckooConfig(); self.r=random.Random(self.config.seed); self.paths=self.g.simple_paths(max_paths=max_paths); self.caps=self.g.edge_capacity_map(); self.logs=[]
    def log(self,s):
        # Ghi log quá trình tiến hóa nghiệm.
        if len(self.logs)<700: self.logs.append(s)
    def edge_usage(self,v:List[float])->Dict[Tuple[str,str],float]:
        # Tính mức sử dụng cạnh từ vector nghiệm.
        u={}
        for p,a in zip(self.paths,v):
            if a>0:
                for e in p.edges: u[e]=u.get(e,0.0)+a
        return u
    def repair(self,v:List[float])->List[float]:
        # Sửa vector nghiệm để thỏa capacity và demand.
        """Sửa nghiệm Cuckoo để nghiệm báo cáo luôn hợp lệ.

        Bản v4 sửa lỗi quan trọng: sau bước làm tròn số nguyên, nghiệm có thể
        phát sinh vi phạm capacity cạnh. Vì vậy cần vòng lặp giảm flow cho tới
        khi hết vi phạm demand/capacity.
        """
        if not self.paths: return []
        x=[min(max(0.0,a),p.capacity) for a,p in zip(v,self.paths)]
        s=sum(x)
        if s>self.g.demand and s>0: x=[a*self.g.demand/s for a in x]
        for _ in range(10):
            changed=False; usage=self.edge_usage(x)
            for e,u in usage.items():
                if u>self.caps[e]+1e-9:
                    ratio=self.caps[e]/u; changed=True
                    for i,p in enumerate(self.paths):
                        if e in p.edges: x[i]*=ratio
            if not changed: break
        x=[float(max(0,int(round(a)))) for a in x]

        # Sau khi làm tròn, bắt buộc sửa lại cho hợp lệ tuyệt đối.
        # Luôn giảm path có cost cao nhất trong nhóm gây vi phạm để giảm thiệt hại mục tiêu min-cost.
        guard=0
        while guard<10000:
            guard+=1
            usage=self.edge_usage(x)
            bad_edges=[e for e,u in usage.items() if u>self.caps[e]]
            if sum(x)<=self.g.demand and not bad_edges:
                break
            candidates=[]
            if sum(x)>self.g.demand:
                candidates=[i for i,val in enumerate(x) if val>0]
            else:
                bad=set(bad_edges)
                candidates=[i for i,(p,val) in enumerate(zip(self.paths,x)) if val>0 and any(e in bad for e in p.edges)]
            if not candidates: break
            idx=max(candidates, key=lambda i:(self.paths[i].cost, len(self.paths[i].nodes)))
            x[idx]=max(0.0,x[idx]-1.0)
        return x
    def eval(self,v:List[float])->dict:
        # Tính fitness của một nghiệm Cuckoo Search.
        rv=self.repair(v); ev=self.g.evaluate_path_flows(self.paths,rv,clip_to_demand=True); raw=self.g.evaluate_path_flows(self.paths,v,clip_to_demand=False)
        fitness=self.config.w_flow*float(ev['total_flow'])-self.config.w_cost*float(ev['total_cost'])-self.config.penalty*(float(raw['capacity_violation'])+float(raw['demand_violation'])+1000*float(ev['capacity_violation'])+1000*float(ev['demand_violation']))
        return {'fitness':fitness,'vector':rv,'flow':int(ev['total_flow']),'cost':float(ev['total_cost']),'edge_usage':{k:int(round(val)) for k,val in ev['edge_usage'].items()}}
    def levy(self,beta=1.5)->float:
        # Sinh bước nhảy Levy flight ngẫu nhiên.
        u=self.r.gauss(0,1); vv=abs(self.r.gauss(0,1))**(1/beta) or 1e-6; return u/vv
    def random_vec(self)->List[float]:
        # Tạo một nghiệm ban đầu ngẫu nhiên.
        return self.repair([self.r.uniform(0,max(1,p.capacity)) for p in self.paths])
    def solve(self)->SolutionSummary:
        # Điều khiển toàn bộ quá trình Cuckoo Search.
        st=perf_counter()
        if not self.paths: return SolutionSummary('Cuckoo Search',0,0.0,0.0,{},[],{'history':[], 'log_text':'Không có path.'})
        nests=[self.random_vec() for _ in range(self.config.nests)]; evals=[self.eval(n) for n in nests]; best=max(evals,key=lambda z:z['fitness']); hist=[float(best['fitness'])]
        for it in range(self.config.iterations):
            for i,cur in enumerate(nests):
                step=self.config.alpha*self.levy(); cand=[a + step*(a-float(best['vector'][j])) + self.r.uniform(-1,1) for j,a in enumerate(cur)]
                ce=self.eval(cand)
                if ce['fitness']>evals[i]['fitness']: nests[i]=list(ce['vector']); evals[i]=ce
            worst=sorted(range(len(evals)),key=lambda i:evals[i]['fitness'])[:max(1,int(self.config.pa*self.config.nests))]
            for i in worst:
                if self.r.random()<self.config.pa: nests[i]=self.random_vec(); evals[i]=self.eval(nests[i])
            cb=max(evals,key=lambda z:z['fitness'])
            if cb['fitness']>best['fitness']: best=cb
            hist.append(float(best['fitness'])); self.log(f'Iteration {it+1}: fitness={best["fitness"]:.2f}, flow={best["flow"]}, cost={best["cost"]:.2f}')
        pf=[(p,int(f)) for p,f in zip(self.paths,best['vector']) if f>0]
        return SolutionSummary('Cuckoo Search',int(best['flow']),float(best['cost']),perf_counter()-st,best['edge_usage'],pf,{'best_fitness':float(best['fitness']),'history':hist,'path_count':len(self.paths),'config':self.config.__dict__,'log_text':'\n'.join(self.logs)})
