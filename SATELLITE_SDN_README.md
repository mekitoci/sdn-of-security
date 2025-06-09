# 動態衛星 SDN 網路模擬器

這是一個基於 Python 開發的動態衛星 SDN 網路模擬器，整合了 Mininet、Ryu 控制器和自定義的衛星軌道模擬功能。

## 📋 系統架構

```
[Ryu Controller]
        |
 -------------------------------
|              |               |
[SAT1]       [SAT2]         [SAT3]   ← 每顆都是 SDN Switch
   |             |              |
[GS1]         [GS2]         [GS3]    ← 地面站 Host or Router
```

隨時間進行：
- SAT2 離開 → 移除 SAT2
- SAT4 進入 → 加入 SAT4，建立 link 到可見地面站

## 🚀 主要功能

### 1. 動態拓撲管理
- **衛星軌道模擬**: 基於簡化的 LEO 軌道模型
- **動態連接管理**: 根據衛星位置自動建立/斷開與地面站的連接
- **實時拓撲更新**: 支援衛星的動態加入和離開

### 2. SDN 控制器
- **智能路由**: 支援最短路徑、負載平衡、延遲最優等路由算法
- **拓撲感知**: 自動感知網路拓撲變化並更新路由
- **流表管理**: 動態安裝和清理流表項

### 3. 流量模擬與測試
- **多種流量模式**: 支援 ping 測試、iperf 吞吐量測試、視頻流模擬等
- **性能監控**: 持續監控網路連通性和性能指標
- **故障模擬**: 測試衛星切換和故障恢復能力

## 📁 檔案結構

```
.
├── satellite_sdn_simulator.py      # 主要的衛星拓撲模擬器
├── satellite_sdn_controller.py     # Ryu SDN 控制器
├── traffic_simulator.py            # 流量模擬器
├── run_satellite_simulation.py     # 主啟動腳本
├── leo_config.yaml                 # 衛星網路配置檔案
└── SATELLITE_SDN_README.md         # 這個文檔
```

## 🛠 安裝與設定

### 系統需求
- Ubuntu 18.04+ 或其他 Linux 發行版
- Python 3.7+
- Mininet
- Ryu 控制器
- Open vSwitch

### 安裝步驟

1. **安裝 Mininet**
```bash
sudo apt-get update
sudo apt-get install mininet
```

2. **安裝 Ryu 控制器**
```bash
pip install ryu
```

3. **安裝 Python 依賴**
```bash
pip install pyyaml numpy matplotlib
```

4. **驗證安裝**
```bash
# 測試 Mininet
sudo mn --test pingall

# 測試 Ryu
ryu-manager --version
```

### 配置修改

修改 `leo_config.yaml` 中的控制器 IP 地址：

```yaml
controller:
  ip: "127.0.0.1"  # 改為您的控制器 IP
  port: 6653
```

## 🎮 使用方法

### 方法 1: 完整啟動 (推薦)

```bash
# 啟動完整模擬環境
sudo python run_satellite_simulation.py

# 帶演示的啟動
sudo python run_satellite_simulation.py --demo

# 詳細模式
sudo python run_satellite_simulation.py --verbose
```

### 方法 2: 分步啟動

**終端 1 - 啟動控制器**
```bash
python run_satellite_simulation.py --controller-only
```

**終端 2 - 啟動拓撲**
```bash
sudo python run_satellite_simulation.py --topology-only
```

### 方法 3: 手動啟動

**步驟 1: 啟動 Ryu 控制器**
```bash
ryu-manager satellite_sdn_controller.py --verbose
```

**步驟 2: 啟動拓撲模擬器**
```bash
sudo python satellite_sdn_simulator.py
```

## 🎯 操作指南

### 基本命令

進入 Mininet CLI 後，可使用以下命令：

```bash
# 基本 Mininet 命令
mininet> pingall                    # 測試所有主機連通性
mininet> iperf gs_beijing gs_london # 測試兩個地面站間的吞吐量
mininet> h1 ping h2                 # 特定主機間 ping 測試

# 衛星模擬命令
mininet> simulate                   # 顯示當前衛星狀態
mininet> add_satellite SAT4         # 動態添加衛星
mininet> remove_satellite SAT2      # 移除衛星
mininet> status                     # 顯示系統狀態

# 流量測試命令
mininet> traffic                    # 進入流量測試模式
mininet> demo                       # 執行完整演示
```

### 流量測試模式

進入流量測試模式後：

```bash
# 列出可用的流量模式
sim> list

# 執行特定流量模式
sim> run basic_connectivity        # 基本連通性測試
sim> run throughput_test           # 吞吐量測試
sim> run video_streaming           # 視頻流測試

# 測試衛星切換
sim> handover                      # 測試衛星切換性能
sim> failure                       # 測試故障恢復

# 查看結果
sim> results                       # 顯示測試結果摘要
sim> plot                          # 繪製性能圖表 (需要 matplotlib)
```

