# K9 Video Server
Dán link YouTube trên điện thoại → máy Windows tải MP4 → bấm tải về điện thoại.

**Trạng thái:** mã nguồn đã kiểm thử cục bộ; chưa cài hay nghiệm thu máy chủ Windows/đường truyền điện thoại của người dùng. GitHub lưu mã nguồn, không chạy máy chủ này. Bản này dùng trang web riêng, **chưa có MCP để ra lệnh ngay trong ChatGPT**.

## Cài một lần trên Windows
Máy đã có Python, Deno và FFmpeg theo lần tải video trước. Không cần gõ PowerShell mỗi lần dùng.

1. Trên GitHub bấm **Code → Download ZIP**. Giải nén vào thư mục cố định, ví dụ `C:\K9VideoServer`. Đừng chạy từ trong ZIP.
2. Nhấp đúp **CAI_DAT.cmd**. Chờ báo `Cai xong`. Nếu Windows yêu cầu xác nhận, chỉ chạy sau khi kiểm tra đúng gói mã của kho này.
3. Nhấp đúp **CHAY_MAY_CHU.cmd**. Giữ cửa sổ máy chủ mở. Trình duyệt mở `http://127.0.0.1:8765`; nếu trang mở trước khi máy chủ sẵn sàng thì bấm tải lại.
4. Mở `data/access-key.txt` bằng Notepad; sao chép mã vào ô **Mã truy cập** trên trang. Mã được tạo ngẫu nhiên tại máy, không nằm trên GitHub. Không gửi mã trong ảnh hoặc chat.
5. Thử một link video được phép tải. Chỉ khi hiện **Đã kiểm tra** và nút tải thì MP4 mới đạt kiểm tra giải mã.

