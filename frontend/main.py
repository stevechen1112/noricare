import streamlit as st
import httpx
import json
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards

# ============ Configuration ============
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="My Health Coach",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ Custom CSS Loading ============
def load_css():
    import os
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS文件未找到: {css_path}")

try:
    load_css()
except Exception as e:
    st.error(f"加载CSS失败: {e}")

# ============ Session State Init ============
if "step" not in st.session_state:
    st.session_state.step = 1
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "health_data" not in st.session_state:
    st.session_state.health_data = {}
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None
if "ocr_process_id" not in st.session_state:
    st.session_state.ocr_process_id = None
# New state for abnormal items
if "abnormal_items" not in st.session_state:
    st.session_state.abnormal_items = []
# New state for history
if "history_data" not in st.session_state:
    st.session_state.history_data = None
# New state for chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "meal_draft_items" not in st.session_state:
    st.session_state.meal_draft_items = []
if "meal_summary" not in st.session_state:
    st.session_state.meal_summary = None
if "meal_recent" not in st.session_state:
    st.session_state.meal_recent = []
if "meal_align_results" not in st.session_state:
    st.session_state.meal_align_results = []
if "meal_align_query" not in st.session_state:
    st.session_state.meal_align_query = ""
if "meal_vision_results" not in st.session_state:
    st.session_state.meal_vision_results = []
if "meal_vision_profile" not in st.session_state:
    st.session_state.meal_vision_profile = "bento"
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

# ============ Functions ============

async def ask_health_coach(msg, history, report_context):
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": st.session_state.user_profile.get("id", 0),
            "message": msg,
            "context": report_context,
            "history": history
        }
        resp = await client.post(f"{API_BASE_URL}/chat/message", json=payload, timeout=20.0)
        return resp.json()


    def _auth_headers():
        token = st.session_state.get("auth_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}


    async def auth_register(email: str, password: str, name: str | None = None):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE_URL}/auth/register",
                json={"email": email, "password": password, "name": name},
                timeout=10.0,
            )
            return resp


    async def auth_login(email: str, password: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=10.0,
            )
            return resp

# ============ Sidebar Navigation ============
with st.sidebar:
    st.markdown("## 🧭 導覽")
    st.markdown("依照步驟完成個人健康分析流程")

    step_labels = ["1. 個人資料", "2. 上傳報告", "3. 健康儀表板", "4. 營養查詢", "5. 飲食紀錄"]
    current_step = st.session_state.step
    progress_value = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}.get(current_step, 0.2)
    st.progress(progress_value, text=f"目前步驟：{step_labels[current_step - 1] if current_step <= 5 else '飲食紀錄'}")

    st.markdown("### 步驟切換")
    if st.button("➡️ 前往：個人資料", width="stretch"):
        st.session_state.step = 1
        st.rerun()
    if st.button("➡️ 前往：上傳報告", width="stretch"):
        st.session_state.step = 2
        st.rerun()
    if st.button("➡️ 前往：健康儀表板", width="stretch"):
        st.session_state.step = 3
        st.rerun()
    if st.button("🔍 營養資料庫查詢", width="stretch"):
        st.session_state.step = 4
        st.rerun()
    if st.button("🍱 飲食紀錄", width="stretch"):
        st.session_state.step = 5
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔐 登入")
    if st.session_state.auth_token:
        user_email = (st.session_state.auth_user or {}).get("email", "已登入")
        st.success(f"已登入：{user_email}")
        if st.button("登出", key="auth_logout"):
            st.session_state.auth_token = None
            st.session_state.auth_user = None
            st.rerun()
    else:
        auth_email = st.text_input("Email", key="auth_email")
        auth_password = st.text_input("Password", type="password", key="auth_password")
        auth_name = st.text_input("Name（註冊用）", key="auth_name")
        cols = st.columns(2)
        with cols[0]:
            if st.button("登入", key="auth_login"):
                if not auth_email or not auth_password:
                    st.warning("請輸入 Email 與密碼")
                else:
                    import asyncio
                    resp = asyncio.run(auth_login(auth_email, auth_password))
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.auth_token = data.get("access_token") or data.get("token")
                        st.session_state.auth_user = data.get("user")
                        st.rerun()
                    else:
                        st.error(f"登入失敗：{resp.text}")
        with cols[1]:
            if st.button("註冊", key="auth_register"):
                if not auth_email or not auth_password:
                    st.warning("請輸入 Email 與密碼")
                else:
                    import asyncio
                    resp = asyncio.run(auth_register(auth_email, auth_password, auth_name))
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.auth_token = data.get("access_token") or data.get("token")
                        st.session_state.auth_user = data.get("user")
                        st.rerun()
                    else:
                        st.error(f"註冊失敗：{resp.text}")
    
    # 側邊欄快速對話
    if st.session_state.analysis_report:
        st.markdown("---")
        st.markdown("### 💬 快速諮詢")
        with st.expander("與 AI 營養師對話", expanded=False):
            for m in st.session_state.chat_history[-3:]: # 只顯示最近 3 則
                role_icon = "🧑‍💻" if m["role"] == "user" else "🌿"
                st.markdown(f"**{role_icon}**: {m['content']}")
            
            side_prompt = st.text_input("問問營養師...", key="side_chat_input")
            if st.button("發送", key="side_chat_send"):
                if side_prompt:
                    st.session_state.chat_history.append({"role": "user", "content": side_prompt})
                    import asyncio
                    clean_history = [{"role": h["role"], "content": h["content"]} for h in st.session_state.chat_history[:-1]]
                    response_data = asyncio.run(ask_health_coach(side_prompt, clean_history, st.session_state.analysis_report))
                    st.session_state.chat_history.append({"role": "assistant", "content": response_data.get("reply", "...")})
                    st.rerun()

