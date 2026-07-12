# Fix: Checkbox "Hiện thread đã dừng" không load được (ThreadDashboard.tsx)

Repo: `CuongMotNang/software-multiagent`, branch `temp`, dựa trên commit `6b71156`
(sau khi bạn đã áp fix #1/#2/#3 lần trước — patch này áp TIẾP lên trên, không đè lại).

Áp bằng:
```bash
cd software-multiagent
git apply fix-thread-dashboard-idle-list.patch
```

## Đã xác nhận KHÔNG phải lỗi

- `status: "idle"` là giá trị hợp lệ theo `ThreadStatus` của LangGraph SDK
  (`Literal["idle", "busy", "interrupted", "error"]`) — tra tài liệu SDK
  chính thức xác nhận, không phải sai tên field.
- `ThreadDashboard.tsx` không bị đụng bởi commit fix trước đó (`d537888`) —
  bug này độc lập, có từ trước.

## Root cause

`loadThreads()` gộp CHUNG 1 `try/catch` cho cả 3 lần gọi `threads.search()`:
```tsx
try {
  const [interruptedResult, busyResult] = await Promise.all([...]);
  let result = [...interruptedResult, ...busyResult];
  if (showIdle) {
    const idleResult = await threadsClient.search({ status: "idle", limit: 50 });
    result = [...result, ...idleResult];
  }
  ...
  setThreads(filtered);
} catch (e) {
  console.error("[ThreadDashboard] load error", e);   // im lặng, không hiện UI
}
```

Nếu request `status: "idle"` lỗi vì bất kỳ lý do gì (timeout, backend tạm
trục trặc, v.v.), toàn bộ `catch` bắt lỗi → `setThreads()` **không bao giờ
được gọi** → kể cả kết quả `interrupted`/`busy` đã fetch thành công cũng bị
vứt bỏ theo. Lỗi chỉ `console.error`, không hiện gì lên UI, nên trải nghiệm
đúng là "bấm vào checkbox là không có được" — không rõ vì sao.

Thêm vào đó, `useEffect` tắt hẳn auto-refresh 10s khi `showIdle === true`:
```tsx
if (showIdle) return;   // không set interval nữa
```
→ nếu lần load đầu tiên dính lỗi trên, danh sách đứng yên mãi, không có cơ
chế tự thử lại — phải tick/untick lại checkbox thủ công.

## Fix

**`frontend/ui-review/src/components/ThreadDashboard.tsx`**
1. Tách fetch `idle` ra khỏi `try/catch` của `interrupted`/`busy` — nếu
   `idle` lỗi, vẫn giữ nguyên + hiển thị kết quả `interrupted`/`busy` đã có,
   không xoá sạch.
2. Thêm state `loadError`, hiển thị banner đỏ nhỏ phía trên danh sách khi có
   lỗi — để không còn "lỗi câm" chỉ nằm trong console.
3. Bỏ điều kiện `if (showIdle) return;` — giữ auto-refresh 10s chạy trong
   mọi trường hợp, để tự phục hồi nếu 1 lần load bị lỗi tạm thời.

## Nếu áp patch xong vẫn không thấy thread đã dừng

Nghĩa là request `status: "idle"` thật sự đang lỗi ở tầng network/backend
(không phải lỗi code React nữa). Lúc đó banner đỏ mới thêm sẽ hiện ra nội
dung lỗi cụ thể — chụp lại nội dung đó (hoặc mở DevTools → tab Network, tìm
request `POST /threads/search` có body `{"status":"idle",...}`, xem response)
gửi lại để debug tiếp bước sau.
