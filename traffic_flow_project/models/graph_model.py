from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import json
from pathlib import Path

@dataclass
class EdgeData:
    from_node: str
    to_node: str
    capacity: int
    cost: float
    def key(self)->Tuple[str,str]:
        # Trả về khóa định danh của cạnh.
        return (self.from_node,self.to_node)
    def to_dict(self)->dict:
        # Chuyển dữ liệu sang dạng dictionary.
        return {"from":self.from_node,"to":self.to_node,"capacity":self.capacity,"cost":self.cost}

@dataclass
class PathData:
    nodes: List[str]
    edges: List[Tuple[str,str]]
    capacity: int
    cost: float
    def to_text(self)->str:
        # Ghép các nút thành chuỗi đường đi.
        return " -> ".join(self.nodes)

@dataclass
class SolutionSummary:
    algorithm: str
    total_flow: int
    total_cost: float
    runtime_seconds: float
    edge_usage: Dict[Tuple[str,str], int]
    path_flows: List[Tuple[PathData,int]]
    extra: Dict[str, object]
    def to_dict(self)->dict:
        # Chuyển dữ liệu sang dạng dictionary.
        return {
            "algorithm": self.algorithm,
            "total_flow": self.total_flow,
            "total_cost": self.total_cost,
            "runtime_seconds": self.runtime_seconds,
            "edge_usage": {f"{u}->{v}":f for (u,v),f in self.edge_usage.items()},
            "path_flows": [{"path":p.to_text(),"flow":f,"capacity":p.capacity,"cost":p.cost} for p,f in self.path_flows],
            "extra": self.extra,
        }