def render_chat_interface():
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; margin-top: 20px;">
        <h3 style="color: #4CAF50; margin-top:0;">💬 Ask Health Coach</h3>
        <p style="color: #666; font-size: 0.9em;">有任何關於報告的疑問，或想調整菜單，都可以直接問我喔！</p>
    </div>
    """, unsafe_allow_html=True)

    # Display Chat History
    for message in st.session_state.chat_history:
        avatar = "🧑‍💻" if message["role"] == "user" else "🌿"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ex: 這週菜單的苦瓜可以換掉嗎？", key="main_chat_input"):
        # Add User Message to History
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Call API
        with st.chat_message("assistant", avatar="🌿"):
            message_placeholder = st.empty()
            with st.spinner("思考中..."):
                import asyncio
                try:
                    # Filter history to only include role and content for API to avoid sending large objects if any
                    clean_history = [{"role": h["role"], "content": h["content"]} for h in st.session_state.chat_history[:-1]]
                    
                    response_data = asyncio.run(ask_health_coach(prompt, clean_history, st.session_state.analysis_report))
                    reply = response_data.get("reply", "抱歉，我現在有點累，請稍後再試。")
                    message_placeholder.markdown(reply)
                    
                    # Add Assistant Message to History
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun() # Refresh to clear input and show history
                except Exception as e:
                    message_placeholder.error(f"發生錯誤: {str(e)}")

async def fetch_user_history(user_id):
    """Fetch trend data for charts"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/users/{user_id}/history", timeout=5.0)
            if resp.status_code == 200:
                st.session_state.history_data = resp.json()["history"]
        except Exception:
            pass # Fail silently for history

async def create_user(profile_data):
    async with httpx.AsyncClient() as client:
        # 轉換前端資料格式為後端 Pydantic
        # Activity level map
        act_map = {
            "幾乎不動 (久坐辦公)": "sedentary",
            "輕度活動 (偶爾散步)": "light",
            "中度活動 (規律運動 1-3次)": "moderate",
            "高度活動 (規律運動 3-5次)": "active"
        }
        
        payload = {
            "name": profile_data["name"],
            "age": profile_data["age"],
            "gender": "male" if profile_data["gender"] == "男" else "female",
            "height_cm": profile_data["height"],
            "weight_kg": profile_data["weight"],
            "health_goals": profile_data["goals"],
            "lifestyle": {
                "activity_level": act_map.get(profile_data["activity"], "sedentary"),
                "dietary_preference": profile_data["diet_pref"],
                "eating_habits": profile_data["habits"],
                "allergies": [] # MVP 暫略
            }
        }
        
        try:
            resp = await client.post(f"{API_BASE_URL}/users/", json=payload, timeout=10.0)
            if resp.status_code == 200:
                st.session_state.user_profile = resp.json()
                return True
            else:
                st.error(f"建立使用者失敗: {resp.text}")
                return False
        except Exception as e:
            st.error(f"連線錯誤: {str(e)}")
            return False

async def align_food_name(query: str, limit: int = 5):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/food/align", params={"q": query, "limit": limit}, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
        raise ValueError(resp.text)

async def suggest_food_from_photo(uploaded_file, limit: int = 5, profile: str = "bento"):
    async with httpx.AsyncClient() as client:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        resp = await client.post(
            f"{API_BASE_URL}/food/vision/suggest",
            params={"limit": limit, "profile": profile},
            files=files,
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()
        raise ValueError(resp.text)

async def create_meal(payload: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE_URL}/meals",
            json=payload,
            headers=_auth_headers(),
            timeout=10.0,
        )
        return resp

async def fetch_meal_summary(days: int = 7):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE_URL}/meals/summary",
            params={"days": days},
            headers=_auth_headers(),
            timeout=5.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return None

