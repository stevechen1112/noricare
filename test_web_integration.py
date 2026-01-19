#!/usr/bin/env python3
"""
完整的Personal Health Web系统集成测试
验证前端、后端、API连接和数据流
"""
import httpx
import json
import time
from datetime import datetime

class WebSystemTester:
    def __init__(self):
        self.api_base = "http://localhost:8000/api/v1"
        self.streamlit_url = "http://localhost:8501"
        self.results = {
            "backend": False,
            "api_endpoints": {},
            "frontend": False,
            "integration": False
        }
    
    def test_backend_health(self):
        """测试后端健康状态"""
        print("\n" + "="*70)
        print("1️⃣  后端API健康检查")
        print("="*70)
        try:
            resp = httpx.get(f"{self.api_base[:-7]}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ 后端正常运行")
                print(f"   • 状态: {data.get('status')}")
                print(f"   • 模型: {data.get('gemini_model')}")
                self.results["backend"] = True
                return True
            else:
                print(f"❌ 后端返回错误代码: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 后端连接失败: {e}")
            return False
    
    def test_api_endpoints(self):
        """测试关键API端点"""
        print("\n" + "="*70)
        print("2️⃣  API端点可用性测试")
        print("="*70)
        
        endpoints = [
            ("GET", "/nutrition/stats", "营养数据库统计"),
            ("GET", "/nutrition/categories", "食物分类列表"),
            ("GET", "/nutrition/search?q=米", "营养查询 - 搜索食物"),
        ]
        
        all_ok = True
        for method, path, desc in endpoints:
            try:
                url = self.api_base + path
                resp = httpx.get(url, timeout=5)
                status = resp.status_code
                
                if status < 400:
                    print(f"✅ {desc}")
                    print(f"   路径: {path}")
                    print(f"   状态: {status}")
                    self.results["api_endpoints"][path] = True
                else:
                    print(f"⚠️  {desc} - 返回 {status}")
                    self.results["api_endpoints"][path] = False
                    all_ok = False
            except Exception as e:
                print(f"❌ {desc} - 失败: {e}")
                self.results["api_endpoints"][path] = False
                all_ok = False
        
        return all_ok
    
    def test_frontend_config(self):
        """测试前端配置"""
        print("\n" + "="*70)
        print("3️⃣  前端配置检查")
        print("="*70)
        
        try:
            with open('frontend/main.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 查找API_BASE_URL
                for i, line in enumerate(content.split('\n')[:20], 1):
                    if 'API_BASE_URL' in line and '=' in line:
                        api_url = line.split('=')[1].strip().strip('"\'')
                        print(f"✅ 前端API配置找到")
                        print(f"   API_BASE_URL = {api_url}")
                        
                        if "8000" in api_url:
                            print(f"   ✓ 正确指向后端端口 8000")
                            return True
                        elif "8001" in api_url:
                            print(f"   ❌ 错误指向端口 8001（应为 8000）")
                            return False
                
                print("❌ 未找到API_BASE_URL配置")
                return False
        except Exception as e:
            print(f"❌ 读取前端配置失败: {e}")
            return False
    
    def test_streamlit_availability(self):
        """测试Streamlit可用性"""
        print("\n" + "="*70)
        print("4️⃣  Streamlit前端可用性")
        print("="*70)
        
        try:
            # Streamlit的健康检查有些复杂，我们用间接方式
            resp = httpx.get(self.streamlit_url, timeout=5, follow_redirects=True)
            if resp.status_code == 200 or resp.status_code == 307:
                print(f"✅ Streamlit前端可访问")
                print(f"   URL: {self.streamlit_url}")
                print(f"   状态: {resp.status_code}")
                self.results["frontend"] = True
                return True
            else:
                print(f"⚠️  Streamlit返回状态 {resp.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  Streamlit连接问题: {e}")
            print(f"   (这通常不影响功能，Streamlit通常需要多次尝试)")
            return False
    
    def test_integration(self):
        """测试前端与后端集成"""
        print("\n" + "="*70)
        print("5️⃣  前端与后端集成测试")
        print("="*70)
        
        # 模拟前端会发起的请求
        print("模拟前端调用后端API...")
        
        try:
            # 测试营养查询 - 这是前端会使用的功能
            search_url = f"{self.api_base}/nutrition/search"
            resp = httpx.get(search_url, params={"q": "雞胸肉"}, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ 营养查询API工作正常")
                print(f"   搜索词: 雞胸肉")
                if data:
                    result = data[0] if isinstance(data, list) else data
                    print(f"   返回结果: {str(result)[:100]}...")
                self.results["integration"] = True
                return True
            else:
                print(f"⚠️  API返回状态 {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            return False
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*70)
        print("📊 测试总结")
        print("="*70 + "\n")
        
        checks = [
            ("后端API", self.results["backend"]),
            ("API端点", all(self.results["api_endpoints"].values()) if self.results["api_endpoints"] else False),
            ("前端配置", self.results.get("frontend_config", False)),
            ("Streamlit", self.results["frontend"]),
            ("前后端集成", self.results["integration"]),
        ]
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        for name, result in checks:
            icon = "✅" if result else "❌"
            print(f"{icon} {name}")
        
        print(f"\n总体通过: {passed}/{total}")
        
        if passed == total:
            print("\n✨ 系统正常运行！Web应用已完全就绪。")
            print("   • 访问 http://localhost:8501 使用Streamlit UI")
            print("   • API文档: http://localhost:8000/docs")
        else:
            print("\n⚠️  仍有一些问题需要解决。请检查上方的错误信息。")
        
        return passed == total
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🔍 "*20)
        print("Personal Health Web系统集成测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔍 "*20 + "\n")
        
        # 运行所有测试
        self.test_backend_health()
        self.test_api_endpoints()
        frontend_config_ok = self.test_frontend_config()
        self.results["frontend_config"] = frontend_config_ok
        self.test_streamlit_availability()
        self.test_integration()
        
        # 打印总结
        return self.print_summary()

if __name__ == "__main__":
    tester = WebSystemTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
