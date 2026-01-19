# 🚀 Personal Health Web - 快速启动指南

**系统状态**: ✅ Web系统已完全修复并就绪

---

## ⚡ 3步快速启动

### 1️⃣ 打开命令行
```powershell
cd C:\Users\User\Desktop\personalhealth
```

### 2️⃣ 启动系统
```powershell
python run_system.py
```

### 3️⃣ 打开浏览器
访问: **http://localhost:8501**

---

## 🌐 服务地址

| 服务 | 地址 |
|------|------|
| 💻 Web UI | http://localhost:8501 |
| 🔧 API | http://localhost:8000 |
| 📚 API文档 | http://localhost:8000/docs |
| 💚 健康检查 | http://localhost:8000/health |

---

## 📱 使用流程

### 第一次使用
1. **个人资料** - 填写基本信息 (姓名、年龄、身高、体重)
2. **上传报告** - 上传健检报告图片
3. **查看结果** - AI会自动分析并生成建议 (~30秒)
4. **营养查询** - 搜索食物的营养信息

### 快速操作
- 🔍 **搜索食物** - "营养查询"页面输入食物名称
- 💬 **AI问答** - 侧边栏"快速咨询"提问
- 📊 **查看报告** - 点击左侧"健康儀表板"查看详情

---

## 🛠️ 如果出现问题

### 后端无法启动
```powershell
# 查看端口占用
netstat -ano | findstr :8000

# 如果有占用，终止进程
taskkill /PID XXXX /F
```

### Streamlit无法连接
```powershell
# 清理Streamlit缓存
rm -r ~/.streamlit

# 重新运行
python run_system.py
```

### 前端显示"连接服务器失败"
✅ 这个问题已修复！检查:
- frontend/main.py第8行应该是 `API_BASE_URL = "http://localhost:8000/api/v1"`
- 重启Streamlit: 按 Ctrl+C 然后重新运行 `python run_system.py`

---

## 📖 详细文档

- 完整系统分析: [WEB_SYSTEM_ANALYSIS.md](WEB_SYSTEM_ANALYSIS.md)
- 启动指南: [STARTUP_GUIDE.md](STARTUP_GUIDE.md)
- 更新日志: [CHANGELOG.md](CHANGELOG.md)
- 营养DB报告: [PHASE1_NUTRITION_DB_REPORT.md](PHASE1_NUTRITION_DB_REPORT.md)

---

## 📊 系统状态检查

```powershell
# 运行完整检查
python test_web_integration.py
```

**期望结果**:
```
✅ 后端API
✅ API端点
✅ 前端配置
✅ 前后端集成
```

---

## 💡 Tips

- 💾 所有数据保存在本地SQLite数据库 (`sql_app.db`)
- 🖼️ 上传的图片存放在 `uploads/` 文件夹
- 🔑 Gemini API Key在 `.env` 文件中配置
- 🌍 可以通过本机IP地址访问 (例: http://192.168.1.176:8501)

---

**祝您使用愉快! 🌿**