async def fetch_recent_meals(limit: int = 10):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE_URL}/meals",
            params={"limit": limit},
            headers=_auth_headers(),
            timeout=5.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return []

async def upload_and_analyze(files_list):
    if not files_list:
        return
    
    async with httpx.AsyncClient() as client:
        # 支援多文件上傳
        all_health_data = {}
        all_abnormal_items = []
        
        # 顯示總進度
        progress_text = st.empty()
        main_progress = st.progress(0)
        
        for idx, file in enumerate(files_list):
            file_progress = int((idx / len(files_list)) * 100)
            main_progress.progress(file_progress)
            progress_text.text(f"📄 正在處理第 {idx+1}/{len(files_list)} 份報告：{file.name}")
            
            files = {"file": (file.name, file, file.type)}
            try:
                # 1. 上傳 & OCR
                upload_resp = await client.post(f"{API_BASE_URL}/ocr/upload", files=files, timeout=30.0)
                
                if upload_resp.status_code != 200:
                    st.warning(f"⚠️ {file.name} 上傳失敗，跳過此文件")
                    continue

                upload_data = upload_resp.json()
                file_id = upload_data["file_id"]
                
                # 2. 輪詢直到 OCR 完成
                import asyncio
                ocr_result = None
                max_retries = 15  # 增加重試次數到15次 (約30秒)
                
                for i in range(max_retries):
                    await asyncio.sleep(2)
                    try:
                        status_resp = await client.get(f"{API_BASE_URL}/ocr/result/{file_id}", timeout=60.0)  # 設置60秒超時
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            if status_data["status"] == "completed":
                                ocr_result = status_data["data"]
                                break
                            elif status_data["status"] == "failed":
                                st.warning(f"⚠️ {file.name} 解析失敗，跳過此文件")
                                break
                    except Exception as e:
                        if i == max_retries - 1:  # 最後一次重試失敗
                            st.error(f"❌ {file.name} 等待超時或連接錯誤: {str(e)}")
                            break
                        # 繼續重試
                        continue
                    
                if ocr_result:
                    # 驗證數據結構
                    if not isinstance(ocr_result, dict):
                        st.warning(f"⚠️ {file.name} 數據格式錯誤（非字典類型）")
                        continue
                    
                    # 檢查必要字段
                    if "structured_data" not in ocr_result:
                        st.warning(f"⚠️ {file.name} 缺少 structured_data 字段")
                        st.info(f"返回的數據鍵: {list(ocr_result.keys())}")
                        continue
                    
                    if "abnormal_items" not in ocr_result:
                        st.warning(f"⚠️ {file.name} 缺少 abnormal_items 字段")
                        ocr_result["abnormal_items"] = []  # 提供默認值
                    
                    # 合併多份報告的數據
                    structured_data = ocr_result["structured_data"]
                    
                    if not isinstance(structured_data, dict):
                        st.warning(f"⚠️ {file.name} structured_data 格式錯誤")
                        continue
                    
                    for key, value in structured_data.items():
                        if key not in all_health_data:
                            all_health_data[key] = value
                        else:
                            # 如果有重複項目，保留最新的
                            if isinstance(value, dict) and isinstance(all_health_data[key], dict):
                                all_health_data[key].update(value)
                            else:
                                all_health_data[key] = value
                    
                    # 合併異常項目
                    abnormal_items = ocr_result.get("abnormal_items", [])
                    if isinstance(abnormal_items, list):
                        all_abnormal_items.extend(abnormal_items)
                    
                    st.success(f"✅ {file.name} 處理完成")
                else:
                    st.warning(f"⚠️ {file.name} 解析超時")
                    
            except Exception as e:
                st.error(f"⚠️ {file.name} 處理錯誤: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
                continue
        
        # 完成所有文件處理
        main_progress.progress(100)
        progress_text.text(f"✅ 已處理 {len(files_list)} 份報告")
        
        if not all_health_data:
            st.error("❌ 沒有成功處理任何報告，請檢查文件格式")
            return

        st.session_state.health_data = all_health_data
        
        # 去重異常項目 (處理 dict 類型不可雜湊的問題)
        seen_abnormal = set()
        unique_abnormal = []
        for item in all_abnormal_items:
            # 如果是字典則取 name 欄位，否則轉字串
            raw_name = item.get("name") if isinstance(item, dict) else str(item)
            # 正規化名稱以去重 (移除空格、轉小寫)
            norm_name = raw_name.replace(" ", "").lower() if raw_name else ""
            
            if norm_name and norm_name not in seen_abnormal:
                seen_abnormal.add(norm_name)
                unique_abnormal.append(item)
        
        st.session_state.abnormal_items = unique_abnormal
        
        # 3. 呼叫推薦引擎 API
        try:
            with st.spinner("💡 營養師大腦運轉中，正在生成專屬建議..."):
                # 提取異常指標名稱（字串列表），以符合後端 RecommendationRequest schema
                abnormal_names = []
                for item in st.session_state.abnormal_items:
                    if isinstance(item, dict) and "name" in item:
                        abnormal_names.append(item["name"])
                    elif isinstance(item, str):
                        abnormal_names.append(item)
                
                # 組合 payload
                rec_payload = {
                    "user_profile": st.session_state.user_profile,
                    "health_data": st.session_state.health_data,
                    "abnormal_items": abnormal_names
                }
                
                # 這裡是一個比較大的 POST，包含所有資料
                rec_resp = await client.post(f"{API_BASE_URL}/recommendation/generate", json=rec_payload, timeout=60.0)
                
                if rec_resp.status_code == 200:
                    st.session_state.analysis_report = rec_resp.json()
                    
                    # 生成成功後，順便拉取最新歷史數據以便繪圖
                    await fetch_user_history(st.session_state.user_profile["id"])
                    
                    st.session_state.step = 3 # Go to report
                    st.rerun()
                else:
                    st.error(f"生成建議失敗: {rec_resp.text}")
        
        except Exception as e:
            st.error(f"發生錯誤: {str(e)}")

# ============ UI: Header ============
st.markdown("<h1 style='color: #556B2F;'>🌿 個人專屬營養師 AI Agent</h1>", unsafe_allow_html=True)

# Clickable Stepper
step = st.session_state.step
step_cols = st.columns([1, 1, 1, 1, 1])
with step_cols[0]:
    if st.button("👤 個人資料", width="stretch", type="primary" if step == 1 else "secondary"):
        st.session_state.step = 1
        st.rerun()
with step_cols[1]:
    if st.button("📄 上傳報告", width="stretch", type="primary" if step == 2 else "secondary"):
        st.session_state.step = 2
        st.rerun()
with step_cols[2]:
    if st.button("📊 健康儀表板", width="stretch", type="primary" if step == 3 else "secondary"):
        st.session_state.step = 3
        st.rerun()
with step_cols[3]:
    if st.button("🔍 營養查詢", width="stretch", type="primary" if step == 4 else "secondary"):
        st.session_state.step = 4
        st.rerun()
with step_cols[4]:
    if st.button("🍱 飲食紀錄", width="stretch", type="primary" if step == 5 else "secondary"):
        st.session_state.step = 5
        st.rerun()
progress_value = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}.get(st.session_state.step, 0.2)
step_names = ['個人資料', '上傳報告', '健康儀表板', '營養查詢', '飲食紀錄']
st.progress(progress_value, text=f"目前步驟：{step_names[st.session_state.step - 1] if st.session_state.step <= 5 else '飲食紀錄'}")
st.markdown("---")

