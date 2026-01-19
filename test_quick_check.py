#!/usr/bin/env python3
"""快速测试Streamlit前端与后端API的连接"""
import httpx
import time
import sys

def test_connection():
    print("\n" + "="*60)
    print("🔍 测试 Streamlit 与后端 API 的连接")
    print("="*60 + "\n")
    
    # 测试后端
    print("1️⃣  测试后端API (port 8000)...")
    try:
        resp = httpx.get('http://localhost:8000/health', timeout=3)
        print(f"   ✅ 后端正常: {resp.json()}\n")
        backend_ok = True
    except Exception as e:
        print(f"   ❌ 后端连接失败: {e}\n")
        backend_ok = False
    
    # 测试Streamlit
    print("2️⃣  测试Streamlit (port 8501)...")
    try:
        resp = httpx.get('http://localhost:8501', timeout=3)
        print(f"   ✅ Streamlit正常: HTTP {resp.status_code}\n")
        streamlit_ok = True
    except Exception as e:
        print(f"   ⚠️  Streamlit未响应: {e}\n")
        streamlit_ok = False
    
    # 测试API端点
    print("3️⃣  测试关键API端点...")
    endpoints = [
        "/api/v1/nutrition/stats",
        "/api/v1/nutrition/categories",
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            resp = httpx.get(f'http://localhost:8000{endpoint}', timeout=3)
            if resp.status_code == 200:
                print(f"   ✅ {endpoint}: 200 OK")
            else:
                print(f"   ⚠️  {endpoint}: {resp.status_code}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ {endpoint}: {e}")
            all_ok = False
    
    print("\n" + "="*60)
    print("检查前端配置...")
    print("="*60 + "\n")
    
    try:
        with open('frontend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            for i, line in enumerate(content.split('\n')[:15], 1):
                if 'API_BASE_URL' in line:
                    print(f"✅ 第 {i} 行: {line.strip()}")
                    if '8000' in line:
                        print("   ✓ 正确配置为端口 8000\n")
                    elif '8001' in line:
                        print("   ❌ 错误配置为端口 8001 (应为 8000)\n")
    except Exception as e:
        print(f"❌ 读取配置失败: {e}\n")
    
    print("="*60)
    print("总结")
    print("="*60)
    if backend_ok and streamlit_ok and all_ok:
        print("✅ 所有服务正常运行！")
        print("   • 后端 API: http://localhost:8000 ✓")
        print("   • Streamlit UI: http://localhost:8501 ✓")
        print("   • 前端到后端连接: 已就绪 ✓\n")
        return 0
    else:
        print("⚠️  存在以下问题:")
        if not backend_ok:
            print("   • 后端API未运行")
        if not streamlit_ok:
            print("   • Streamlit未运行或未就绪")
        if not all_ok:
            print("   • 某些API端点不可用")
        print()
        return 1

if __name__ == "__main__":
    time.sleep(2)  # 给Streamlit启动的时间
    sys.exit(test_connection())
