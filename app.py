import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import json
import os
import time
import requests
from datetime import datetime, timedelta
from PIL import Image
import io
import base64
import plotly.express as px
import plotly.graph_objects as go

# ==================== CẤU HÌNH TRANG ====================
st.set_page_config(
    page_title="InnoMine-X",
    page_icon="🤖",
    layout="wide"
)

# ==================== CSS ====================
st.markdown("""
<style>
    .stApp { background: #0a0e1a; }
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #00d4ff, #7b2ffc, #ff6fd8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .sub-title {
        text-align: center;
        color: #8892b0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 1rem;
    }
    .card-title {
        color: #e6f1ff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .journal-entry {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.6rem;
        border-left: 3px solid #00d4ff;
    }
    .stButton button {
        background: linear-gradient(135deg, #00d4ff, #7b2ffc) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        transition: all 0.3s !important;
    }
    .stButton button:hover {
        transform: scale(1.03);
        box-shadow: 0 0 30px rgba(0,212,255,0.3);
    }
    .status-online { color: #00ff88; font-weight: 600; }
    .status-offline { color: #ff4444; font-weight: 600; }
    .warning-green { background: rgba(16,185,129,0.15); border-left: 4px solid #10b981; padding:0.8rem; border-radius:8px; color:#a7f3d0; }
    .warning-yellow { background: rgba(245,158,11,0.15); border-left: 4px solid #f59e0b; padding:0.8rem; border-radius:8px; color:#fcd34d; }
    .warning-orange { background: rgba(234,88,12,0.15); border-left: 4px solid #ea580c; padding:0.8rem; border-radius:8px; color:#fb923c; }
    .warning-red { background: rgba(220,38,38,0.15); border-left: 4px solid #dc2626; padding:0.8rem; border-radius:8px; color:#fca5a5; }
    .timeline-item { padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ==================== BẢO MẬT ====================
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

USER_FILE = "users.json"
if not os.path.exists(USER_FILE):
    default_users = {"minh": hash_password("123"), "lan": hash_password("456")}
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(default_users, f, indent=2)

def load_users():
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def authenticate(username, password):
    users = load_users()
    return username in users and users[username] == hash_password(password)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True

# ==================== LƯU DỮ LIỆU HOẠT ĐỘNG ====================
ACTIVITY_FILE = "activities.json"
if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)

def load_activities():
    with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_activities(activities):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)

def add_activity(username, entry):
    activities = load_activities()
    if username not in activities:
        activities[username] = []
    activities[username].append(entry)
    save_activities(activities)

# ==================== TẠO LỘ TRÌNH ====================
def generate_learning_path(activities):
    if not activities:
        return ["Bắt đầu theo dõi hoạt động để có lộ trình phù hợp."]
    
    # Phân tích hoạt động gần đây (24h)
    recent = [a for a in activities if (datetime.now() - datetime.fromisoformat(a["time"])).total_seconds() < 86400]
    
    if not recent:
        return ["Chưa có dữ liệu hôm nay."]
    
    study_time = sum(1 for a in recent if a.get("activity") == "học")
    rest_time = sum(1 for a in recent if a.get("activity") == "nghỉ ngơi")
    exercise_time = sum(1 for a in recent if a.get("activity") == "thể thao")
    social_time = sum(1 for a in recent if a.get("activity") == "kết nối")
    
    suggestions = []
    
    # Đề xuất dựa trên dữ liệu
    if study_time > 180:  # Học > 3 giờ
        suggestions.append("📚 Bạn đã học nhiều, hãy nghỉ ngơi 15 phút và vận động nhẹ.")
    elif study_time < 60:
        suggestions.append("📖 Hôm nay học còn ít, hãy dành ít nhất 1 giờ để ôn bài.")
    
    if rest_time < 30:
        suggestions.append("😴 Bạn cần nghỉ ngơi nhiều hơn. Hãy ngồi thiền hoặc nghe nhạc thư giãn.")
    
    if exercise_time < 20:
        suggestions.append("🏃 Hãy vận động ít nhất 15 phút để tăng cường sức khỏe và tập trung.")
    
    if social_time < 10:
        suggestions.append("💬 Kết nối với bạn bè hoặc gia đình để cải thiện tinh thần.")
    
    # Cá nhân hóa lộ trình
    if study_time > 120 and rest_time > 20:
        suggestions.append("🌟 Bạn đang có một ngày học tập hiệu quả! Hãy duy trì nhịp độ này.")
    
    # Đề xuất khung giờ học tối ưu
    times = [datetime.fromisoformat(a["time"]) for a in recent if a.get("activity") == "học"]
    if times:
        morning = sum(1 for t in times if 6 <= t.hour < 12)
        afternoon = sum(1 for t in times if 12 <= t.hour < 18)
        evening = sum(1 for t in times if 18 <= t.hour < 23)
        
        if morning >= afternoon and morning >= evening:
            suggestions.append("⏰ Bạn học tốt nhất vào buổi sáng. Hãy sắp xếp các môn khó vào khung giờ này.")
        elif afternoon >= morning and afternoon >= evening:
            suggestions.append("⏰ Bạn học tốt nhất vào buổi chiều. Đây là thời điểm lý tưởng để học các môn cần tư duy.")
        elif evening >= morning and evening >= afternoon:
            suggestions.append("⏰ Bạn học tốt nhất vào buổi tối. Hãy tận dụng thời gian yên tĩnh để học.")
    
    if not suggestions:
        suggestions.append("📝 Tiếp tục duy trì các hoạt động tích cực. Bạn đang làm tốt!")
    
    return suggestions[:5]

# ==================== SESSION STATE ====================
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
if 'activities' not in st.session_state:
    st.session_state.activities = []
if 'selected_activity' not in st.session_state:
    st.session_state.selected_activity = "học"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:1rem;">
        <span style="font-size:2.5rem;">🤖</span>
        <span style="font-size:1.3rem; font-weight:700; color:#64ffda;">InnoMine-X</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.success(f"👋 {st.session_state.username}")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        st.markdown("---")
        
        # Kết nối Robot
        st.markdown("### 📡 Robot")
        ip = st.text_input("IP Robot:", st.session_state.robot_ip)
        if st.button("🔗 Kết nối", use_container_width=True):
            try:
                response = requests.get(f"http://{ip}/capture", timeout=3)
                if response.status_code == 200:
                    st.session_state.robot_ip = ip
                    st.session_state.robot_connected = True
                    st.success("✅ Kết nối thành công!")
                    st.balloons()
                else:
                    st.error("❌ Lỗi kết nối")
            except:
                st.error("❌ Không kết nối được")
        
        if st.session_state.robot_connected:
            st.markdown(f"""
            <div style="background:rgba(0,255,136,0.1); padding:0.5rem 1rem; border-radius:8px; border-left:3px solid #00ff88;">
                <span class="status-online">● Online</span>
                <br><small>IP: {st.session_state.robot_ip}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(255,68,68,0.1); padding:0.5rem 1rem; border-radius:8px; border-left:3px solid #ff4444;">
                <span class="status-offline">● Offline</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Cài đặt hoạt động
        st.markdown("### 🎯 Hoạt động hiện tại")
        activity_options = ["học", "nghỉ ngơi", "thể thao", "kết nối", "khác"]
        st.session_state.selected_activity = st.selectbox("Chọn hoạt động:", activity_options)
        if st.button("📤 Cập nhật hoạt động", use_container_width=True):
            if st.session_state.robot_connected:
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=set_activity&value={st.session_state.selected_activity}", timeout=2)
                    st.success(f"✅ Đã cập nhật: {st.session_state.selected_activity}")
                    add_activity(st.session_state.username, {
                        "time": datetime.now().isoformat(),
                        "activity": st.session_state.selected_activity,
                        "emotion": "neutral"
                    })
                except:
                    st.error("❌ Lỗi gửi lệnh")
            else:
                st.warning("⚠️ Chưa kết nối robot")

# ==================== ĐĂNG NHẬP ====================
if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🤖 InnoMine-X</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Hệ thống AI & Robot đồng hành hỗ trợ học tập và sức khỏe tinh thần</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div style="background:rgba(255,255,255,0.04); padding:2rem; border-radius:20px; border:1px solid rgba(255,255,255,0.06);">', unsafe_allow_html=True)
            option = st.radio("", ["🔐 Đăng nhập", "🆕 Đăng ký"], horizontal=True)
            if option == "🔐 Đăng nhập":
                u = st.text_input("Tên đăng nhập", key="login_user")
                p = st.text_input("Mật khẩu", type="password", key="login_pass")
                if st.button("Đăng nhập", use_container_width=True):
                    if authenticate(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.success("✅ Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Sai tên hoặc mật khẩu.")
            else:
                u = st.text_input("Tên mới", key="reg_user")
                p = st.text_input("Mật khẩu", type="password", key="reg_pass")
                c = st.text_input("Xác nhận mật khẩu", type="password", key="reg_confirm")
                if st.button("Đăng ký", use_container_width=True):
                    if u and p and p == c and u.isalnum():
                        if register_user(u, p):
                            st.success("✅ Đăng ký thành công! Đăng nhập ngay.")
                        else:
                            st.error("❌ Tên đã tồn tại.")
                    else:
                        st.error("❌ Vui lòng kiểm tra lại.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==================== DASHBOARD ====================
user = st.session_state.username
st.markdown(f'<div class="main-title">Chào {user} 👋</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Theo dõi và tối ưu hóa hoạt động học tập của bạn</div>', unsafe_allow_html=True)

# ==================== TABS ====================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🤖 Điều khiển", "📈 Lộ trình", "📝 Nhật ký"])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    # Thống kê nhanh
    activities = load_activities().get(user, [])
    today_activities = [a for a in activities if (datetime.now() - datetime.fromisoformat(a["time"])).total_seconds() < 86400]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Hôm nay", f"{len(today_activities)} hoạt động")
    with col2:
        study_count = sum(1 for a in today_activities if a.get("activity") == "học")
        st.metric("📖 Học", f"{study_count} lần")
    with col3:
        rest_count = sum(1 for a in today_activities if a.get("activity") == "nghỉ ngơi")
        st.metric("😴 Nghỉ ngơi", f"{rest_count} lần")
    with col4:
        st.metric("📊 Tổng", f"{len(activities)} hoạt động")
    
    st.markdown("---")
    
    # Biểu đồ hoạt động
    if activities:
        df = pd.DataFrame(activities)
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time")
        
        st.markdown("### 📊 Biểu đồ hoạt động")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(df, x="time", y="activity", title="Hoạt động theo thời gian", 
                          color_discrete_sequence=["#00d4ff"])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font_color='#a8b2d1', height=350)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            activity_counts = df["activity"].value_counts().reset_index()
            activity_counts.columns = ["Hoạt động", "Số lần"]
            fig = px.pie(activity_counts, values="Số lần", names="Hoạt động", 
                         title="Phân bố hoạt động",
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font_color='#a8b2d1', height=350)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Chưa có dữ liệu hoạt động. Hãy cập nhật hoạt động từ robot hoặc sidebar.")

# ==================== TAB 2: ĐIỀU KHIỂN ROBOT ====================
with tab2:
    st.markdown("### 🤖 Điều khiển Robot")
    
    if not st.session_state.robot_connected:
        st.warning("⚠️ Chưa kết nối robot. Vào Sidebar để kết nối.")
    else:
        def send_cmd(action):
            try:
                url = f"http://{st.session_state.robot_ip}/control?action={action}"
                requests.get(url, timeout=2)
                st.success(f"✅ {action}")
            except:
                st.error("❌ Lỗi gửi lệnh")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="card"><div class="card-title">💡 LED</div>', unsafe_allow_html=True)
            if st.button("😊 Vui", use_container_width=True):
                send_cmd("led_vui")
                add_activity(user, {"time": datetime.now().isoformat(), "activity": "led_vui", "emotion": "happy"})
            if st.button("😢 Buồn", use_container_width=True):
                send_cmd("led_buon")
                add_activity(user, {"time": datetime.now().isoformat(), "activity": "led_buon", "emotion": "sad"})
            if st.button("⏹ Tắt", use_container_width=True):
                send_cmd("led_off")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card"><div class="card-title">⚡ Relay</div>', unsafe_allow_html=True)
            if st.button("🔴 Bật", use_container_width=True):
                send_cmd("relay_on")
                add_activity(user, {"time": datetime.now().isoformat(), "activity": "relay_on", "emotion": "neutral"})
            if st.button("⚫ Tắt", use_container_width=True):
                send_cmd("relay_off")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="card"><div class="card-title">📳 Rung</div>', unsafe_allow_html=True)
            if st.button("📳 Bật", use_container_width=True):
                send_cmd("rung_on")
            if st.button("📳 Tắt", use_container_width=True):
                send_cmd("rung_off")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="card"><div class="card-title">📷 Camera</div>', unsafe_allow_html=True)
            if st.button("📸 Chụp ảnh", use_container_width=True):
                try:
                    response = requests.get(f"http://{st.session_state.robot_ip}/capture", timeout=5)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        st.session_state.image_data = img
                        st.success("✅ Ảnh đã chụp!")
                        add_activity(user, {"time": datetime.now().isoformat(), "activity": "chụp ảnh", "emotion": "neutral"})
                    else:
                        st.error("❌ Lỗi chụp ảnh")
                except:
                    st.error("❌ Lỗi kết nối")
            
            if st.session_state.image_data:
                st.image(st.session_state.image_data, caption="📷 Ảnh từ robot", use_column_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==================== TAB 3: LỘ TRÌNH ====================
with tab3:
    st.markdown("### 🗺️ Lộ trình học tập thông minh")
    
    activities = load_activities().get(user, [])
    suggestions = generate_learning_path(activities)
    
    # Hiển thị lộ trình
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📝 Đề xuất cho bạn")
    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"{i}. {suggestion}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lịch trình gợi ý
    st.markdown("### 🕐 Lịch trình mẫu")
    
    schedule = """
    | Thời gian | Hoạt động | Ghi chú |
    |-----------|-----------|---------|
    | 6:30 - 7:00 | Thức dậy, tập thể dục nhẹ | Tăng cường tuần hoàn máu |
    | 7:00 - 7:30 | Ăn sáng | Bổ sung năng lượng |
    | 7:30 - 9:30 | Học tập (môn khó) | Sáng tập trung tốt nhất |
    | 9:30 - 9:45 | Nghỉ giải lao | Thư giãn mắt, vận động |
    | 9:45 - 11:30 | Học tập (môn dễ) | Tiếp tục duy trì |
    | 11:30 - 13:30 | Nghỉ trưa, ăn trưa | Nghỉ ngơi phục hồi |
    | 13:30 - 15:30 | Học tập (nhóm/ôn tập) | Tương tác xã hội |
    | 15:30 - 16:30 | Thể thao, vận động | Giải phóng endorphin |
    | 16:30 - 18:00 | Tự do (sở thích) | Thư giãn tinh thần |
    | 18:00 - 19:00 | Ăn tối | Kết nối gia đình |
    | 19:00 - 21:00 | Học tập (ôn bài) | Ôn lại kiến thức |
    | 21:00 - 22:00 | Thư giãn, đọc sách | Chuẩn bị ngủ |
    | 22:00 | Đi ngủ | Ngủ đủ 7-8 tiếng |
    """
    st.markdown(schedule)
    
    # Thống kê tuần
    st.markdown("### 📈 Thống kê tuần")
    if len(activities) >= 7:
        df = pd.DataFrame(activities)
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date
        weekly = df.groupby(["date", "activity"]).size().reset_index(name="count")
        fig = px.bar(weekly, x="date", y="count", color="activity", title="Hoạt động theo ngày")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font_color='#a8b2d1', height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Cần ít nhất 7 ngày dữ liệu để thống kê tuần.")

# ==================== TAB 4: NHẬT KÝ ====================
with tab4:
    st.markdown("### ✍️ Nhật ký hoạt động")
    
    activities = load_activities().get(user, [])
    if activities:
        for entry in reversed(activities[-20:]):
            d = datetime.fromisoformat(entry["time"]).strftime("%H:%M %d/%m")
            emoji = "😊" if entry.get("emotion") == "happy" else "😢" if entry.get("emotion") == "sad" else "😐"
            st.markdown(f"""
            <div class='journal-entry'>
                <strong>{d}</strong> {emoji} {entry.get('activity', 'khác')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 Chưa có nhật ký hoạt động.")

# ==================== FOOTER ====================
st.markdown("""
<div style="text-align:center; color:#495670; font-size:0.8rem; padding:2rem 0 1rem; border-top:1px solid rgba(255,255,255,0.05);">
    🤖 InnoMine-X · v3.0 · Hệ thống AI & Robot đồng hành
</div>
""", unsafe_allow_html=True)