# ============ UI: Step 1 - Welcome & Profile ============
if st.session_state.step == 1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### Hi, 歡迎回來！
        我是您的個人專屬營養師。
        
        為了提供最貼近您生活的建議，
        請告訴我一些關於您今天的狀態。
        """)
        st.image("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=2070&auto=format&fit=crop", caption="Eat well, Live well", width="stretch")

    with col2:
        with st.container(border=True):
            st.markdown("#### 📝 建立/更新您的檔案")
            name = st.text_input("如何稱呼您?", value="Steve")
            col_a, col_b = st.columns(2)
            with col_a:
                age = st.number_input("年齡", 18, 100, 40)
                height = st.number_input("身高 (cm)", 100.0, 250.0, 178.8)
            with col_b:
                gender = st.selectbox("性別", ["男", "女"])
                weight = st.number_input("體重 (kg)", 30.0, 200.0, 78.8)
            
            st.markdown("#### 🥗 生活型態")
            activity = st.select_slider(
                "平日活動量", 
                options=["幾乎不動 (久坐辦公)", "輕度活動 (偶爾散步)", "中度活動 (規律運動 1-3次)", "高度活動 (規律運動 3-5次)"]
            )
            
            diet_pref = st.selectbox("飲食偏好", ["無特殊偏好", "素食 (Vegetarian)", "生酮 (Keto)", "低醣 (Low Carb)"])
            
            habits = st.multiselect(
                "飲食習慣 (多選)",
                ["外食族", "自己煮", "不吃早餐", "愛吃甜食", "常喝手搖飲", "常應酬喝酒"],
                default=["外食族"]
            )

            goals = st.multiselect(
                "健康目標",
                ["減重", "增肌", "控制血糖", "降低膽固醇", "提升精力"],
                default=["控制血糖", "減重"]
            )
            
            if st.button("下一步：上傳報告 ➡️", width="stretch"):
                profile_data = {
                    "name": name, "age": age, "height": height, "weight": weight,
                    "gender": gender, "activity": activity, "diet_pref": diet_pref,
                    "habits": habits, "goals": goals
                }
                import asyncio
                success = asyncio.run(create_user(profile_data))
                if success:
                    st.session_state.step = 2
                    st.rerun()

# ============ UI: Step 2 - Upload ============
elif st.session_state.step == 2:
    st.markdown("### 📤 上傳您的最新健檢報告")
    st.markdown("別擔心，我看得懂複雜的醫學表格。請直接上傳照片即可。")

    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 3])
    with nav_col1:
        if st.button("⬅️ 返回修改資料"):
            st.session_state.step = 1
            st.rerun()
    with nav_col2:
        if st.button("🔄 重新填寫表單"):
            st.session_state.user_profile = {}
            st.session_state.step = 1
            st.rerun()
    
    st.markdown("### 📤 上傳健檢報告")
    st.info("💡 提示：可以一次上傳多份報告（例如：血液檢查、尿液檢查、心電圖等），系統會自動整合所有數據")
    
    uploaded_files = st.file_uploader(
        "支援 JPG, PNG 格式（可選擇多個文件）", 
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True  # 啟用多文件上傳
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if uploaded_files:
            # 顯示上傳的文件列表
            st.write(f"📋 已選擇 **{len(uploaded_files)}** 份報告：")
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"　{i}. {file.name}")
            
            # 預覽第一份報告
            if len(uploaded_files) > 0:
                st.image(uploaded_files[0], caption=f"預覽：{uploaded_files[0].name}", width="stretch")
                if len(uploaded_files) > 1:
                    st.caption(f"...還有 {len(uploaded_files)-1} 份報告未顯示")
            
            if st.button("🚀 開始 AI 深度分析", width="stretch", type="primary"):
                import asyncio
                asyncio.run(upload_and_analyze(uploaded_files))
                
    with st.expander("還沒有報告? 使用測試數據"):
        if st.button("使用 Steve 的範例數據"):
            # Mock analysis for demo purposes if backend fails or for quick show
             pass

# ============ UI: Step 3 - Dashboard ============
elif st.session_state.step == 3:
    report = st.session_state.analysis_report
    
    # --- Top Banner: Score ---
    score = report.get('health_score', 75)
    score_color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 60 else "#F44336"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background-color: #fff; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="margin:0;">本期健康綜合評分</h2>
        <h1 style="font-size: 3.5rem; color: {score_color}; margin: 10px 0;">{score}</h1>
        <p style="color: #666;">根據您的檢驗數值與生活習慣綜合評估</p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    # --- Tabs for Content ---
    tab0, tab1, tab2, tab3, tab4 = st.tabs(["📈 趨勢分析", "📊 數值解讀", "🍽️ 飲食建議", "💊 保健補充", "📅 一週菜單"])
    
    with tab0:
        if st.session_state.history_data and len(st.session_state.history_data) > 1:
            st.markdown("### 🏆 您的健康進步軌跡")
            
            # Convert history to DataFrame for plotting
            hist_df_data = []
            for h in st.session_state.history_data:
                # Flatten metrics
                row = {"Date": h["created_at"], "Score": h["health_score"]}
                row.update(h["key_metrics"])
                hist_df_data.append(row)
            
            hist_df = pd.DataFrame(hist_df_data)
            
            # Plot Health Score
            st.markdown("#### 綜合評分趨勢")
            st.line_chart(hist_df, x="Date", y="Score", color="#6B8E23")
            
            # Plot Key Metrics (HbA1c & Glucose) if available
            metrics_to_plot = [col for col in hist_df.columns if col not in ["Date", "Score"]]
            if metrics_to_plot:
                st.markdown("#### 關鍵指標變化")
                selected_metrics = st.multiselect("選擇指標", metrics_to_plot, default=metrics_to_plot[:2])
                if selected_metrics:
                    st.line_chart(hist_df, x="Date", y=selected_metrics)
        else:
            st.info("累積兩次以上的分析紀錄後，這裡將顯示您的健康趨勢圖表！")
            st.image("https://cdn-icons-png.flaticon.com/512/271/271228.png", width=100, caption="持續追蹤是進步的開始")

    with tab1:
        st.markdown("### ⚠️ 需要關注的異常指標")
        for item in st.session_state.abnormal_items:
             if isinstance(item, dict):
                 name = item.get("name", "未知項目")
                 val = item.get("value", "-")
                 unit = item.get("unit", "")
                 status = item.get("status", "")
                 st.markdown(f"<div class='chat-bubble'>🔴 <b>{name}</b>: {val} {unit} ({status})</div>", unsafe_allow_html=True)
             else:
                 st.markdown(f"<div class='chat-bubble'>🔴 {item}</div>", unsafe_allow_html=True)
        
        st.markdown("### 🧬 完整數據快照")
        # Creating a nice dataframe display
        data_rows = []
        for k, v in st.session_state.health_data.items():
            status = str(v.get('status', '正常'))
            # 支援多種正常狀態
            is_normal = status.strip().title() in ['Pass', '正常', 'Normal', 'Ok']
            status_emoji = "✅" if is_normal else "⚠️"
            
            val = v.get('value', '-')
            unit = v.get('unit', '')
            
            data_rows.append({
                "項目": k,
                "數值": f"{val} {unit}",
                "狀態": f"{status_emoji} {status}",
                "參考值": v.get('reference_range', '-')
            })
        df = pd.DataFrame(data_rows)
        st.dataframe(df, width="stretch", hide_index=True)

    with tab2:
        if report.get('food_advice'):
            advice = report['food_advice'][0] # Assuming first section
            st.markdown(f"""
            <div class="lifestyle-card">
                <div class="card-title">🥗 {advice['title']}</div>
                <div class="card-content">{advice['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        if report.get('supplement_advice'):
            advice = report['supplement_advice'][0]
            st.markdown(f"""
            <div class="lifestyle-card">
                <div class="card-title">💊 {advice['title']}</div>
                <div class="card-content">{advice['content']}</div>
            </div>
            """, unsafe_allow_html=True)
            
    with tab4:
        if report.get('meal_plan'):
            # Check if it's prompt-generated markdown or structured
            # In our current backend service, we returned the raw text in a dict
            content = report['meal_plan'].get('markdown_content', '')
            st.markdown(f"""
            <div class="lifestyle-card" style="background-color: #FFFDE7;">
                <div class="card-title">📅 營養師客製化的一週菜單</div>
                <div class="card-content">{content}</div>
            </div>
            """, unsafe_allow_html=True)

    # ============ Chat Interface ============
    render_chat_interface()

    if st.button("🔄 開始新的分析"):
        st.session_state.step = 1
        st.rerun()

    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 3])
    with nav_col1:
        if st.button("⬅️ 返回上傳", key="back_to_upload"):
            st.session

