# Phần 1 – Phát hiện lỗi

## Chỗ code bị lỗi

Lỗi nằm ở hàm `get_current_user`, đoạn decode token:

```python
payload = jwt.get_unverified_claims(token)
```

Sau đó code chỉ lấy `sub`, tìm user trong `USERS` rồi `return user`. Không hề check chữ ký, không check hết hạn, cũng không đụng tới `is_active`.

Cụ thể:
- Dùng `get_unverified_claims` thay vì `jwt.decode` → bỏ qua verify.
- Không xét `payload.get("sub")` có rỗng hay không (chỉ check user có trong dict).
- User `bob` bị khóa (`is_active: False`) vẫn trả về bình thường vì không có if nào chặn.

## Vì sao `get_unverified_claims()` nguy hiểm

Hàm này chỉ “mở” JWT ra đọc claim, kiểu như parse JSON đã base64. Nó **không**:
- đối chiếu chữ ký với `SECRET_KEY`
- từ chối token khi `exp` đã qua

Nên client muốn sửa gì trong payload (đổi `sub` từ alice sang bob) cũng được, miễn token còn đúng format. Server vẫn tin. Token hết hạn 1 ngày cũng vẫn pass. Đây là chỗ không được dùng cho auth thật.

Cách đúng là `jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])` — lúc đó sai chữ ký hoặc hết hạn sẽ ném lỗi.

## Test case

### 1. Token hợp lệ (alice, còn hạn)

- Gọi `GET /issue-token/alice`, lấy token.
- Gọi `GET /users/me` header `Authorization: Bearer <token>`.
- Mong đợi: 200, trả về thông tin alice.
- Thực tế code cũ: cũng 200. (case này “đúng” vì may mắn token còn hạn + user active, nhưng vẫn không an toàn vì chưa verify signature.)

### 2. Token hết hạn

- `GET /issue-token/alice?expired=true`
- Dùng token đó gọi `/users/me`.
- Mong đợi: 401 Unauthorized.
- Thực tế: 200 OK — vì `get_unverified_claims` không đọc `exp`.

### 3. Tài khoản bị khóa (bob)

- `GET /issue-token/bob` rồi `/users/me`.
- Mong đợi: 403 Forbidden (bob `is_active = False`).
- Thực tế: 200 OK, vẫn trả full info bob.

### (Thêm) Token bị sửa payload

- Lấy token alice, sửa claim `sub` (không ký lại), gọi `/users/me`.
- Mong đợi: 401.
- Thực tế code cũ: có thể 200 nếu `sub` trỏ user có trong hệ thống — giả mạo identity được.

## Kết luận ngắn

Ba lỗ hổng gắn với nhau: không verify JWT, không enforce hết hạn, không chặn user inactive. Sửa ở `get_current_user` bằng `jwt.decode` + check `sub` + check tồn tại + check `is_active` (401 / 403 tương ứng) là đủ theo đề.
