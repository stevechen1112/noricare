#!/usr/bin/env python3
"""测试Web连接和API集成"""
import httpx
import json
import time

def test_backend():
    """测试后端API"""
    print("\n" + "="*60)
    print("测试后端 API 连接")
    print("="*60)
    
    try:
        # 健康检查
        resp = httpx.get('http://localhost:8000/health', timeout=5)
        print(f"✅ 健康检查: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        # 获取API文档
        resp_docs = httpx.get('http://localhost:8000/docs', timeout=5)
        print(f"✅ API文档: {resp_docs.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False

def test_streamlit():
    """测试Streamlit前端"""
    print("\n" + "="*60)
    print("测试 Streamlit 前端")
    print("="*60)
    
    try:
        resp = httpx.get('http://localhost:8501', timeout=5)
        print(f"✅ Streamlit 连接: {resp.status_code}")
        return True
    except Exception as e:
        print(f"⚠️  Streamlit 连接问题: {e}")
        return False

def test_api_endpoints():
    """测试关键API端点"""
    print("\n" + "="*60)
    print("测试 API 端点")
    print("="*60)
    
    endpoints = [
        ("GET", "/api/v1/nutrition/stats", {}),
        ("GET", "/api/v1/nutrition/categories", {}),
    ]
    
    base_url = "http://localhost:8000"
    
    for method, endpoint, data in endpoints:
        url = base_url + endpoint
        try:
            if method == "GET":
                resp = httpx.get(url, timeout=5)
            else:
                resp = httpx.post(url, json=data, timeout=5)
            
            print(f"✅ {method} {endpoint}: {resp.status_code}")
            if resp.status_code < 400:
                print(f"   数据: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:200]}...")
        except Exception as e:
            print(f"❌ {method} {endpoint}: {e}")

def test_frontend_config():
    """检查前端配置"""
    print("\n" + "="*60)
    print("前端配置检查")
    print("="*60)
    
    try:
        with open('frontend/main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找API_BASE_URL配置
            for i, line in enumerate(content.split('\n')[:20], 1):
                if 'API_BASE_URL' in line:
                    print(f"第 {i} 行: {line.strip()}")
    except Exception as e:
        print(f"❌ 读取前端配置失败: {e}")

if __name__ == "__main__":
    print("\n🔍 Personal Health Web 系统连接性测试\n")
    
    backend_ok = test_backend()
    streamlit_ok = test_streamlit()
    test_api_endpoints()
    test_frontend_config()
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"后端 API: {'✅ 正常' if backend_ok else '❌ 失败'}")
    print(f"Streamlit: {'✅ 正常' if streamlit_ok else '⚠️  问题'}")
    print("\n⚠️  关键问题发现:")
    print("   • Streamlit 前端使用 API_BASE_URL = 'http://localhost:8001/api/v1'")
    print("   • 但后端实际运行在 http://localhost:8000")
    print("   • 这会导致前端无法连接到后端API\n")
