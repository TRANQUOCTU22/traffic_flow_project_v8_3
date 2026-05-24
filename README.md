Hướng Tiếp Cận 2: Thuật Toán Cuckoo Search (Tối Ưu Luồng Mạng)

Phần nghiên cứu này tập trung ứng dụng thuật toán tối ưu hóa siêu tiến hóa **Cuckoo Search (CS)** nhằm giải quyết bài toán phân luồng giao thông (Path-Flow) quy mô lớn, khắc phục triệt để nhược điểm bùng nổ tổ hợp của phương pháp Backtracking.

### Các thành phần cốt lõi:
* **Mã hóa nghiệm:** Mỗi tổ chim (Nest) đại diện cho một Vector phân bổ luồng xe $X = [x_1, x_2, ..., x_k]$.
* **Hàm mục tiêu (Fitness Function):** Áp dụng kỹ thuật **Hàm Phạt (Penalty Method)** với trọng số phạt khổng lồ để đào thải ngay lập tức các phương án vi phạm giới hạn sức chứa (Capacity) của cung đường.
* **Cơ chế dịch chuyển:** Sử dụng bước nhảy ngẫu nhiên đuôi nặng **Levy Flight** (thuật toán Mantegna) giúp bầy chim đột biến, dễ dàng thoát khỏi các bẫy cực trị cục bộ (kẹt xe).
* **Cơ chế sửa nghiệm (Repair Solution):** Tự động chuẩn hóa các vector số thực do Levy sinh ra về dạng số nguyên phi âm và cân bằng khớp với tổng cầu (Demand).

### Độ phức tạp tính toán:
Độ phức tạp thời gian được khống chế ở mức đa thức tuyến tính: 
$$\mathcal{O}(N \cdot I \cdot k)$$

*(Trong đó: $N$ là số tổ chim, $I$ là số vòng lặp tối đa, $k$ là số tuyến đường đơn).*