## 📊 監控與分析

### 系統狀態監控

```bash
# 查看衛星位置和連接狀態
mininet> simulate

# 查看系統整體狀態
mininet> status
```

### 性能指標

系統會自動收集以下性能指標：
- **連通性**: 所有主機間的連通成功率
- **吞吐量**: 各連接的數據傳輸速率
- **延遲**: 端到端延遲時間
- **切換性能**: 衛星切換時的中斷時間

### 結果視覺化

```bash
# 在流量測試模式中
sim> plot
```

這會生成包含以下圖表的文件：
1. 網路吞吐量隨時間變化
2. 網路連通性隨時間變化  
3. 網路延遲隨時間變化
4. 衛星切換成功率

## 🔧 配置說明

### leo_config.yaml 主要參數

```yaml
# 網路基本參數
network:
  simulation_duration: 3600    # 模擬持續時間（秒）
  update_interval: 5           # 更新間隔（秒）

# 衛星參數
satellites:
  count: 12                    # 衛星數量
  altitude: 550                # 軌道高度（km）
  inclination: 53              # 軌道倾角（度）

# 地面站參數  
ground_stations:
  count: 6                     # 地面站數量
  min_elevation_angle: 10      # 最小仰角（度）
  
# 控制器參數
controller:
  ip: "127.0.0.1"             # 控制器 IP
  port: 6653                   # 控制器端口
```

## 📋 測試腳本

### 自動化測試範例

```python
# 在 Python 中使用
from satellite_sdn_simulator import DynamicSatelliteTopology
from traffic_simulator import SatelliteTrafficSimulator

# 創建拓撲
topology = DynamicSatelliteTopology()
topology.start_simulation()

# 創建流量模擬器
traffic_sim = SatelliteTrafficSimulator(topology)
traffic_sim.start_simulation()

# 執行測試
result = traffic_sim.run_traffic_pattern("throughput_test")
handover_result = traffic_sim.test_satellite_handover()

# 查看結果
traffic_sim.show_results()
```

## 🐛 故障排除

### 常見問題

1. **控制器連接失敗**
   ```bash
   # 檢查端口是否被佔用
   sudo netstat -tlnp | grep :6653
   
   # 修改配置文件中的 IP 地址
   # 確保控制器 IP 可從 Mininet 訪問
   ```

2. **權限問題**
   ```bash
   # 確保以 sudo 權限運行 Mininet 部分
   sudo python run_satellite_simulation.py
   ```

3. **Python 依賴問題**
   ```bash
   # 安裝缺失的依賴
   pip install pyyaml numpy matplotlib
   ```

4. **Open vSwitch 問題**
   ```bash
   # 重啟 OVS 服務
   sudo service openvswitch-switch restart
   ```

### 調試模式

```bash
# 啟用詳細日誌
python run_satellite_simulation.py --verbose

# 檢查 Ryu 日誌
tail -f ryu.log
```

## 🎯 進階使用

### 自定義衛星軌道

修改 `SatelliteOrbitSimulator` 類中的軌道計算方法：

```python
def get_satellite_position(self, satellite_id: str, time_offset: float):
    # 實現更複雜的軌道模型
    # 例如：考慮地球自轉、軌道攝動等
```

### 自定義路由算法

在 `SatelliteSDNController` 中添加新的路由算法：

```python
def _custom_routing_algorithm(self, src_dpid, dst_dpid):
    # 實現自定義路由邏輯
    # 例如：基於 QoS 需求的路由選擇
```

### 自定義流量模式

在 `SatelliteTrafficSimulator` 中添加新的流量模式：

```python
def _run_custom_test(self, pattern: TrafficPattern):
    # 實現自定義流量測試
    # 例如：物聯網流量、語音通話模擬等
```

## 📈 實驗建議

### 基礎實驗

1. **靜態連通性測試**: 測試不同地面站間的基本連通性
2. **動態切換測試**: 觀察衛星切換對連通性的影響
3. **吞吐量分析**: 比較不同路由算法的性能

### 進階實驗

1. **故障恢復能力**: 模擬多衛星同時故障的情況
2. **負載平衡效果**: 測試高負載下的流量分配
3. **QoS 保證**: 測試不同服務類型的性能保證

### 研究方向

1. **智能路由**: 基於機器學習的動態路由選擇
2. **資源分配**: 衛星資源的最優分配策略  
3. **安全性**: SDN 環境下的衛星網路安全機制

## 📝 許可證

本專案僅供學術研究和教育用途。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個模擬器。

---

**注意**: 這是一個模擬環境，用於研究和教育目的。實際的衛星網路部署需要考慮更多複雜的物理因素和工程實現細節。 