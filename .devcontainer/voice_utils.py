import streamlit as st
import requests
import base64
import os
import tempfile
from gtts import gTTS

# ============================================
# SPEECH TO TEXT (STT) - Web Speech API
# ============================================
def get_speech_html():
    """
    Trả về HTML/JS để nhúng vào Streamlit,
    cho phép nhấn nút và nói -> nhận diện thành văn bản (tiếng Việt).
    """
    return """
    <div id="speech_container">
        <button id="start_btn" style="padding: 15px 30px; font-size: 20px; background: #4CAF50; color: white; border: none; border-radius: 10px; cursor: pointer;">
            🎤 Nhấn và nói
        </button>
        <p id="status" style="margin-top: 10px; color: #888;">Nhấn nút để bắt đầu</p>
        <p id="result" style="margin-top: 10px; font-weight: bold; color: #ff5722;"></p>
    </div>
    <script>
        const startBtn = document.getElementById('start_btn');
        const statusEl = document.getElementById('status');
        const resultEl = document.getElementById('result');
        let recognition;
        
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'vi-VN';
            recognition.continuous = false;
            recognition.interimResults = false;

            startBtn.onclick = function() {
                statusEl.textContent = '🎧 Đang nghe... Hãy nói lệnh!';
                startBtn.disabled = true;
                startBtn.style.background = '#f44336';
                resultEl.textContent = '';
                recognition.start();
            };

            recognition.onresult = function(event) {
                const last = event.results.length - 1;
                const text = event.results[last][0].transcript;
                resultEl.textContent = '✅ Bạn nói: ' + text;
                statusEl.textContent = '⏳ Đang gửi lệnh...';
                
                // Gửi lên Streamlit backend bằng query param
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('voice_cmd', text);
                window.location.href = currentUrl.toString();
            };

            recognition.onerror = function(event) {
                statusEl.textContent = '❌ Lỗi: ' + event.error + '. Thử lại nhé!';
                startBtn.disabled = false;
                startBtn.style.background = '#4CAF50';
            };
            
            recognition.onend = function() {
                startBtn.disabled = false;
                startBtn.style.background = '#4CAF50';
            };
        } else {
            statusEl.textContent = '❌ Trình duyệt không hỗ trợ voice. Dùng Chrome/Edge nhé!';
        }
    </script>
    """


def handle_voice_command(robot_ip):
    """
    Đọc lệnh thoại từ st.query_params, parse và gọi API điều khiển robot.
    Hàm này nên được gọi ở đầu app.py (sau khi đăng nhập) để bắt kịp lệnh.
    """
    cmd = st.query_params.get("voice_cmd")
    if not cmd:
        return
    
    cmd = str(cmd).strip().lower()
    success_msg = ""
    error_msg = ""
    
    try:
        # ---- Điều khiển LED ----
        if "led" in cmd and "vui" in cmd:
            requests.get(f"http://{robot_ip}/control?action=led_vui", timeout=2)
            success_msg = "😊 Đã bật LED Vui theo giọng nói!"
        elif "led" in cmd and "buồn" in cmd:
            requests.get(f"http://{robot_ip}/control?action=led_buon", timeout=2)
            success_msg = "😢 Đã bật LED Buồn theo giọng nói!"
        elif "led" in cmd and ("tắt" in cmd or "off" in cmd):
            requests.get(f"http://{robot_ip}/control?action=led_off", timeout=2)
            success_msg = "⏹ Đã tắt LED theo giọng nói!"
        
        # ---- Điều khiển Rung ----
        elif "rung" in cmd and ("bật" in cmd or "mở" in cmd or "on" in cmd):
            requests.get(f"http://{robot_ip}/control?action=rung_on", timeout=2)
            success_msg = "📳 Đã bật rung theo giọng nói!"
        elif "rung" in cmd and ("tắt" in cmd or "đóng" in cmd or "off" in cmd):
            requests.get(f"http://{robot_ip}/control?action=rung_off", timeout=2)
            success_msg = "📳 Đã tắt rung theo giọng nói!"
        
        # ---- Điều khiển Relay ----
        elif "relay" in cmd and ("bật" in cmd or "mở" in cmd or "on" in cmd):
            requests.get(f"http://{robot_ip}/control?action=relay_on", timeout=2)
            success_msg = "🔴 Đã bật Relay theo giọng nói!"
        elif "relay" in cmd and ("tắt" in cmd or "đóng" in cmd or "off" in cmd):
            requests.get(f"http://{robot_ip}/control?action=relay_off", timeout=2)
            success_msg = "⚫ Đã tắt Relay theo giọng nói!"
        
        # ---- Lệnh chụp ảnh (cần thao tác thủ công) ----
        elif "chụp" in cmd or "ảnh" in cmd:
            success_msg = "📸 Đã nhận lệnh chụp ảnh. Hãy bấm nút 'Chụp ảnh' thủ công nhé!"
        
        # ---- Không hiểu ----
        else:
            error_msg = f"🤔 Không hiểu lệnh: '{cmd}'. Thử: 'Bật LED Vui', 'Tắt rung', 'Bật Relay'..."
    
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Không kết nối được robot. Kiểm tra IP và Wifi!"
    except Exception as e:
        error_msg = f"❌ Lỗi xử lý lệnh: {e}"
    
    # Hiển thị thông báo và xóa query param để tránh chạy lặp
    if success_msg:
        st.success(success_msg)
    if error_msg:
        st.error(error_msg)
    
    st.query_params.clear()
    st.rerun()


# ============================================
# TEXT TO SPEECH (TTS) - gTTS
# ============================================
def render_tts(text, lang='vi'):
    """
    Nhận văn bản, chuyển thành giọng nói (MP3) và phát trực tiếp trên trình duyệt.
    Tự động xóa file tạm sau khi đọc.
    """
    if not text or len(text.strip()) < 2:
        return
    
    try:
        # Tạo file MP3 tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
            tts = gTTS(text=text[:350], lang=lang)
            tts.save(tmpfile.name)
            tmpfile_path = tmpfile.name
        
        # Đọc file và mã hóa base64
        with open(tmpfile_path, 'rb') as f:
            audio_bytes = f.read()
        os.unlink(tmpfile_path)
        
        audio_b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'''
            <audio autoplay controls style="width: 100%; margin-top: 10px;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Trình duyệt của bạn không hỗ trợ audio.
            </audio>
        '''
        st.markdown(audio_html, unsafe_allow_html=True)
    
    except Exception as e:
        st.warning(f"⚠️ Không thể phát giọng nói: {e}")
