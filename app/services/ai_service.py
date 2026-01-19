import json
import asyncio
import google.generativeai as genai
from app.core.config import settings
from app.schemas.user import UserProfile, UserLifestyle
from app.schemas.analysis import NutritionReport, AdviceSection
from app.services.knowledge_service import knowledge_service
from app.services.nutrition_db_service import get_nutrition_service

# Initialize Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
# Using Gemini 3 Pro (Preview) equivalent or latest stable
model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL_NAME)

# 設定生成超時時間（秒）
GENERATION_TIMEOUT = 90

class AIService:
    async def generate_comprehensive_report(self, 
                                            user_profile: UserProfile, 
                                            health_data: dict,
                                            abnormal_items: list[str],
                                            history_records: list[dict] = [],
                                            risk_assessment: dict = None) -> NutritionReport:
        """
        整合所有 AI 生成邏輯，產出完整報告。
        """
        
        # 1. 建構 Prompt 上下文
        lifestyle_context = self._build_lifestyle_context(user_profile.lifestyle) if user_profile.lifestyle else "無特殊生活型態記錄"
        
        # RAG Search: Retrieve professional knowledge
        professional_knowledge = knowledge_service.get_relevant_context(tags=abnormal_items)
        
        # 處理歷史數據字串
        history_context = ""
        if history_records:
            history_context = "【歷史健康趨勢】\n"
            last_record = history_records[0] 
            history_context += f"上次檢查日期: {last_record.get('date', '未知')}\n"
            history_context += f"上次數據: {json.dumps(last_record.get('data', {}), ensure_ascii=False)}\n"
        
        # 計算 BMI
        bmi = round(user_profile.weight_kg / ((user_profile.height_cm / 100) ** 2), 1) if user_profile.height_cm and user_profile.weight_kg else None
        bmi_status = ""
        if bmi:
            if bmi < 18.5:
                bmi_status = "過輕"
            elif bmi < 24:
                bmi_status = "正常"
            elif bmi < 27:
                bmi_status = "過重"
            else:
                bmi_status = "肥胖"
        
        # 分析異常摘要（讓 AI 更容易抓重點）
        abnormal_summary = ""
        if abnormal_items:
            abnormal_summary = f"""
    ⚠️ **重要異常發現 ({len(abnormal_items)} 項)**：
    {chr(10).join(f'  - {item}' for item in abnormal_items)}
    """
        else:
            abnormal_summary = "所有指標皆在正常範圍內"
        
        # 風險評估摘要（從後端計算引擎得來）
        risk_summary = ""
        if risk_assessment:
            # 移除 __risk_assessment__ 避免重複
            clean_health_data = {k: v for k, v in health_data.items() if not k.startswith("__")}
            
            risk_parts = []
            for category, risks in risk_assessment.items():
                if category == "calculated_metrics":
                    continue
                if risks:
                    risk_parts.append(f"  【{category}】")
                    for r in risks:
                        risk_parts.append(f"    {r}")
            
            if risk_parts:
                risk_summary = "===== 系統風險評估 =====\n" + "\n".join(risk_parts)
            
            # 如果有計算指標，也加入
            calc_metrics = risk_assessment.get("calculated_metrics", {})
            if calc_metrics:
                risk_summary += f"\n\n【計算指標】\n"
                for k, v in calc_metrics.items():
                    risk_summary += f"  - {k}: {v}\n"
        else:
            clean_health_data = health_data
        
        base_context = f"""
    ===== 使用者健康檔案 =====
    【基本資料】
    - 年齡: {user_profile.age} 歲
    - 性別: {'男性' if user_profile.gender == 'male' else '女性'}
    - 身高: {user_profile.height_cm} cm
    - 體重: {user_profile.weight_kg} kg
    - BMI: {bmi} ({bmi_status})
    - 健康目標: {', '.join(user_profile.health_goals)}
    - 生活型態: {lifestyle_context}

    {history_context if history_context else "【歷史紀錄】無先前檢查紀錄"}

    ===== 本次健檢數據 =====
    {json.dumps(clean_health_data if risk_assessment else health_data, ensure_ascii=False, indent=2)}

    ===== 異常指標摘要 =====
    {abnormal_summary}
    
    {risk_summary}

    ===== 專業知識庫參考 =====
    {professional_knowledge}
    """

        # 2. 並行呼叫各個生成模組（大幅加速！）
        print("[AI Service] Starting parallel AI generation...")
        import time
        start_time = time.time()
        
        try:
            # 使用 asyncio.gather 並行執行三個 AI 呼叫
            food_task = self._generate_food_advice(base_context)
            supp_task = self._generate_supplement_advice(base_context, health_data)
            meal_task = self._generate_meal_plan(base_context)
            
            # 設定超時，避免無限等待
            results = await asyncio.wait_for(
                asyncio.gather(food_task, supp_task, meal_task, return_exceptions=True),
                timeout=GENERATION_TIMEOUT
            )
            
            food_advice_text, supp_advice_text, meal_plan_text = results
            
            # 檢查是否有例外
            if isinstance(food_advice_text, Exception):
                print(f"[AI Service] Food advice error: {food_advice_text}")
                food_advice_text = "抱歉，飲食建議生成時發生錯誤，請稍後再試。"
            if isinstance(supp_advice_text, Exception):
                print(f"[AI Service] Supplement advice error: {supp_advice_text}")
                supp_advice_text = "抱歉，保健品建議生成時發生錯誤，請稍後再試。"
            if isinstance(meal_plan_text, Exception):
                print(f"[AI Service] Meal plan error: {meal_plan_text}")
                meal_plan_text = "抱歉，餐點計畫生成時發生錯誤，請稍後再試。"
                
        except asyncio.TimeoutError:
            print(f"[AI Service] Parallel generation timed out after {GENERATION_TIMEOUT}s")
            food_advice_text = "AI 生成超時，請稍後再試。"
            supp_advice_text = "AI 生成超時，請稍後再試。"
            meal_plan_text = "AI 生成超時，請稍後再試。"
        
        elapsed = time.time() - start_time
        print(f"[AI Service] Parallel generation completed in {elapsed:.2f}s")

        # 3. 解析與結構化 (這一步在 MVP 階段可能是透過 Prompt 直接要求 JSON，或後處理)
        # 這裡為了 MVP 穩定性，我們先假設回傳的是 Markdown，後續可再做更細的 parsing
        # 暫時用簡單的封裝
        
        # 清理 health_data，移除 __risk_assessment__ 等內部資料
        clean_health_data_for_snapshot = {k: v for k, v in health_data.items() if not k.startswith("__")}
        
        # 從 risk_assessment 取得健康分數，如果沒有則計算
        health_score = 75
        if risk_assessment:
            calc_metrics = risk_assessment.get("calculated_metrics", {})
            if "health_score" in calc_metrics:
                health_score = calc_metrics["health_score"]
        
        return NutritionReport(
            report_id="temp_id",
            created_at="now",
            health_score=health_score,
            food_advice=[AdviceSection(title="AI 飲食建議", content=food_advice_text)],
            supplement_advice=[AdviceSection(title="AI 保健建議", content=supp_advice_text)],
            meal_plan={"markdown_content": meal_plan_text},
            health_data_snapshot=clean_health_data_for_snapshot
        )

    def _build_lifestyle_context(self, lifestyle: UserLifestyle) -> str:
        ctx = []
        if lifestyle.dietary_preference:
            ctx.append(f"Dietary Preference: {lifestyle.dietary_preference}")
        if lifestyle.allergies:
            ctx.append(f"Allergies: {', '.join(lifestyle.allergies)}")
        if lifestyle.eating_habits:
            ctx.append(f"Eating Habits: {', '.join(lifestyle.eating_habits)}")
        ctx.append(f"Activity Level: {lifestyle.activity_level}")
        return "; ".join(ctx)

    async def _generate_food_advice(self, context: str) -> str:
        prompt = f"""
        # Role
        You are an expert Taiwanese Nutritionist (AI Agent).
        
        # Task
        Provide personalized FOOD advice based on the provided context.
        
        # Context
        {context}
        
        # Requirements
        1. **Personalization**: Connect advice to 'Lifestyle' and 'Abnormal Findings'.
        2. **Trend Analysis**: If 'History Analysis' shows changes:
           - Improvement: Praise specific actions.
           - Regression: Gently analyze causes.
        3. **Evidence-Based (RAG)**: 
           - MUST cross-reference 'Knowledge Base'.
           - If suggesting food, ensure it aligns with 'general_guidelines.md'.
           - If specific food interactions exist in 'drug_interactions', WARN the user.
        4. **Tone**: Encouraging, professional, empathetic.
        5. **Output**: Markdown format.
        """
        import time
        start = time.time()
        response = await model.generate_content_async(prompt)
        print(f"[AI Service] _generate_food_advice took {time.time()-start:.2f}s")
        return response.text

    async def _generate_supplement_advice(self, context: str, health_data: dict) -> str:
        # eGFR Safety Check
        egfr = health_data.get("eGFR", {}).get("value", 90)
        safety_note = ""
        if isinstance(egfr, (int, float)) and egfr < 60:
            safety_note = "⚠️ CRITICAL WARNING: User has low eGFR (<60). AVOID high protein, potassium, or phosphorus supplements."

        prompt = f"""
        # Role
        You are a cautious and professional Nutritionist.
        
        # Task
        Provide SUPPLEMENT advice.
        
        # Context
        {context}
        
        {safety_note}
        
        # Output Structure
        1. **Prioritized Suggestions**: For abnormal items.
        2. **Supportive Suggestions**: For general health.
        3. **⛔ Safety Contraindications (Most Important)**:
           - List ANY drug-food interactions found in 'Knowledge Base'.
           - List ANY warnings for their specific condition (e.g. eGFR).
        
        # Safety Guardrails (Strict Enforcement)
        1. **Compliance**: Follow 'supplement_safety.md'.
        2. **No Medical Claims**: Do NOT use words like "Treat(治療)", "Cure(治癒)". Use "Support(輔助)", "Maintain(維持)".
        3. **Source Citation**: If you mention a rule from the Knowledge Base, explicit state "根據知識庫指引...".
        """
        import time
        start = time.time()
        response = await model.generate_content_async(prompt)
        print(f"[AI Service] _generate_supplement_advice took {time.time()-start:.2f}s")
        return response.text

    async def _generate_meal_plan(self, context: str) -> str:
        prompt = f"""
        # Task
        Design a 7-Day Meal Plan.
        
        # Context
        {context}
        
        # Requirements
        1. **Guideline Alignment**: Adhere to 'general_guidelines.md' (e.g., Veggies > 3 servings).
        2. **Variety**: Avoid repetition.
        3. **Local Friendly**: Focus on commercially available food in Taiwan (Lunch boxes, Convenience stores) if 'Lifestyle' suggests busy work.
        4. **Format**:
           Day 1: Breakfast / Lunch / Dinner
           ...
        """
        import time
        start = time.time()
        response = await model.generate_content_async(prompt)
        print(f"[AI Service] _generate_meal_plan took {time.time()-start:.2f}s")
        return response.text

    async def generate_chat_response(self, user_id: str, message: str, context: dict, history: list) -> str:
        """
        處理使用者與營養師的對話。
        """
        # 1. 偵測是否需要查詢營養資料庫 (Tool Use Simulation)
        nutrition_context = ""
        intent_keywords = ["多少錢", "內容", "成分", "熱量", "蛋白質", "脂肪", "碳水", "營養", "查", "搜尋", "雞蛋", "雞肉", "米飯"]
        
        # 簡單的意圖偵測：如果訊息包含關鍵字，嘗試搜尋資料庫
        if any(kw in message for kw in intent_keywords) and len(message) < 50:
            nutrition_service = get_nutrition_service()
            # 嘗試提取食物名稱 (這裡先簡化，直接用整個訊息或部分去查)
            search_query = message.replace("查", "").replace("搜尋", "").replace("多少", "").replace("成分", "").strip()
            if search_query:
                results = nutrition_service.search(search_query, limit=3)
                if results:
                    nutrition_context = "\n【從營養資料庫找到的精確數據】\n"
                    for r in results:
                        p = r.get('per_100g', {})
                        nutrition_context += f"- {r['name']} (每100g): {p.get('calories')}kcal, 蛋白質:{p.get('protein')}g, 碳水:{p.get('carbs')}g, 脂肪:{p.get('fat')}g\n"

        # 2. RAG Search for Chat
        tags = []
        if context and "abnormal_items" in context:
            tags = context["abnormal_items"] # Use previous report's abnormalities as context
        
        professional_knowledge = knowledge_service.get_relevant_context(tags=tags)

        # 3. 建構 Chat Context
        system_prompt = f"""
        # Persona
        You are "Health Coach" (AI Nutritionist), warm, professional, and knowledgeable about Taiwan's food culture.
        
        # Knowledge Base (Available Source of Truth)
        {professional_knowledge}
        
        # Nutrition Database Data (Real-time search results)
        {nutrition_context if nutrition_context else "No specific food data searched."}
        
        # Instructions
        1. Answer User's question clearly.
        2. ALWAYS ground your answer in the provided 'Knowledge Base' or 'Nutrition Database Data' if available. 
        3. If you use data from 'Nutrition Database Data', mention that it's based on the official Taiwan Food Database.
        4. Keep it conversational but concise.
        
        # Context (User Report)
        """
        
        # 轉換 Context 為字串
        context_str = json.dumps(context, ensure_ascii=False) if context else "No Report Data"
        
        # 處理對話歷史 (僅取最近 5 輪以節省 Token)
        chat_history_text = ""
        for h in history[-10:]:
            role = "User" if h.get("role") == "user" else "Nutritionist"
            chat_history_text += f"{role}: {h.get('content')}\n"
            
        full_prompt = f"""
        {system_prompt}
        {context_str}
        
        之前的對話記錄:
        {chat_history_text}
        
        現在 User 說: {message}
        
        Nutritionist:
        """
        
        response = await model.generate_content_async(full_prompt)
        return response.text

ai_service = AIService()