# ============ UI: Step 4 - Nutrition Search ============
elif st.session_state.step == 4:
    st.markdown("### 🔍 台灣食品營養成分資料庫 2024")
    st.markdown("查詢 2,180 種食物的完整營養資訊（衛福部官方資料）")
    
    # Search Bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔎 搜尋食物名稱", placeholder="例如：雞胸肉、糙米、香蕉", label_visibility="collapsed")
    with col2:
        search_button = st.button("🔍 搜尋", width="stretch")
    
    # Quick Search Tags
    st.markdown("**熱門搜尋：**")
    tag_cols = st.columns(8)
    quick_tags = ["雞胸肉", "糙米", "香蕉", "雞蛋", "牛奶", "番茄", "花椰菜", "鮭魚"]
    for idx, tag in enumerate(quick_tags):
        with tag_cols[idx]:
            if st.button(f"#{tag}", key=f"tag_{tag}"):
                search_query = tag
                search_button = True
    
    # Perform Search
    if search_button and search_query:
        import asyncio
        
        async def search_nutrition(query):
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(f"{API_BASE_URL}/nutrition/search", params={"q": query}, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        # 核心變動：API 回傳 SearchResponse(query, count, results)
                        # 前端期望的是 results 列表
                        return data.get("results", [])
                    return None
                except Exception as e:
                    st.error(f"查詢失敗: {str(e)}")
                    return None
        
        with st.spinner(f"正在搜尋「{search_query}」..."):
            results = asyncio.run(search_nutrition(search_query))
        
        if results and len(results) > 0:
            st.success(f"✅ 找到 {len(results)} 筆結果")
            
            # Display Results
            for idx, item in enumerate(results[:10]):  # Limit to top 10
                nutrients = item.get('per_100g', {})
                with st.expander(f"🍽️ {item['name']} ({item['category']})", expanded=(idx == 0)):
                    # Basic Info
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("熱量", f"{nutrients.get('calories', 'N/A')} kcal")
                    with col_b:
                        st.metric("蛋白質", f"{nutrients.get('protein', 'N/A')} g")
                    with col_c:
                        st.metric("脂肪", f"{nutrients.get('fat', 'N/A')} g")
                    with col_d:
                        st.metric("碳水化合物", f"{nutrients.get('carbs', 'N/A')} g")
                    
                    # Detailed Nutrients
                    st.markdown("---")
                    st.markdown("**詳細營養素（每 100g）**")
                    
                    # Create 3 columns for detailed nutrients
                    detail_cols = st.columns(3)
                    nutrient_list = [
                        ("膳食纖維", nutrients.get('fiber', 'N/A'), "g"),
                        ("鈉", nutrients.get('sodium', 'N/A'), "mg"),
                        ("鉀", nutrients.get('potassium', 'N/A'), "mg"),
                        # 備選，如果資料庫有更多可以加在此
                    ]
                    
                    for i, (name, value, unit) in enumerate(nutrient_list):
                        with detail_cols[i % 3]:
                            st.markdown(f"**{name}**: {value} {unit}")
                    
                    # Food Code
                    st.markdown(f"<small style='color: #999;'>食品代碼: {item.get('food_code', 'N/A')}</small>", unsafe_allow_html=True)
        
        elif results is not None:
            st.warning(f"😔 找不到「{search_query}」相關的食物，請試試其他關鍵字")
    
    elif search_query:
        st.info("👆 請點擊「搜尋」按鈕或按 Enter 開始查詢")
    
    # Statistics
    st.markdown("---")
    st.markdown("### 📊 資料庫統計")
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("總食物數", "2,180 種")
    with stat_cols[1]:
        st.metric("營養素項目", "110 項")
    with stat_cols[2]:
        st.metric("資料來源", "衛福部")
    with stat_cols[3]:
        st.metric("更新日期", "2024")
    
    # Navigation
    st.markdown("---")
    nav_cols = st.columns([1, 1, 2])
    with nav_cols[0]:
        if st.button("⬅️ 返回儀表板", key="back_from_nutrition"):
            st.session_state.step = 3
            st.rerun()
    with nav_cols[1]:
        if st.button("🏠 回到首頁", key="home_from_nutrition"):
            st.session_state.step = 1
            st.rerun()

# ============ UI: Step 5 - Meal Logging ============
elif st.session_state.step == 5:
    st.markdown("### 🍱 飲食紀錄與營養加總")

    if not st.session_state.auth_token:
        st.warning("請先在側邊欄登入，才能記錄飲食。")
    else:
        with st.container(border=True):
            st.markdown("#### 📷 拍照辨識（粗估份量）")
            st.session_state.meal_vision_profile = st.radio(
                "份量模式",
                options=["bento", "fitness"],
                format_func=lambda v: "台式便當 / 一般外食" if v == "bento" else "健身高蛋白",
                horizontal=True,
                key="meal_vision_profile_radio",
            )
            uploaded_photo = st.file_uploader("上傳餐點照片（JPG/PNG/WEBP）", type=["jpg", "jpeg", "png", "webp"], key="meal_photo")
            col_photo_a, col_photo_b = st.columns([1, 1])
            with col_photo_a:
                if st.button("🔍 分析照片", width="stretch"):
                    if not uploaded_photo:
                        st.warning("請先上傳照片")
                    else:
                        import asyncio
                        try:
                            result = asyncio.run(suggest_food_from_photo(
                                uploaded_photo,
                                limit=5,
                                profile=st.session_state.meal_vision_profile,
                            ))
                            st.session_state.meal_vision_results = result.get("items", [])
                            if not st.session_state.meal_vision_results:
                                st.info("未找到明確候選，請改用下方手動對齊")
                        except Exception as e:
                            st.error(f"照片分析失敗: {str(e)}")
            with col_photo_b:
                if st.button("🧹 清除照片結果", width="stretch"):
                    st.session_state.meal_vision_results = []

            if st.session_state.meal_vision_results:
                st.markdown("**候選食物（可直接加入餐點）**")
                for idx, item in enumerate(st.session_state.meal_vision_results):
                    name_display = item.get("matched_name") or item.get("name", "未知")
                    category_display = item.get("matched_category") or "未知"
                    grams_min = item.get("grams_min", 1)
                    grams_max = item.get("grams_max", 2000)
                    grams_default = item.get("estimated_grams", 100.0)

                    grams_key = f"vision_grams_{idx}"
                    if grams_key not in st.session_state:
                        st.session_state[grams_key] = float(grams_default)

                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{name_display}**")
                        st.caption(f"分類：{category_display}｜估計範圍：{grams_min}–{grams_max} g")
                    with col2:
                        grams_value = st.number_input(
                            "份量(g)",
                            min_value=1.0,
                            max_value=2000.0,
                            value=float(st.session_state[grams_key]),
                            step=10.0,
                            key=grams_key,
                        )

                        quick_cols = st.columns(3)
                        with quick_cols[0]:
                            if st.button("小", key=f"vision_quick_s_{idx}", width="stretch"):
                                st.session_state[grams_key] = float(grams_min)
                                st.rerun()
                        with quick_cols[1]:
                            if st.button("中", key=f"vision_quick_m_{idx}", width="stretch"):
                                st.session_state[grams_key] = float(grams_default)
                                st.rerun()
                        with quick_cols[2]:
                            if st.button("大", key=f"vision_quick_l_{idx}", width="stretch"):
                                st.session_state[grams_key] = float(grams_max)
                                st.rerun()
                    with col3:
                        can_add = bool(item.get("matched_food_id"))
                        if st.button("➕ 加入", key=f"vision_add_{idx}", width="stretch", disabled=not can_add):
                            st.session_state.meal_draft_items.append({
                                "food_id": item.get("matched_food_id"),
                                "food_name": name_display,
                                "grams": grams_value,
                            })
                            st.success("已加入餐點清單")
                        if not can_add:
                            st.caption("需手動對齊")

        with st.container(border=True):
            st.markdown("#### ➕ 新增一餐")
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                food_query = st.text_input("輸入食物名稱", placeholder="例如：雞胸肉、白飯、香蕉")
            with col_b:
                grams = st.number_input("份量(g)", min_value=1.0, max_value=2000.0, value=100.0)
            with col_c:
                align_click = st.button("🔍 對齊", width="stretch")

            if align_click and food_query:
                import asyncio
                try:
                    align_res = asyncio.run(align_food_name(food_query, limit=5))
                    results = align_res.get("results", [])
                    st.session_state.meal_align_results = results
                    st.session_state.meal_align_query = food_query
                    if not results:
                        st.warning("找不到匹配的食物名稱，請換個關鍵字。")
                except Exception as e:
                    st.error(f"對齊失敗: {str(e)}")

            if st.session_state.meal_align_results:
                results = st.session_state.meal_align_results
                options = [f"{r['name']} ({r['category']}) | score={r['score']} | id={r['food_id']}" for r in results]
                selected = st.selectbox("選擇匹配結果", options, key="meal_align_select")
                if st.button("➕ 加入餐點", width="stretch"):
                    selected_id = selected.split("id=")[-1].strip()
                    selected_name = selected.split("(")[0].strip()
                    st.session_state.meal_draft_items.append({
                        "food_id": selected_id,
                        "food_name": selected_name,
                        "grams": grams,
                    })
                    st.session_state.meal_align_results = []
                    st.success("已加入餐點清單")

        if st.session_state.meal_draft_items:
            st.markdown("#### 🧾 餐點清單")
            df_items = pd.DataFrame(st.session_state.meal_draft_items)
            st.dataframe(df_items, width="stretch", hide_index=True)

            col_submit, col_clear = st.columns([1, 1])
            with col_submit:
                if st.button("✅ 儲存這一餐", width="stretch", type="primary"):
                    payload = {
                        "items": [
                            {
                                "food_id": item["food_id"],
                                "grams": item["grams"],
                                "portion_label": "manual",
                                "raw_text": item["food_name"],
                            }
                            for item in st.session_state.meal_draft_items
                        ],
                        "source": "manual",
                    }
                    import asyncio
                    resp = asyncio.run(create_meal(payload))
                    if resp.status_code == 200:
                        st.success("餐點已儲存")
                        st.session_state.meal_draft_items = []
                    else:
                        st.error(f"儲存失敗: {resp.text}")
            with col_clear:
                if st.button("🗑️ 清空清單", width="stretch"):
                    st.session_state.meal_draft_items = []

        st.markdown("---")
        st.markdown("#### 📊 近 7 日營養總結")
        import asyncio
        st.session_state.meal_summary = asyncio.run(fetch_meal_summary(days=7))
        if st.session_state.meal_summary:
            summary = st.session_state.meal_summary
            total = summary.get("total_nutrients", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("熱量", f"{total.get('calories', 0)} kcal")
            col2.metric("蛋白質", f"{total.get('protein', 0)} g")
            col3.metric("脂肪", f"{total.get('fat', 0)} g")
            col4.metric("碳水", f"{total.get('carbs', 0)} g")
        else:
            st.info("目前尚無飲食紀錄")

        st.markdown("---")
        st.markdown("#### 🕒 最近餐點")
        st.session_state.meal_recent = asyncio.run(fetch_recent_meals(limit=10))
        if st.session_state.meal_recent:
            for meal in st.session_state.meal_recent:
                with st.expander(f"餐點 {meal.get('eaten_at', '')}"):
                    st.write(f"來源：{meal.get('source', 'manual')}")
                    st.write(f"備註：{meal.get('note', '')}")
                    items = meal.get("items", [])
                    if items:
                        st.dataframe(pd.DataFrame(items), width="stretch", hide_index=True)
        else:
            st.info("尚無餐點紀錄")

    nav_cols = st.columns([1, 1, 2])
    with nav_cols[0]:
        if st.button("⬅️ 返回營養查詢", key="back_from_meals"):
            st.session_state.step = 4
            st.rerun()
    with nav_cols[1]:
        if st.button("🏠 回到首頁", key="home_from_meals"):
            st.session_state.step = 1
            st.rerun()

