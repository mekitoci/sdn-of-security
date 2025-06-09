#!/usr/bin/env python3
"""
測試 position_update API 端點的功能
"""

import requests
import json
import time

# 配置基礎 URL - 選擇一個使用
# BASE_URL = "http://localhost:8080"  # 本地測試
BASE_URL = "https://23f6-101-3-154-122.ngrok-free.app"  # ngrok 隧道

def get_ngrok_headers():
    """獲取 ngrok 所需的 headers"""
    return {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",  # 跳過 ngrok 瀏覽器警告
        "User-Agent": "SatelliteSDN-TestClient/1.0"
    }

def test_position_update():
    """測試 position_update API 端點"""
    
    # SDN 控制器的 API 端點
    api_url = f"{BASE_URL}/api/position_update"

    # 模擬衛星位置數據
    test_position_data = {
        "satellites": {
            "1": {
                "id": "SAT-001",
                "latitude": 24.7136,
                "longitude": 120.9818,
                "altitude": 550,
                "visible_stations": ["taipei", "tokyo"]
            },
            "2": {
                "id": "SAT-002", 
                "latitude": 35.6762,
                "longitude": 139.6503,
                "altitude": 550,
                "visible_stations": ["tokyo", "seoul"]
            }
        },
        "ground_stations": {
            "taipei": {
                "name": "Taipei Ground Station",
                "latitude": 25.0330,
                "longitude": 121.5654,
                "detection_range": 1000,
                "elevation_threshold": 10
            },
            "tokyo": {
                "name": "Tokyo Ground Station",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "detection_range": 1000,
                "elevation_threshold": 10
            }
        }
    }
    
    print("🛰️ 測試 position_update API 端點...")
    print(f"API URL: {api_url}")
    print(f"Base URL: {BASE_URL}")
    print(f"測試數據: {json.dumps(test_position_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 獲取適當的 headers
        headers = get_ngrok_headers()
        print(f"📡 使用 Headers: {headers}")
        
        # 發送 POST 請求
        response = requests.post(
            api_url,
            json=test_position_data,
            headers=headers,
            timeout=15,  # 增加超時時間給 ngrok
            verify=True  # 驗證 SSL (對 ngrok 重要)
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ 成功回應: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return True
        elif response.status_code == 404:
            print(f"❌ 404 錯誤: API 端點不存在")
            print(f"請檢查 SDN 控制器是否正確配置了 /api/position_update 端點")
            return False
        elif response.status_code == 400:
            print(f"❌ 400 錯誤: 請求數據格式有問題")
            print(f"回應內容: {response.text}")
            return False
        else:
            print(f"❌ 錯誤回應 ({response.status_code}): {response.text}")
            return False
            
    except requests.ConnectionError as e:
        print(f"❌ 連接錯誤: {e}")
        if "ngrok" in BASE_URL:
            print("請確認 ngrok 隧道是否正常運行")
            print("可以嘗試在瀏覽器中訪問:", BASE_URL)
        else:
            print("請確認 SDN 控制器是否在 localhost:8080 運行")
        return False
    except requests.Timeout:
        print("❌ 請求超時 (15秒)")
        print("ngrok 可能響應較慢，請檢查網路連接")
        return False
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL 錯誤: {e}")
        print("嘗試跳過 SSL 驗證...")
        # 重試不驗證 SSL
        try:
            response = requests.post(
                api_url,
                json=test_position_data,
                headers=headers,
                timeout=15,
                verify=False  # 跳過 SSL 驗證
            )
            print(f"🔓 重試 (跳過SSL驗證) - Status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ 成功回應: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                return True
        except Exception as retry_e:
            print(f"❌ 重試也失敗: {retry_e}")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        return False

def test_api_status():
    """測試 API 狀態端點以確認服務正常"""
    
    api_url = f"{BASE_URL}/api/status"
    
    print(f"\n🔍 測試 API 狀態端點: {api_url}")
    
    try:
        headers = get_ngrok_headers()
        response = requests.get(api_url, headers=headers, timeout=10, verify=True)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SDN 控制器正常運行")
            print(f"📊 衛星數量: {data.get('switches', {}).get('total', 0)}")
            print(f"📊 鏈路數量: {data.get('links', {}).get('total', 0)}")
            return True
        else:
            print(f"⚠️ API 狀態異常: {response.status_code}")
            print(f"回應: {response.text[:200]}...")
            return False
            
    except requests.exceptions.SSLError:
        print("🔓 SSL 錯誤，嘗試跳過 SSL 驗證...")
        try:
            response = requests.get(api_url, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                print("✅ SDN 控制器正常運行 (跳過SSL驗證)")
                print(f"📊 衛星數量: {data.get('switches', {}).get('total', 0)}")
                return True
        except Exception as e:
            print(f"❌ 重試失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 無法檢查 API 狀態: {e}")
        return False

def test_ngrok_connectivity():
    """測試 ngrok 連接性"""
    if "ngrok" not in BASE_URL:
        return True
        
    print(f"\n🔗 測試 ngrok 連接性: {BASE_URL}")
    
    try:
        headers = {"User-Agent": "SatelliteSDN-TestClient/1.0"}
        response = requests.get(BASE_URL, headers=headers, timeout=10, verify=False)
        
        print(f"📡 ngrok 狀態: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ngrok 隧道正常")
            return True
        elif "ngrok" in response.text.lower():
            print("⚠️ ngrok 回應了，但可能需要特殊處理")
            return True
        else:
            print("❌ ngrok 隧道異常")
            return False
            
    except Exception as e:
        print(f"❌ ngrok 連接測試失敗: {e}")
        return False

def check_position_data_format():
    """檢查 position_update 接收的數據格式"""
    
    print("\n📋 檢查 position_update 應該接收的數據格式:")
    
    expected_format = {
        "satellites": {
            "<dpid>": {
                "id": "衛星 ID (字符串)",
                "latitude": "緯度 (浮點數)",
                "longitude": "經度 (浮點數)", 
                "altitude": "高度 (整數/浮點數)",
                "visible_stations": "可見地面站列表 (數組)"
            }
        },
        "ground_stations": {
            "<station_name>": {
                "name": "地面站名稱 (字符串)",
                "latitude": "緯度 (浮點數)",
                "longitude": "經度 (浮點數)",
                "detection_range": "探測範圍 (可選, 默認1000)",
                "elevation_threshold": "仰角閾值 (可選, 默認10)"
            }
        }
    }
    
    print(json.dumps(expected_format, indent=2, ensure_ascii=False))

def main():
    """主測試函數"""
    
    print("=" * 60)
    print("🛰️ Position Update API 測試工具")
    print("=" * 60)
    print(f"🔗 目標 URL: {BASE_URL}")
    
    # 1. 檢查數據格式
    check_position_data_format()
    
    # 2. 測試 ngrok 連接 (如果適用)
    if not test_ngrok_connectivity():
        print("\n⚠️ ngrok 連接有問題，但仍繼續測試...")
    
    # 3. 測試 API 狀態
    if not test_api_status():
        print("\n⚠️ SDN 控制器 API 狀態檢查失敗，但仍繼續測試...")
    
    # 4. 測試 position_update API
    print("\n" + "="*40)
    if test_position_update():
        print("\n✅ position_update API 測試成功!")
    else:
        print("\n❌ position_update API 測試失敗!")
        print("\n🔧 可能的解決方案:")
        print("1. 檢查 ngrok 隧道是否正常運行")
        print("2. 確認 SDN 控制器是否在運行")
        print("3. 檢查防火牆設置")
        print("4. 嘗試使用 localhost URL 測試")
    
    print("\n" + "="*60)
    print("測試完成")

if __name__ == "__main__":
    main() 