class GraphModel:
    def __init__(self, edges:List[EdgeData], source:str, sink:str, demand:int, nodes:Optional[List[str]]=None)->None:
        # Khởi tạo đồ thị với cạnh, source, sink và demand.
        self.edges=edges; self.source=source.strip(); self.sink=sink.strip(); self.demand=int(demand); self._nodes=nodes or []
    @property
    def nodes(self)->List[str]:
        # Lấy danh sách nút của đồ thị.
        s=set(self._nodes)
        for e in self.edges: s.add(e.from_node); s.add(e.to_node)
        return sorted(x for x in s if str(x).strip())
    def adjacency(self)->Dict[str,List[EdgeData]]:
        # Tạo danh sách kề phục vụ duyệt đường đi.
        adj={n:[] for n in self.nodes}
        for e in self.edges: adj.setdefault(e.from_node,[]).append(e)
        return adj
    def edge_capacity_map(self)->Dict[Tuple[str,str],int]:
        # Tạo bảng tra capacity theo từng cạnh.
        return {e.key():int(e.capacity) for e in self.edges}
    def edge_cost_map(self)->Dict[Tuple[str,str],float]:
        # Tạo bảng tra cost theo từng cạnh.
        return {e.key():float(e.cost) for e in self.edges}
    def validate(self)->List[str]:
        # Kiểm tra tính hợp lệ của dữ liệu đầu vào.
        errors=[]; seen=set()
        if not self.edges: errors.append('Đồ thị chưa có cạnh nào.')
        if not self.source or not self.sink: errors.append('Source và sink không được để trống.')
        if self.source==self.sink: errors.append('Source và sink phải khác nhau.')
        if self.demand<=0: errors.append('Demand phải > 0.')
        for i,e in enumerate(self.edges,1):
            if not e.from_node or not e.to_node: errors.append(f'Cạnh dòng {i} thiếu from/to.')
            if e.from_node==e.to_node: errors.append(f'Cạnh {e.from_node}->{e.to_node} là self-loop.')
            if e.capacity<0: errors.append(f'Cạnh {e.from_node}->{e.to_node} capacity âm.')
            if e.cost<0: errors.append(f'Cạnh {e.from_node}->{e.to_node} cost âm.')
            if e.key() in seen: errors.append(f'Cạnh {e.from_node}->{e.to_node} bị trùng.')
            seen.add(e.key())
        if self.source and self.source not in self.nodes: errors.append('Source không tồn tại trong node.')
        if self.sink and self.sink not in self.nodes: errors.append('Sink không tồn tại trong node.')
        if not errors and not self.simple_paths(max_paths=1):
            errors.append('Không có đường đi từ source đến sink.')
        if not errors:
            max_flow = self.max_possible_flow()
            if self.demand > max_flow:
                errors.append(
                    f'Demand = {self.demand} lớn hơn luồng tối đa mạng có thể vận chuyển = {max_flow}. '
                    f'Vui lòng giảm demand hoặc tăng capacity/thêm cạnh.'
                )
        return errors

    def max_possible_flow(self) -> int:
        # Tính luồng tối đa mạng có thể vận chuyển.
        """Tính luồng tối đa khả thi từ source đến sink bằng Edmonds-Karp tự cài đặt.

        Hàm này chỉ dùng để kiểm tra dữ liệu đầu vào: nếu demand lớn hơn
        khả năng vận chuyển tối đa của mạng thì báo lỗi ngay, tránh chạy thuật toán
        trong trường hợp chắc chắn không thể đáp ứng đủ nhu cầu.
        Không dùng networkx.max_flow hoặc thư viện tối ưu.
        """
        nodes = self.nodes
        if self.source not in nodes or self.sink not in nodes:
            return 0

        residual: Dict[str, Dict[str, int]] = {n: {} for n in nodes}
        for e in self.edges:
            if e.capacity <= 0:
                continue
            residual.setdefault(e.from_node, {})
            residual.setdefault(e.to_node, {})
            residual[e.from_node][e.to_node] = residual[e.from_node].get(e.to_node, 0) + int(e.capacity)
            residual[e.to_node].setdefault(e.from_node, 0)

        max_flow = 0
        while True:
            parent: Dict[str, str | None] = {self.source: None}
            queue = [self.source]
            head = 0
            while head < len(queue) and self.sink not in parent:
                u = queue[head]
                head += 1
                for v, cap in residual.get(u, {}).items():
                    if cap > 0 and v not in parent:
                        parent[v] = u
                        queue.append(v)
                        if v == self.sink:
                            break

            if self.sink not in parent:
                break

            bottleneck = 10**18
            v = self.sink
            while v != self.source:
                u = parent[v]
                assert u is not None
                bottleneck = min(bottleneck, residual[u][v])
                v = u

            v = self.sink
            while v != self.source:
                u = parent[v]
                assert u is not None
                residual[u][v] -= bottleneck
                residual[v][u] = residual[v].get(u, 0) + bottleneck
                v = u

            max_flow += int(bottleneck)

        return int(max_flow)

    def simple_paths(self,max_paths:int=30,cutoff:Optional[int]=None)->List[PathData]:
        # Liệt kê các đường đi đơn giản từ source đến sink.
        """Liệt kê simple paths theo cách cân bằng.

        Bản v6 sửa lỗi quan trọng của mẫu lớn: bản cũ dừng ngay khi đủ max_paths
        trong DFS nên có thể lấy quá nhiều đường bắt đầu bằng cùng một nhánh
        (ví dụ chỉ S->A), làm tổng flow không thể đạt demand dù đồ thị thật có đủ năng lực.

        Cách mới:
        1) Liệt kê toàn bộ simple path trong giới hạn cutoff.
        2) Chọn path theo round-robin trên cạnh đầu tiên từ source để các nhánh S->A,
           S->B, S->C... đều được đại diện.
        3) Nếu vẫn còn thiếu, bổ sung theo cost thấp/capacity cao.
        """
        adj=self.adjacency(); cutoff=cutoff or max(2,len(self.nodes)); all_paths:List[PathData]=[]
        def dfs(u:str, visited:set, ns:List[str], es:List[Tuple[str,str]], cap:int, cost:float):
            # Duyệt DFS để sinh từng đường đi đơn giản.
            if len(ns)>cutoff+1: return
            if u==self.sink:
                all_paths.append(PathData(ns.copy(), es.copy(), cap if es else 0, cost)); return
            for e in sorted(adj.get(u,[]), key=lambda x:(x.cost,-x.capacity,x.to_node)):
                if e.to_node in visited: continue
                visited.add(e.to_node); ns.append(e.to_node); es.append(e.key())
                dfs(e.to_node, visited, ns, es, min(cap,e.capacity) if es[:-1] else e.capacity, cost+e.cost)
                es.pop(); ns.pop(); visited.remove(e.to_node)
        dfs(self.source,{self.source},[self.source],[],10**9,0.0)
        all_paths.sort(key=lambda p:(p.cost,-p.capacity,len(p.nodes),p.to_text()))
        if len(all_paths)<=max_paths:
            return all_paths

        groups:Dict[Tuple[str,str],List[PathData]]={}
        for p in all_paths:
            first=p.edges[0] if p.edges else ('','')
            groups.setdefault(first,[]).append(p)
        selected:List[PathData]=[]; used=set()
        # Round-robin theo cạnh xuất phát để không bỏ sót nhánh có capacity lớn.
        while len(selected)<max_paths:
            added=False
            for key in sorted(groups.keys(), key=lambda e:(e[0],e[1])):
                bucket=groups[key]
                while bucket and bucket[0].to_text() in used:
                    bucket.pop(0)
                if bucket and len(selected)<max_paths:
                    p=bucket.pop(0); selected.append(p); used.add(p.to_text()); added=True
            if not added: break
        for p in all_paths:
            if len(selected)>=max_paths: break
            if p.to_text() not in used:
                selected.append(p); used.add(p.to_text())
        selected.sort(key=lambda p:(p.cost,-p.capacity,len(p.nodes),p.to_text()))
        return selected[:max_paths]
    def evaluate_path_flows(self, paths:List[PathData], path_flows:Iterable[float], clip_to_demand:bool=False)->Dict[str,object]:
        # Tính flow, cost và mức sử dụng cạnh của một nghiệm.
        flows=[max(0.0,float(x)) for x in path_flows]
        usage:Dict[Tuple[str,str],float]={}; total=sum(flows); cost=0.0
        for p,a in zip(paths,flows):
            if a<=0: continue
            cost += a*p.cost
            for ed in p.edges: usage[ed]=usage.get(ed,0.0)+a
        caps=self.edge_capacity_map(); cap_v=sum(max(0.0,u-caps.get(e,0)) for e,u in usage.items()); dem_v=max(0.0,total-self.demand)
        return {"total_flow":min(total,self.demand) if clip_to_demand else total,"raw_total_flow":total,"total_cost":cost,"edge_usage":usage,"capacity_violation":cap_v,"demand_violation":dem_v,"valid":cap_v==0 and dem_v==0}
    def to_json_dict(self)->dict:
        # Đóng gói đồ thị thành dữ liệu JSON.
        return {"nodes":self.nodes,"source":self.source,"sink":self.sink,"demand":self.demand,"edges":[e.to_dict() for e in self.edges]}
    @staticmethod
    def from_json_dict(d:dict)->'GraphModel':
        # Tạo GraphModel từ dữ liệu JSON.
        return GraphModel([EdgeData(str(x.get('from','')).strip(),str(x.get('to','')).strip(),int(x.get('capacity',0)),float(x.get('cost',0))) for x in d.get('edges',[])], str(d.get('source','')).strip(), str(d.get('sink','')).strip(), int(d.get('demand',0)), [str(x) for x in d.get('nodes',[])])
    @staticmethod
    def load_json(path:
        # Đọc dữ liệu đồ thị từ file JSON.
        str|Path)->'GraphModel': return GraphModel.from_json_dict(json.loads(Path(path).read_text(encoding='utf-8')))
    def save_json(self,path:
        # Lưu dữ liệu đồ thị ra file JSON.
        str|Path)->None: Path(path).write_text(json.dumps(self.to_json_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
