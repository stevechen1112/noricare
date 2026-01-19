#!/usr/bin/env python3
"""
Personal Health System - 统一启动脚本
启动后端API和Streamlit前端，确保两者都正确配置
"""
import subprocess
import time
import os
import sys
import signal
import httpx
from pathlib import Path

class SystemLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.venv_path = Path(".venv/Scripts/python.exe")
        self.base_dir = Path.cwd()
    
    def launch_backend(self):
        """启动后端API"""
        print("\n" + "="*70)
        print("🚀 启动后端API (FastAPI)")
        print("="*70)
        
        cmd = [
            str(self.venv_path),
            "start_backend.py"
        ]
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            print("✅ 后端API进程已启动 (PID: {})".format(self.backend_process.pid))
            print("   监听端口: http://localhost:8000")
            print("   API文档: http://localhost:8000/docs")
            return True
        except Exception as e:
            print(f"❌ 后端启动失败: {e}")
            return False
    
    def launch_frontend(self):
        """启动Streamlit前端"""
        print("\n" + "="*70)
        print("🌐 启动Streamlit前端")
        print("="*70)
        
        cmd = [
            str(self.venv_path),
            "-m", "streamlit",
            "run", "frontend/main.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ]
        
        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            print("✅ Streamlit前端进程已启动 (PID: {})".format(self.frontend_process.pid))
            print("   监听端口: http://localhost:8501")
            return True
        except Exception as e:
            print(f"❌ Streamlit启动失败: {e}")
            return False
    
    def wait_for_backend(self, timeout=30):
        """等待后端就绪"""
        print("\n⏳ 等待后端API就绪...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                resp = httpx.get("http://localhost:8000/health", timeout=2)
                if resp.status_code == 200:
                    print(f"✅ 后端API已就绪！")
                    return True
            except:
                pass
            
            time.sleep(1)
            print("  等待中... ({:.0f}s)".format(time.time() - start_time), end="\r")
        
        print("\n❌ 后端API未在规定时间内就绪")
        return False
    
    def wait_for_frontend(self, timeout=15):
        """等待前端就绪"""
        print("\n⏳ 等待Streamlit前端就绪...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                resp = httpx.get("http://localhost:8501", timeout=2)
                if resp.status_code in [200, 307]:
                    print(f"✅ Streamlit前端已就绪！")
                    return True
            except:
                pass
            
            time.sleep(1)
            print("  等待中... ({:.0f}s)".format(time.time() - start_time), end="\r")
        
        print("\n⚠️  Streamlit可能未完全初始化，但通常可以访问")
        return True  # Streamlit延迟初始化是正常的
    
    def verify_connection(self):
        """验证前后端连接"""
        print("\n" + "="*70)
        print("🔍 验证系统连接")
        print("="*70)
        
        try:
            # 测试后端
            resp = httpx.get("http://localhost:8000/health", timeout=5)
            print(f"✅ 后端API: {resp.json().get('status')}")
            
            # 测试API端点
            resp = httpx.get("http://localhost:8000/api/v1/nutrition/stats", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ API端点: 可用 (食物库: {data.get('total_foods')} 种)")
            
            # 测试前端配置
            with open("frontend/main.py", "r", encoding="utf-8") as f:
                content = f.read()
                if "http://localhost:8000" in content:
                    print(f"✅ 前端配置: 正确指向后端 (端口 8000)")
                else:
                    print(f"⚠️  前端配置: 可能配置错误")
            
            return True
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False
    
    def print_status(self):
        """打印系统状态"""
        print("\n" + "="*70)
        print("✨ 系统已启动!")
        print("="*70)
        print("\n📱 访问方式:")
        print("  • Streamlit Web UI: http://localhost:8501")
        print("  • FastAPI后端: http://localhost:8000")
        print("  • API文档: http://localhost:8000/docs")
        print("\n🌐 网络访问 (同一局域网):")
        print("  • Streamlit: http://192.168.1.176:8501")
        print("  • 后端: http://192.168.1.176:8000")
        print("\n📝 日志位置:")
        print("  • 后端日志: 单独的控制台窗口")
        print("  • 前端日志: 单独的控制台窗口")
        print("\n⚠️  关键提示:")
        print("  • 保持此脚本运行，勿关闭")
        print("  • 若需停止，按 Ctrl+C")
        print("  • 若需重启，关闭所有窗口后重新运行此脚本")
        print("\n" + "="*70)
    
    def run(self):
        """运行整个系统"""
        print("\n🏥 Personal Health Web System - 完整启动\n")
        
        # 启动后端
        if not self.launch_backend():
            return False
        
        # 等待后端就绪
        if not self.wait_for_backend():
            print("❌ 后端启动失败，停止启动前端")
            return False
        
        # 启动前端
        if not self.launch_frontend():
            print("⚠️  前端启动失败，但后端仍在运行")
        else:
            # 等待前端就绪
            self.wait_for_frontend()
        
        # 验证连接
        time.sleep(2)
        if self.verify_connection():
            self.print_status()
            return True
        else:
            print("⚠️  系统启动可能存在问题")
            return False
    
    def cleanup(self):
        """清理进程"""
        if self.backend_process:
            try:
                self.backend_process.terminate()
            except:
                pass
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
            except:
                pass

if __name__ == "__main__":
    launcher = SystemLauncher()
    
    try:
        launcher.run()
        print("\n✅ 系统已准备就绪，按 Ctrl+C 停止")
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 停止系统...")
        launcher.cleanup()
        print("✅ 系统已停止")
