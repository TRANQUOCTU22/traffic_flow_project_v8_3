# Traffic Flow Optimization - Backtracking & Cuckoo Search

Đồ án môn Trí tuệ nhân tạo: **Giải bài toán tối ưu luồng giao thông / Network Flow** bằng các biến thể Backtracking và Cuckoo Search.

## Điểm chính

- Cài đặt thuật toán từ đầu, không dùng `max_flow` hoặc `min_cost_flow` có sẵn.
- Cùng một bài toán, cùng một input, cùng một dạng nghiệm path-flow.
- Có giao diện desktop PySide6 để nhập dữ liệu, vẽ mạng, chạy thuật toán, so sánh hiệu năng và xuất báo cáo.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy chương trình

```bash
python main.py
```

## Cấu trúc thư mục

```text
traffic_flow_project/
├── main.py
├── requirements.txt
├── README.md
├── models/graph_model.py
├── algorithms/
│   ├── backtracking_basic.py
│   ├── backtracking_forward.py
│   ├── backtracking_backward.py
│   ├── backtracking_branch_bound.py
│   ├── backtracking_heuristic.py
│   ├── backtracking_constraint.py
│   ├── backtracking_full.py
│   └── cuckoo_search_flow.py
├── ui/
│   ├── main_window.py
│   └── tabs/
├── utils/
└── data/
```

## Mô hình dữ liệu

Input là đồ thị có hướng gồm node, edge, source, sink, demand. Mỗi cạnh có `from`, `to`, `capacity`, `cost`.

Nghiệm được biểu diễn theo **path-flow**: liệt kê các đường đi đơn giản từ source đến sink, sau đó gán lượng flow nguyên cho từng path. Từ path-flow tính ra edge usage và kiểm tra capacity/demand.

## Thuật toán

Nhóm Backtracking gồm 7 phiên bản:

1. Basic Backtracking: duyệt toàn bộ cách gán flow.
2. FC: kiểm tra ràng buộc ngay khi gán.
3. BC: sinh nghiệm rồi mới kiểm tra.
4. BnB: cắt nhánh bằng upper bound.
5. Heuristic: ưu tiên path rẻ, capacity cao, ngắn.
6. Constraint Propagation: cập nhật miền flow khả thi theo capacity còn lại.
7. Full Optimization: kết hợp forward checking, pruning, heuristic và constraint propagation.

Cuckoo Search:

- Một nest là vector flow theo path.
- Có repair nghiệm để không vượt demand/capacity.
- Fitness ưu tiên tổng flow lớn, chi phí thấp, phạt vi phạm ràng buộc.
- Có Levy flight, abandon nest xấu và lưu history fitness.

## Cách đọc kết quả

- `total_flow`: tổng luồng đạt được từ source đến sink.
- `total_cost`: tổng chi phí của nghiệm.
- `runtime_seconds`: thời gian chạy.
- `states_visited`: số trạng thái/ nghiệm lá được duyệt.
- `recursive_calls`: số lần gọi đệ quy.
- `pruned_branches`: số nhánh bị cắt.
- `relative_flow_error`: sai số luồng so với nghiệm tham chiếu Full Optimization hoặc BnB.

## Gợi ý demo

1. Nạp mẫu nhỏ, chạy tất cả Backtracking để chứng minh các biến thể cùng giải một bài toán.
2. Nạp mẫu trung bình, so sánh Basic với BnB/Full Optimization.
3. Nạp mẫu lớn, chạy Cuckoo Search để thấy tốc độ tốt hơn, nhưng nghiệm có thể chỉ gần tối ưu.
4. Xuất báo cáo DOCX/TXT/CSV.

