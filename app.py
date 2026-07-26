# =================================================================
#                INNOMINE-X PRO - WEB APP HOÀN CHỈNH
# =================================================================
# Tích hợp: Đăng nhập, Nhật ký, AI, Robot điều khiển, Thống kê, 
# Chat AI, Bảng xếp hạng, Cảnh báo sức khỏe tinh thần
# =================================================================

import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import json
import os
import requests
from datetime import datetime
from PIL import Image
import io
import plotly.express as px
import plotly.graph_objects as go

# ---- Cấu hình trang ----
st.set_page_config(
    page_title="InnoMine-X Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS TỐI ĐEN - SANG TRỌNG ----
st.markdown("""
<style>
    /* Reset và font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    .stApp {
        background: #0a0e1a;
        background-image: radial-gradient(ellipse at 20% 50%, rgba(72,0,255,0.06) 0%, transparent 50%),
                          radial-gradient(ellipse at 80% 50%, rgba(0,200,255,0.04) 0%, transparent 50%);
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #00d4ff 0%, #7b2ffc 50%, #ff6fd8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        padding: 1rem 0 0.5rem;
        text-shadow: 0 0 60px rgba(0,212,255,0.2);
        animation: glow 3s ease-in-out infinite;
    }
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 30px rgba(0,212,255,0.2); }
        50% { text-shadow: 0 0 60px rgba(123,47,252,0.4); }
    }
    .sub-title {
        text-align: center;
        color: #8892b0;
        font-size: 1.1rem;
        letter-spacing: 0.15em;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        padding-bottom: 1.5rem;
    }
    .card {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 40px rgba(0,0,0,0.6);
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        margin-bottom: 1.5rem;
    }
    .card:hover {
        border-color: rgba(0,212,255,0.15);
        box-shadow: 0 12px 56px rgba(0,0,0,0.8);
        transform: translateY(-2px);
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e6f1ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .journal-entry {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 3px solid #00d4ff;
        transition: 0.2s;
    }
    .journal-entry:hover {
        background: rgba(255,255,255,0.07);
    }
    .btn-primary {
        background: linear-gradient(135deg, #00d4ff 0%, #7b2ffc 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0,212,255,0.3) !important;
        width: 100%;
    }
    .btn-primary:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 8px 40px rgba(0,212,255,0.5) !important;
    }
    .btn-secondary {
        background: rgba(255,255,255,0.05) !important;
        color: #e6f1ff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s !important;
        width: 100%;
    }
    .btn-secondary:hover {
        background: rgba(255,255,255,0.1) !important;
    }
    .status-online {
        color: #00ff88;
        font-weight: 600;
    }
    .status-offline {
        color: #ff4444;
        font-weight: 600;
    }
    .warning-green {
        background: rgba(16, 185, 129, 0.12);
        border-left: 4px solid #10b981;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        color: #a7f3d0;
    }
    .warning-yellow {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid #f59e0b;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        color: #fcd34d;
    }
    .warning-orange {
        background: rgba(234, 88, 12, 0.12);
        border-left: 4px solid #ea580c;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        color: #fb923c;
    }
    .warning-red {
        background: rgba(220, 38, 38, 0.12);
        border-left: 4px solid #dc2626;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        color: #fca5a5;
    }
    .stButton button {
        width: 100%;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: #e6f1ff !important;
        padding: 0.6rem 1rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 3px rgba(0,212,255,0.15) !important;
    }
    .css-1d391kg, .css-12oz5g7 {
        background: rgba(10,14,26,0.9) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    .footer {
        margin-top: 3rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid rgba(255,255,255,0.04);
        text-align: center;
        color: #495670;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
    }
    .footer span {
        color: #64ffda;
    }
    .stMetric {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 0.5rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    [data-testid="stMetricValue"] {
        color: #64ffda !important;
        font-weight: 700 !important;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #00d4ff, #7b2ffc) !important;
    }
    .stImage {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        background: transparent;
        border-bottom: 2px solid rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #8892b0;
        padding: 0.5rem 0;
        font-size: 1rem;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #64ffda;
        border-bottom: 2px solid #64ffda;
    }
</style>
""", unsafe_allow_html=True)

# ---- HÀM BẢO MẬT & DỮ LIỆU ----
USER_FILE = "users.json"
JOURNAL_FILE = "journals.json"
RANKING_FILE = "rankings.json"

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Tạo file mặc định nếu chưa có
if not os.path.exists(USER_FILE):
    save_json(USER_FILE, {"minh": hash_password("123"), "lan": hash_password("456"), "huy": hash_password("789")})
if not os.path.exists(JOURNAL_FILE):
    save_json(JOURNAL_FILE, {})
if not os.path.exists(RANKING_FILE):
    save_json(RANKING_FILE, {})

def authenticate(username, password):
    users = load_json(USER_FILE)
    return username in users and users[username] == hash_password(password)

def register_user(username, password):
    users = load_json(USER_FILE)
    if username in users:
        return False
    users[username] = hash_password(password)
    save_json(USER_FILE, users)
    return True

# ---- HÀM NHẬT KÝ & PGI ----
MOOD_SCORE = {
    "😢 Buồn": 2,
    "😐 Bình thường": 5,
    "😊 Vui vẻ": 8,
    "🤔 Suy tư": 6,
    "😎 Tự tin": 9,
    "✨ Hy vọng": 9
}
STRESS_KEYWORDS = ["stress", "áp lực", "mệt mỏi", "căng thẳng", "lo lắng", "mất ngủ", "cô đơn", "buồn"]

def get_journal(username):
    journals = load_json(JOURNAL_FILE)
    return journals.get(username, [])

def add_journal(username, entry):
    journals = load_json(JOURNAL_FILE)
    if username not in journals:
        journals[username] = []
    journals[username].append(entry)
    save_json(JOURNAL_FILE, journals)

def compute_pgi(username):
    entries = get_journal(username)
    if not entries:
        return 50, {"Số bài viết": 0, "Điểm trung bình": 0}
    mood_scores = []
    stress_count = 0
    for e in entries[-15:]:
        mood = e.get("mood", "😐 Bình thường")
        mood_scores.append(MOOD_SCORE.get(mood, 5))
        content = e.get("content", "").lower()
        stress_count += sum(1 for kw in STRESS_KEYWORDS if kw in content)
    avg_mood = np.mean(mood_scores) if mood_scores else 5
    stress_factor = min(stress_count * 3, 20)
    pgi = min(max(avg_mood * 10 - stress_factor, 0), 100)
    return int(pgi), {"Số bài viết": len(entries), "Điểm trung bình": round(avg_mood, 2)}

def early_warning_level(username):
    pgi, _ = compute_pgi(username)
    entries = get_journal(username)
    if not entries:
        return "🟢 Bình thường", "Chưa có dữ liệu", "green"
    last_5 = entries[-5:]
    recent_stress = sum(1 for e in last_5 if any(kw in e.get("content", "").lower() for kw in STRESS_KEYWORDS))
    if pgi < 30 or recent_stress >= 3:
        return "🔴 Cảnh báo đỏ", "Cần hỗ trợ ngay! Hãy trò chuyện với AI hoặc tìm sự giúp đỡ.", "red"
    elif pgi < 50 or recent_stress >= 2:
        return "🟠 Cảnh báo cam", "Có dấu hiệu căng thẳng. Hãy nghỉ ngơi và viết nhật ký.", "orange"
    elif pgi < 70:
        return "🟡 Cảnh báo vàng", "Hãy chú ý hơn đến tinh thần của bạn.", "yellow"
    else:
        return "🟢 Trạng thái xanh", "Tinh thần ổn định! Tiếp tục duy trì.", "green"

def get_ranking():
    return load_json(RANKING_FILE, {})

def update_ranking(username, score):
    rank = get_ranking()
    if username not in rank or score > rank[username]:
        rank[username] = score
        save_json(RANKING_FILE, rank)

# ---- SESSION STATE ----
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'robot_ip' not in st.session_state:
    st.session_state.robot_ip = "192.168.8.126"
if 'robot_connected' not in st.session_state:
    st.session_state.robot_connected = False
if 'image_data' not in st.session_state:
    st.session_state.image_data = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": "Xin chào! Tôi là InnoMine AI. Hôm nay bạn cảm thấy thế nào? 💙"}]

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:1.5rem;">
        <span style="font-size:2.5rem;">🤖</span>
        <span style="font-family: 'Inter', sans-serif; font-size:1.3rem; font-weight:700; color:#64ffda;">InnoMine-X</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.success(f"👋 {st.session_state.username}")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🤖 Kết nối Robot")
        ip = st.text_input("IP:", st.session_state.robot_ip)
        if st.button("🔗 Kết nối", use_container_width=True):
            try:
                response = requests.get(f"http://{ip}/capture", timeout=3)
                if response.status_code == 200:
                    st.session_state.robot_ip = ip
                    st.session_state.robot_connected = True
                    st.success("✅ Robot online!")
                    st.balloons()
                else:
                    st.error("❌ Lỗi kết nối")
            except:
                st.error("❌ Không kết nối được")
        
        if st.session_state.robot_connected:
            st.markdown(f"""
            <div style="background:rgba(0,255,136,0.08); padding:0.5rem 1rem; border-radius:8px; border-left:3px solid #00ff88;">
                <span class="status-online">● Online</span>
                <br><small>IP: {st.session_state.robot_ip}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(255,68,68,0.08); padding:0.5rem 1rem; border-radius:8px; border-left:3px solid #ff4444;">
                <span class="status-offline">● Offline</span>
            </div>
            """, unsafe_allow_html=True)

# ---- ĐĂNG NHẬP ----
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🤖 InnoMine-X</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Hệ thống AI & Robot đồng hành hỗ trợ sức khỏe tinh thần học sinh</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            option = st.radio("", ["🔐 Đăng nhập", "🆕 Đăng ký"], horizontal=True)
            if option == "🔐 Đăng nhập":
                u = st.text_input("Tên đăng nhập", key="login_user")
                p = st.text_input("Mật khẩu", type="password", key="login_pass")
                if st.button("Đăng nhập", use_container_width=True, key="login_btn"):
                    if authenticate(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.success("✅ Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Sai tên hoặc mật khẩu. Dùng: minh/123, lan/456, huy/789")
            else:
                u = st.text_input("Tên mới (chữ thường, không dấu)", key="reg_user")
                p = st.text_input("Mật khẩu", type="password", key="reg_pass")
                c = st.text_input("Xác nhận mật khẩu", type="password", key="reg_confirm")
                if st.button("Đăng ký", use_container_width=True, key="reg_btn"):
                    if u and p and p == c and u.isalnum():
                        if register_user(u, p):
                            st.success("✅ Đăng ký thành công! Đăng nhập ngay.")
                        else:
                            st.error("❌ Tên đã tồn tại.")
                    else:
                        st.error("❌ Vui lòng kiểm tra lại thông tin.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---- DASHBOARD ----
user = st.session_state.username
st.markdown(f'<div class="main-title">Chào {user} 👋</div>', unsafe_allow_html=True)

pgi, pgi_components = compute_pgi(user)
warning_text, warning_desc, warning_color = early_warning_level(user)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🧠 Chỉ số PGI", f"{pgi}/100", delta=f"{pgi - 50:+d}")
with col2:
    st.metric("📝 Số bài viết", pgi_components["Số bài viết"])
with col3:
    st.metric("⭐ Điểm TB cảm xúc", pgi_components["Điểm trung bình"])

# Cảnh báo
if warning_color == "red":
    st.markdown(f"<div class='warning-red'>🚨 {warning_text}: {warning_desc}</div>", unsafe_allow_html=True)
elif warning_color == "orange":
    st.markdown(f"<div class='warning-orange'>⚠️ {warning_text}: {warning_desc}</div>", unsafe_allow_html=True)
elif warning_color == "yellow":
    st.markdown(f"<div class='warning-yellow'>⚠️ {warning_text}: {warning_desc}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='warning-green'>✅ {warning_text}: {warning_desc}</div>", unsafe_allow_html=True)

# ---- TABS ----
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Nhật ký", "🤖 Điều khiển Robot", "📊 Thống kê", "💬 Chat AI", "🏆 Bảng xếp hạng"])

# ---- TAB 1: NHẬT KÝ ----
with tab1:
    st.markdown("### ✍️ Viết nhật ký")
    col1, col2 = st.columns([1, 1])
    with col1:
        mood = st.selectbox("Cảm xúc hôm nay:", list(MOOD_SCORE.keys()))
    with col2:
        date = st.date_input("Ngày:", datetime.now())
    content = st.text_area("Nội dung:", placeholder="Hôm nay bạn thế nào? Hãy chia sẻ nhé!", height=150)
    uploaded_file = st.file_uploader("📸 Ảnh (tùy chọn)", type=["jpg", "jpeg", "png"])
    
    if st.button("💾 Lưu nhật ký", use_container_width=True, key="save_journal"):
        if content.strip():
            entry = {
                "date": datetime.now().isoformat(),
                "mood": mood,
                "content": content,
                "image": None
            }
            if uploaded_file:
                entry["image"] = uploaded_file.getvalue()
            add_journal(user, entry)
            update_ranking(user, len(get_journal(user)))
            st.success("✅ Đã lưu nhật ký!")
            st.rerun()
        else:
            st.warning("⚠️ Vui lòng nhập nội dung.")
    
    st.markdown("---")
    st.markdown("### 📖 Lịch sử nhật ký")
    journal = get_journal(user)
    if journal:
        for entry in reversed(journal[-10:]):
            d = datetime.fromisoformat(entry["date"]).strftime("%H:%M %d/%m/%Y")
            st.markdown(f"""
            <div class='journal-entry'>
                <strong>{d}</strong> {entry['mood']}
                <br>{entry['content']}
            </div>
            """, unsafe_allow_html=True)
            if entry.get("image"):
                st.image(entry["image"], width=200)
    else:
        st.info("📭 Chưa có nhật ký nào. Hãy viết ngay!")

# ---- TAB 2: ĐIỀU KHIỂN ROBOT ----
with tab2:
    st.markdown("### 🤖 Điều khiển Robot")
    
    if not st.session_state.robot_connected:
        st.warning("⚠️ Chưa kết nối robot. Vào Sidebar để kết nối.")
    else:
        def send_cmd(action):
            try:
                url = f"http://{st.session_state.robot_ip}/control?action={action}"
                requests.get(url, timeout=2)
                st.success(f"✅ {action} thành công")
            except:
                st.error("❌ Lỗi gửi lệnh")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="card"><div class="card-title">💡 LED</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("😊 Vui", use_container_width=True, key="led_vui"):
                    send_cmd("led_vui")
            with c2:
                if st.button("😢 Buồn", use_container_width=True, key="led_buon"):
                    send_cmd("led_buon")
            with c3:
                if st.button("⏹ Tắt", use_container_width=True, key="led_off"):
                    send_cmd("led_off")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card"><div class="card-title">⚡ Relay</div>', unsafe_allow_html=True)
            c4, c5 = st.columns(2)
            with c4:
                if st.button("🔴 Bật", use_container_width=True, key="relay_on"):
                    send_cmd("relay_on")
            with c5:
                if st.button("⚫ Tắt", use_container_width=True, key="relay_off"):
                    send_cmd("relay_off")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card"><div class="card-title">📳 Rung</div>', unsafe_allow_html=True)
            c6, c7 = st.columns(2)
            with c6:
                if st.button("📳 Bật", use_container_width=True, key="rung_on"):
                    send_cmd("rung_on")
            with c7:
                if st.button("📳 Tắt", use_container_width=True, key="rung_off"):
                    send_cmd("rung_off")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card"><div class="card-title">📷 Camera</div>', unsafe_allow_html=True)
            if st.button("📸 Chụp ảnh", use_container_width=True, key="capture"):
                try:
                    response = requests.get(f"http://{st.session_state.robot_ip}/capture", timeout=5)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        st.session_state.image_data = img
                        st.success("✅ Ảnh đã chụp!")
                    else:
                        st.error("❌ Lỗi chụp ảnh")
                except:
                    st.error("❌ Lỗi kết nối")
            if st.session_state.image_data:
                st.image(st.session_state.image_data, caption="📷 Ảnh từ robot", use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ---- TAB 3: THỐNG KÊ ----
with tab3:
    st.markdown("### 📊 Thống kê cảm xúc")
    journal = get_journal(user)
    if journal:
        df = pd.DataFrame(journal)
        df["date"] = pd.to_datetime(df["date"])
        df["mood_score"] = df["mood"].map(MOOD_SCORE)
        df = df.sort_values("date")
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(df, x="date", y="mood_score", title="Biểu đồ cảm xúc theo thời gian",
                          labels={"mood_score": "Điểm cảm xúc", "date": "Ngày"})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font_color='#8892b0', xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                              yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            mood_counts = df["mood"].value_counts().reset_index()
            mood_counts.columns = ["Cảm xúc", "Số lần"]
            fig = px.bar(mood_counts, x="Cảm xúc", y="Số lần", title="Phân bố cảm xúc",
                         color="Cảm xúc", color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font_color='#8892b0', showlegend=False,
                              xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                              yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📋 Chi tiết nhật ký")
        st.dataframe(df[["date", "mood", "content"]].tail(10))
        
        # Cập nhật điểm bảng xếp hạng dựa trên số bài viết
        update_ranking(user, len(journal))
    else:
        st.info("📭 Chưa có dữ liệu để thống kê.")

# ---- TAB 4: CHAT AI ----
with tab4:
    st.markdown("### 💬 Trò chuyện với AI")
    
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    prompt = st.chat_input("Nhập tin nhắn...")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI phản hồi
        lower = prompt.lower()
        if any(kw in lower for kw in ["buồn", "stress", "áp lực", "mệt"]):
            response = "Tôi hiểu bạn đang cảm thấy không ổn. Hãy hít thở sâu, viết ra những gì bạn nghĩ, và nhớ rằng bạn không cô đơn. Tôi luôn ở đây lắng nghe. 💙"
        elif any(kw in lower for kw in ["vui", "tốt", "hạnh phúc", "tuyệt"]):
            response = "Thật tuyệt vời! Hãy tận hưởng khoảnh khắc này và chia sẻ với mọi người nhé! 😊🌟"
        elif any(kw in lower for kw in ["robot", "điều khiển", "led", "rung", "relay"]):
            response = "Bạn muốn điều khiển robot? Hãy vào tab 'Điều khiển Robot' nhé! 🤖"
        elif any(kw in lower for kw in ["nhật ký", "cảm xúc", "mood"]):
            response = "Hãy viết nhật ký ở tab 'Nhật ký' để theo dõi cảm xúc và sức khỏe tinh thần của bạn nhé! 📝"
        elif any(kw in lower for kw in ["cảm ơn", "thanks"]):
            response = "Không có gì! Tôi luôn sẵn sàng đồng hành cùng bạn. 💖"
        else:
            response = "Cảm ơn bạn đã chia sẻ! Hãy duy trì việc viết nhật ký để theo dõi sức khỏe tinh thần nhé. 🌟"
        
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

# ---- TAB 5: BẢNG XẾP HẠNG ----
with tab5:
    st.markdown("### 🏆 Bảng xếp hạng Thợ săn tinh thần")
    rank = get_ranking()
    if rank:
        sorted_rank = sorted(rank.items(), key=lambda x: x[1], reverse=True)
        rank_df = pd.DataFrame(sorted_rank, columns=["Người dùng", "Điểm"])
        rank_df.index = rank_df.index + 1
        rank_df.index.name = "Hạng"
        if st.session_state.logged_in:
            rank_df["Bạn?"] = rank_df["Người dùng"].apply(lambda x: "⭐" if x == st.session_state.username else "")
        st.dataframe(rank_df, use_container_width=True)
        
        # Biểu đồ
        fig = px.bar(rank_df.head(10), x="Người dùng", y="Điểm", title="Top 10",
                     color="Người dùng", color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font_color='#8892b0', showlegend=False,
                          xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                          yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Chưa có người chơi nào. Hãy viết nhật ký để tích điểm!")

# ---- FOOTER ----
st.markdown("""
<div class="footer">
    🤖 InnoMine-X Pro · v3.0 · Hệ thống AI & Robot đồng hành<br>
    <span>© 2026 · Phát triển với ❤️ và Streamlit</span>
</div>
""", unsafe_allow_html=True)

# ==================== FOOTER ====================
st.sidebar.markdown("---")
st.sidebar.caption("InnoMine-X | Hệ thống AI & Robot đồng hành | Bản demo chính thức")