## Dùng điện thoại cả khi khác Wi-Fi
1. Cài [Tailscale](https://tailscale.com/download) trên máy Windows và điện thoại; đăng nhập cùng tài khoản cá nhân. Tự hoàn tất đăng nhập trên thiết bị, không cung cấp mật khẩu cho trợ lý. Kiểm tra gói dịch vụ phù hợp trên trang nhà cung cấp; bộ cài này không đăng ký gói trả phí.
2. Máy Windows đang chạy máy chủ: nhấp đúp **KET_NOI_DIEN_THOAI.cmd**. Nếu có đường dẫn bật HTTPS, mở và hoàn tất theo hướng dẫn Tailscale rồi chạy lại tệp.
3. Ghi lại URL HTTPS `.ts.net` do lệnh hiện ra. Trên điện thoại bật Tailscale, mở URL đó bằng Safari/Chrome.
4. Nhập mã trong `data/access-key.txt`, dán link YouTube, chọn Nhanh hoặc Nét, xác nhận quyền tải rồi bấm **Tải MP4**.
5. Chờ **Đã kiểm tra** → bấm **Tải MP4 về thiết bị**. Trên iPhone xem trong Files/Tệp → Downloads, rồi dùng Chia sẻ → Lưu video nếu muốn lưu vào Ảnh. Có thể thêm trang vào màn hình chính.

Máy Windows phải **bật, đã đăng nhập, có Internet và không ngủ**. Không cần cùng Wi-Fi. Không bật Tailscale Funnel; không mở cổng router. Máy chủ chỉ nghe `127.0.0.1`; Tailscale Serve cung cấp HTTPS trong mạng riêng. URL này không truy cập được từ ChatGPT cloud nếu chưa có tích hợp riêng.

## Tự chạy sau khi đăng nhập Windows (tuỳ chọn)
Nhấp đúp **BAT_KHOI_DONG.cmd** một lần. Tạo duy nhất shortcut `K9 Video Server.lnk` trong thư mục Startup. Đây là chạy sau đăng nhập, không phải dịch vụ chạy trước đăng nhập. Đừng mở thêm cửa sổ máy chủ khi đã chạy.
Để tắt tự chạy: bấm Win+R → nhập `shell:startup` → xoá shortcut đó. Để dừng máy chủ hiện tại: đóng cửa sổ chạy máy chủ. Để tắt chia sẻ Tailscale Serve: dùng `tailscale serve reset` nếu máy không dùng Serve cho ứng dụng khác; kiểm tra cấu hình trước vì reset xoá các cấu hình Serve khác.

## Chế độ tải và kiểm tra
- **Nhanh:** ưu tiên MP4 H.264 có sẵn tiếng, cạnh ngắn tối đa 720; có thể là 360p.
- **Nét:** chọn luồng H.264 tốt nhất trong giới hạn cạnh ngắn 1080, ghép M4A không mã hoá lại nếu cần. Không tự nâng độ phân giải.
- Kiểm tra tệp tồn tại, có hình, có tiếng khi nguồn có tiếng; kích thước khớp luồng chọn; thời lượng sai số <= max(1 giây, 1%); FFmpeg giải mã toàn bộ không lỗi.
- Chỉ nhận một video YouTube, bỏ thông tin playlist. Chỉ tải nội dung sở hữu hoặc được phép. Không cookies, mật khẩu, DRM bypass hay dịch vụ tải trung gian.
- Tối đa một tác vụ chạy; lỗi/timeout hữu hạn; 4 phân đoạn đồng thời, giảm tải nếu nhận 429. Không cam kết tốc độ.
- Video/receipt lưu trong `data/videos`. Không tự xoá; cần dọn định kỳ khi máy chủ không đang tải. Cần ít nhất 1 GiB trống để bắt đầu; giới hạn 2 GiB mỗi luồng. Video dài có thể vượt timeout.
- 20 tác vụ gần nhất giữ trong RAM; khởi động lại mất danh sách nhưng không mất video. Dán lại cùng URL/chế độ để kiểm tra và tái dùng cache hợp lệ.
- Tệp và URL video không gửi lên GitHub. Không commit thư mục `data`, `.venv`, mã truy cập, cookie hoặc log chứa URL ký số. Kho hiện Public chỉ chứa mã nguồn/tài liệu.

## Kiểm thử
Chạy `python -m unittest -v test_server.py` sau khi cài dependencies, có FFmpeg/ffprobe. Kiểm thử URL, quyền truy cập, phiên đăng nhập, nguồn request, giới hạn đăng nhập, tác vụ bận, video tổng hợp có hình/tiếng, giao đúng byte MP4 và từ chối kết quả lỗi. Phần download network trong kiểm thử máy chủ được mô phỏng, không chứng minh YouTube luôn tải được.
Đã có một video thật do người dùng tải trên Windows bằng yt-dlp + Deno: `WhNIFLcvDUA`, được kiểm tra độc lập là H.264/AAC, 360×640, 123.53 giây, 3,174,141 byte. Đây là bằng chứng cho lần tải CLI trước, **không phải nghiệm thu máy chủ mới**.

## Nếu lỗi
- Trang không mở: kiểm tra cửa sổ CHAY_MAY_CHU, Tailscale và trạng thái ngủ của máy. Chỉ chạy một máy chủ trên cổng 8765.
- Lỗi mã: xem đúng tệp access-key tại máy; không dùng GitHub token. Sau 5 lần sai chờ 60 giây.
- Thiếu công cụ: bảo đảm `ffmpeg`, `ffprobe`, `deno` có trong PATH; đóng mở lại máy chủ sau khi cài.
- YouTube không cung cấp luồng phù hợp hoặc chặn truy cập: dừng, báo lỗi; không vô hiệu hoá TLS hay vượt bảo vệ. Có thể cập nhật yt-dlp bằng cách chạy lại CAI_DAT sau khi cập nhật requirements khi cần.
- Không dùng máy này như máy chủ công khai đa người dùng. Chưa có quản lý nhiều tài khoản, dịch vụ Windows hoặc MCP cloud.

## Nguồn và ghi nhận
- Skill gốc phần tải/kiểm tra: **Dung Nguyễn**. Phần mở rộng máy chủ và giao diện: **K9 – Nguyễn Văn Định**.
- [yt-dlp chính thức](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Flask](https://flask.palletsprojects.com/) và [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/)
