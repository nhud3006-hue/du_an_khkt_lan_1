import streamlit as st
from groq import Groq
import datetime
import os
import glob
import pandas as pd
import plotly.express as px
from datetime import datetime as dt, timedelta

# ========== CẤU HÌNH TRANG ==========
st.set_page_config(
    page_title="InnoMine Pro - Robot đồng hành",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS TÙY CHỈNH ==========
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #4A90E2;
        font-size: 3rem;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .journal-card {
        background-color: #f9f9ff;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
    }
    .edit-mode {
        background-color: #fff8e7;
        border-left: 5px solid #FFA500;
    }
</style>
""", unsafe_allow_html=True)

# ========== KHỞI TẠO GROQ (XỬ LÝ LỖI) ==========
if "GROQ_API_KEY" in st.secrets:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # Kiểm tra nhanh model (chỉ in ra log nếu cần)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"⚠️ Lỗi khởi tạo Groq: {e}")
        st.stop()
else:
    st.error("⚠️ Thiếu API Key. Vui lòng thêm GROQ_API_KEY vào Secrets (Settings → Secrets).")
    st.stop()

# ========== QUẢN LÝ USER & MẬT KHẨU ==========
USER_FILE = "users.txt"

def init_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            f.write("minh:123\nlan:456\nhuy:789\n")

def authenticate(username, password):
    init_users()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            u, p = line.split(":", 1)
            if u == username and p == password:
                return True
    return False

def register_user(username, password):
    init_users()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        existing = [line.split(":", 1)[0] for line in f.read().splitlines() if line]
    if username in existing:
        return False
    with open(USER_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username}:{password}\n")
    return True

# ========== QUẢN LÝ NHẬT KÝ ==========
def get_journal_file(username):
    return f"{username}_nhatky.txt"

def load_journal(username):
    fname = get_journal_file(username)
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f.readlines() if line.strip()]
    return []

def save_all_journal(username, lines):
    fname = get_journal_file(username)
    with open(fname, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

def append_journal(username, entry_line):
    fname = get_journal_file(username)
    with open(fname, "a", encoding="utf-8") as f:
        f.write(entry_line + "\n")

def get_all_users():
    init_users()
    users = []
    with open(USER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                users.append(line.split(":", 1)[0])
    return sorted(users)

# ========== XỬ LÝ ĐĂNG NHẬP ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-header'>🤖 InnoMine Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Robot đồng hành – Phát hiện điểm mạnh & Hỗ trợ tâm lý</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=180)
        option = st.radio("Bạn muốn:", ["🔐 Đăng nhập", "🆕 Tạo tài khoản mới"])
        
        if option == "🔐 Đăng nhập":
            all_users = get_all_users()
            if not all_users:
                st.info("Chưa có tài khoản nào. Hãy chọn 'Tạo tài khoản mới'.")
            else:
                selected_user = st.selectbox("Tên đăng nhập", all_users)
                password = st.text_input("Mật khẩu", type="password")
                if st.button("🚪 Đăng nhập", use_container_width=True):
                    if authenticate(selected_user, password):
                        st.session_state.logged_in = True
                        st.session_state.username = selected_user
                        st.rerun()
                    else:
                        st.error("❌ Sai mật khẩu.")
        else:
            new_user = st.text_input("Tên tài khoản mới (chữ thường, không dấu)")
            new_pass = st.text_input("Mật khẩu", type="password")
            confirm_pass = st.text_input("Xác nhận mật khẩu", type="password")
            if st.button("📝 Đăng ký & Đăng nhập", use_container_width=True):
                if not new_user or not new_pass:
                    st.error("Vui lòng nhập đầy đủ.")
                elif new_pass != confirm_pass:
                    st.error("Mật khẩu không khớp.")
                elif not new_user.isalnum() or " " in new_user:
                    st.error("Tên chỉ gồm chữ và số, không khoảng trắng.")
                elif register_user(new_user, new_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = new_user
                    st.rerun()
                else:
                    st.error("Tên đã tồn tại.")
    st.stop()

# ========== ĐÃ ĐĂNG NHẬP ==========
user = st.session_state.username
default_avatars = ["🤖", "😊", "🌟", "🐱", "🐶", "🦊", "🐼", "🐨", "🐸", "🐙"]
avatar = default_avatars[abs(hash(user)) % len(default_avatars)]

col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.markdown(f"<h1 style='font-size:70px;'>{avatar}</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h1 style='margin-bottom:0;'>Xin chào, {user}!</h1>", unsafe_allow_html=True)
    st.caption("InnoMine – Người bạn đồng hành lắng nghe và thấu hiểu")
with col3:
    if st.button("🚪 Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# Sidebar
st.sidebar.markdown(f"## 👤 {avatar} {user}")
st.sidebar.markdown("---")
all_users = get_all_users()
friends = [u for u in all_users if u != user]
if friends:
    friend_choice = st.sidebar.selectbox("👥 Xem nhật ký của bạn bè", ["Chính tôi"] + friends)
    viewing_user = user if friend_choice == "Chính tôi" else friend_choice
else:
    viewing_user = user
    st.sidebar.info("Chưa có bạn bè nào. Hãy khuyến khích bạn tạo tài khoản!")

st.sidebar.markdown("---")
if st.sidebar.button("📥 Xuất nhật ký của tôi (TXT)"):
    my_journal = load_journal(user)
    if my_journal:
        export_content = "\n".join(my_journal)
        st.sidebar.download_button(
            label="📁 Tải file xuống",
            data=export_content,
            file_name=f"{user}_nhatky.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("Bạn chưa có nhật ký nào.")

st.sidebar.info("📌 **Lưu ý:** Dữ liệu được lưu tạm thời trên máy chủ. Hãy xuất nhật ký thường xuyên để tránh mất khi hệ thống khởi động lại.")

# ========== PHẦN CHÍNH: GHI NHẬT KÝ ==========
st.markdown("---")
left, right = st.columns([2, 1])

with left:
    st.subheader(f"📝 Nhật ký hôm nay – {viewing_user}")
    with st.form("entry_form"):
        work = st.text_area("✨ Hôm nay bạn đã làm những gì?", placeholder="Ví dụ: học toán, đá bóng, nấu cơm...", height=120)
        mood = st.select_slider("🎭 Cảm xúc của bạn", options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"])
        submitted = st.form_submit_button("💾 Lưu & Phân tích", use_container_width=True)

    if submitted and work:
        if viewing_user == user:
            timestamp = dt.now().strftime("%Y-%m-%d %H:%M")
            entry = f"{timestamp} | {work} | {mood}"
            append_journal(user, entry)
            st.success("✅ Đã lưu nhật ký!")

            with st.spinner("🤖 InnoMine đang phân tích (có thể mất vài giây)..."):
                prompt = f"""
Bạn là InnoMine, robot đồng hành thân thiện. Người dùng vừa viết nhật ký:
- Công việc: {work}
- Cảm xúc: {mood}
Hãy phân tích điểm mạnh tiềm ẩn và đưa ra lời khuyên ngắn gọn, ấm áp, khích lệ (tối đa 150 từ).
"""
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant",
                        temperature=0.7,
                        timeout=20
                    )
                    st.info(f"💡 **InnoMine nói:** {response.choices[0].message.content}")
                except Exception as e:
                    st.error(f"❌ Lỗi kết nối AI: {e}. Vui lòng thử lại sau.")
        else:
            st.warning("⚠️ Bạn chỉ có thể ghi nhật ký cho chính mình.")

# ========== BIỂU ĐỒ CẢM XÚC 7 NGÀY ==========
with right:
    st.subheader("📊 Thống kê cảm xúc 7 ngày")
    journal_self = load_journal(user)
    if journal_self:
        data = []
        for line in journal_self:
            parts = line.split(" | ")
            if len(parts) >= 3:
                date_str = parts[0][:10]
                mood_full = parts[2]
                mood_text = mood_full.split(maxsplit=1)[-1] if " " in mood_full else mood_full
                try:
                    d = dt.strptime(date_str, "%Y-%m-%d")
                    data.append({"date": d, "mood": mood_text})
                except:
                    pass
        if data:
            df = pd.DataFrame(data)
            last_week = dt.now() - timedelta(days=7)
            df = df[df["date"] >= last_week]
            if not df.empty:
                freq = df.groupby(["date", "mood"]).size().reset_index(name="count")
                fig = px.bar(freq, x="date", y="count", color="mood", title="Cảm xúc gần đây")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu 7 ngày qua.")
        else:
            st.info("Không thể phân tích cảm xúc.")
    else:
        st.info("Viết nhật ký để xem thống kê cảm xúc.")

# ========== TIMELINE VỚI SỬA/XÓA ==========
st.markdown("---")
st.subheader(f"📜 Dòng thời gian – {viewing_user}")

journal = load_journal(viewing_user)

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if journal:
    for idx, line in enumerate(reversed(journal)):
        parts = line.split(" | ")
        if len(parts) >= 3:
            date_part, work_part, mood_part = parts[0], parts[1], parts[2]
            if st.session_state.edit_index == idx:
                st.markdown(f"<div class='journal-card edit-mode'>", unsafe_allow_html=True)
                new_work = st.text_area("Sửa nội dung", value=work_part, key=f"edit_work_{idx}")
                new_mood = st.select_slider("Cảm xúc", options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"], 
                                            index=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"].index(mood_part),
                                            key=f"edit_mood_{idx}")
                col1, col2 = st.columns(2)
                if col1.button("💾 Lưu", key=f"save_{idx}"):
                    new_line = f"{date_part} | {new_work} | {new_mood}"
                    journal[-(idx+1)] = new_line
                    save_all_journal(viewing_user, journal)
                    st.session_state.edit_index = None
                    st.rerun()
                if col2.button("❌ Hủy", key=f"cancel_{idx}"):
                    st.session_state.edit_index = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                col_text, col_edit, col_del = st.columns([10, 1, 1])
                with col_text:
                    st.markdown(f"""
                    <div class='journal-card'>
                        🕒 **{date_part}**<br>
                        📌 {work_part}<br>
                        🎭 {mood_part}
                    </div>
                    """, unsafe_allow_html=True)
                if viewing_user == user:
                    with col_edit:
                        if st.button("✏️", key=f"edit_{idx}"):
                            st.session_state.edit_index = idx
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{idx}"):
                            del journal[-(idx+1)]
                            save_all_journal(viewing_user, journal)
                            st.rerun()
        else:
            st.write(line)
else:
    st.info("✨ Chưa có nhật ký nào. Hãy viết những điều bạn trải nghiệm!")

# ========== FOOTER ==========
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Sắp ra mắt")
st.sidebar.markdown("""
- 🔐 Bảo mật nâng cao
- 👥 Kết bạn, gửi tin nhắn
- ☁️ Lưu trữ đám mây vĩnh viễn
- 🤖 Robot hình cầu với mắt LED
""")
st.sidebar.markdown("---")
st.sidebar.caption("InnoMine Pro - Phiên bản thi đấu chính thức | © 2026")
