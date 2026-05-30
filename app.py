import streamlit as st
from groq import Groq
import datetime
import os

# ========== CẤU HÌNH TRANG ==========
st.set_page_config(
    page_title="InnoMine Pro - Robot đồng hành",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== TÙY CHỈNH GIAO DIỆN ==========
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
    .sidebar-text {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== KHỞI TẠO GROQ ==========
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("⚠️ Thiếu API Key. Vui lòng thêm GROQ_API_KEY vào Secrets (Settings → Secrets).")
    st.stop()

# ========== DỮ LIỆU NGƯỜI DÙNG ==========
USERS = {
    "minh": {"avatar": "🐻", "name": "Minh", "bg_color": "#FFE4E1"},
    "lan": {"avatar": "🐰", "name": "Lan", "bg_color": "#E0FFFF"},
    "huy": {"avatar": "🐧", "name": "Huy", "bg_color": "#FFF0F5"}
}

def get_journal_file(username):
    return f"{username}_nhatky.txt"

def load_journal(username):
    fname = get_journal_file(username)
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_journal(username, entry_line):
    with open(get_journal_file(username), "a", encoding="utf-8") as f:
        f.write(entry_line + "\n")

# ========== QUẢN LÝ ĐĂNG NHẬP ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-header'>🤖 InnoMine Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Robot đồng hành – Phát hiện điểm mạnh & Hỗ trợ tâm lý</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=180)
        selected = st.selectbox("🔑 Chọn tài khoản của bạn", list(USERS.keys()), format_func=lambda x: USERS[x]["name"])
        if st.button("🚪 Đăng nhập", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.username = selected
            st.rerun()
    st.stop()

# ========== GIAO DIỆN CHÍNH SAU ĐĂNG NHẬP ==========
user = st.session_state.username
info = USERS[user]

# Header
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.markdown(f"<h1 style='font-size:70px;'>{info['avatar']}</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h1 style='margin-bottom:0;'>Xin chào, {info['name']}!</h1>", unsafe_allow_html=True)
    st.caption("InnoMine – Người bạn đồng hành lắng nghe và thấu hiểu")
with col3:
    if st.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.rerun()

# Sidebar: chọn bạn bè để xem nhật ký
st.sidebar.markdown(f"## 👤 {info['avatar']} {info['name']}")
st.sidebar.markdown("---")
friends = [f for f in USERS.keys() if f != user]
friend_names = ["Chính tôi"] + [USERS[f]["name"] for f in friends]
friend_map = dict(zip(friend_names, ["self"] + friends))
choice = st.sidebar.selectbox("👥 Xem nhật ký của", friend_names)
viewing_user = user if choice == "Chính tôi" else friend_map[choice]

# ========== PHẦN GHI NHẬT KÝ ==========
st.markdown("---")
left, right = st.columns([2, 1])

with left:
    st.subheader(f"📝 Nhật ký hôm nay – {USERS[viewing_user]['name'] if viewing_user != user else info['name']}")
    with st.form("entry_form"):
        work = st.text_area("✨ Bạn đã làm những gì hôm nay?", placeholder="Ví dụ: học toán, đá bóng, nấu cơm, giúp đỡ bạn...", height=120)
        mood = st.select_slider("🎭 Cảm xúc của bạn", options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"])
        submitted = st.form_submit_button("💾 Lưu & Phân tích", use_container_width=True)

    if submitted and work:
        if viewing_user == user:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"{timestamp} | {work} | {mood}"
            save_journal(user, entry)
            st.success("✅ Đã lưu nhật ký!")

            with st.spinner("🤖 InnoMine đang phân tích..."):
                prompt = f"""
Bạn là InnoMine, robot đồng hành thân thiện. Người dùng vừa viết nhật ký:
- Công việc: {work}
- Cảm xúc: {mood}
Hãy phân tích điểm mạnh tiềm ẩn (dựa trên hành động và cảm xúc) và đưa ra lời khuyên ngắn gọn, ấm áp, khích lệ (tối đa 150 từ).
"""
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.7
                )
                st.info(f"💡 **InnoMine nói:** {response.choices[0].message.content}")
        else:
            st.warning("⚠️ Bạn chỉ có thể ghi nhật ký cho chính mình. Hãy chọn 'Chính tôi' để viết.")

# ========== TIMELINE ==========
st.markdown("---")
st.subheader(f"📜 Dòng thời gian – {USERS[viewing_user]['name'] if viewing_user != user else info['name']}")
journal = load_journal(viewing_user)
if journal:
    for line in reversed(journal[-10:]):  # chỉ hiện 10 dòng mới nhất
        parts = line.split(" | ")
        if len(parts) >= 3:
            date_part = parts[0]
            work_part = parts[1]
            mood_part = parts[2]
            st.markdown(f"""
            <div class='journal-card'>
                🕒 **{date_part}**<br>
                📌 {work_part}<br>
                🎭 {mood_part}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write(line)
else:
    st.info("✨ Chưa có nhật ký nào. Hãy viết những điều bạn trải nghiệm!")

# ========== FOOTER & THÔNG TIN PHÁT TRIỂN ==========
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Sắp ra mắt")
st.sidebar.markdown("""
- 🔐 Đăng nhập bảo mật thực tế
- 👥 Kết bạn, gửi tin nhắn, thả cảm xúc
- 🗃️ Lưu nhật ký trên đám mây (Firebase)
- 🤖 Robot hình cầu với mắt LED nhấp nháy
""")
st.sidebar.markdown("---")
st.sidebar.caption("InnoMine Pro - Phiên bản thi đấu | © 2026")

# ========== CHẠY ỨNG DỤNG ==========
# (không cần thêm gì, chạy bằng `streamlit run app.py`)
