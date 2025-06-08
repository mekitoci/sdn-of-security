# PCAP模擬器 (PCAP Simulator)

一個強大的網路封包分析和生成工具，可以從真實的PCAP檔案中學習並生成合成的網路流量。支援OpenAI集成，可以使用AI來生成更智能的網路封包模式。

## 功能特點

### 🔍 PCAP分析
- 載入和分析PCAP檔案
- 提取網路流量統計資訊
- 分析協議分佈、IP地址、埠號使用情況
- 生成封包摘要和流量模式

### 🧠 AI增強生成
- 集成OpenAI GPT模型
- 從真實流量中學習生成模式
- 智能化的封包生成建議
- 可自定義的提示模板

### 📦 合成封包生成
- 基於模板的封包生成
- 真實流量模式模擬
- 支援多種協議 (TCP, UDP, ICMP)
- 可配置的流量特徵

### 📊 完整流程
- 端到端的分析和生成流程
- 自動化的報告生成
- 多種輸出格式支援
- 批次處理能力

## 安裝說明

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設置OpenAI API Key (可選)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. 檢查Scapy權限
在某些系統上，Scapy需要管理員權限來創建原始封包：
```bash
# macOS/Linux
sudo python3 pcap_simulator.py

# 或者設置cap權限 (Linux)
sudo setcap cap_net_raw=eip /usr/bin/python3
```

## 使用方法

### 基本使用

#### 1. 命令行模式
```bash
# 基本分析
python3 pcap_simulator.py input.pcap

# 指定輸出目錄
python3 pcap_simulator.py input.pcap -o my_output

# 使用OpenAI API
python3 pcap_simulator.py input.pcap --api-key your-key

# 指定生成時長
python3 pcap_simulator.py input.pcap --duration 60
```

#### 2. 演示模式
```bash
# 互動式演示
python3 demo.py

# 自動運行所有演示
python3 demo.py --auto
```

#### 3. 聊天機器人模式
```bash
# 命令行聊天
python3 openai.py

# Web界面
python3 openai.py --web
```

### 程式化使用

```python
from pcap_simulator import PCAPSimulator

# 創建模擬器
simulator = PCAPSimulator("your-openai-key")

# 運行完整流程
results = simulator.run_full_pipeline("input.pcap", "output_dir")

print("生成的檔案:", results)
```

### 單獨使用各組件

#### PCAP分析
```python
from pcap_simulator import PCAPAnalyzer

analyzer = PCAPAnalyzer()
analyzer.load_pcap("traffic.pcap")
stats = analyzer.analyze_packets()
summaries = analyzer.extract_packet_summaries(10)
```

#### 合成封包生成
```python
from pcap_simulator import SyntheticPacketGenerator

generator = SyntheticPacketGenerator()

# 根據模板生成
template = {
    'protocol': 'TCP',
    'src_ip': '192.168.1.100',
    'dst_ip': '8.8.8.8',
    'src_port': 12345,
    'dst_port': 80
}
packets = generator.generate_from_template(template, 10)

# 生成真實流量模式
realistic_packets = generator.generate_realistic_traffic({}, duration=60)

# 保存到PCAP
generator.save_to_pcap("synthetic.pcap")
```

#### AI封包生成
```python
from pcap_simulator import OpenAIPacketGenerator

ai_gen = OpenAIPacketGenerator("your-api-key")
ideas = ai_gen.generate_packet_ideas(training_data, count=5)
```

## 輸出說明

運行完整流程後，系統會在輸出目錄中生成以下檔案：

```
output/
├── analysis_stats.json      # 原始PCAP統計資訊
├── training_data.json       # 提取的訓練數據
├── ai_generated_ideas.txt   # AI生成的封包想法 (如果使用OpenAI)
├── synthetic_traffic.pcap   # 生成的合成流量
└── simulation_report.txt    # 完整報告
```

### 檔案說明

#### analysis_stats.json
包含原始PCAP檔案的詳細統計資訊：
- 總封包數
- 協議分佈
- IP地址使用情況
- 埠號統計
- 封包大小分佈
- 流量模式

#### training_data.json
結構化的訓練數據，包含：
- 元數據資訊
- 封包摘要列表
- 網路模式
- 提示模板

#### synthetic_traffic.pcap
生成的合成網路流量，可以用Wireshark等工具打開分析。

## 支援的協議

- **TCP**: HTTP, HTTPS, SSH, FTP等
- **UDP**: DNS, DHCP, SNMP等
- **ICMP**: Ping, 錯誤消息等
- 可擴展支援其他協議

## 流量模式

系統內建多種真實流量模式：

1. **Web瀏覽模式**: HTTP/HTTPS請求
2. **DNS查詢模式**: 域名解析
3. **Ping模式**: ICMP回聲請求
4. **SSH會話模式**: 遠程連接
5. **可自定義模式**: 根據需求添加

## API參考

### PCAPAnalyzer類

#### 主要方法
- `load_pcap(pcap_file)`: 載入PCAP檔案
- `analyze_packets()`: 分析封包統計
- `extract_packet_summaries(max_packets)`: 提取封包摘要

### SyntheticPacketGenerator類

#### 主要方法
- `generate_from_template(template, count)`: 根據模板生成
- `generate_realistic_traffic(patterns, duration)`: 生成真實流量
- `save_to_pcap(filename, packets)`: 保存到PCAP檔案

### OpenAIPacketGenerator類

#### 主要方法
- `generate_packet_ideas(training_data, count)`: 生成封包想法

### PCAPSimulator類

#### 主要方法
- `run_full_pipeline(input_pcap, output_dir)`: 運行完整流程

## 配置選項

### 環境變量
- `OPENAI_API_KEY`: OpenAI API密鑰
- `PYTHONPATH`: 如果需要，添加模組路徑

### 命令行參數
- `input_pcap`: 輸入PCAP檔案路徑
- `-o, --output`: 輸出目錄 (預設: output)
- `--api-key`: OpenAI API密鑰
- `--duration`: 生成流量持續時間 (預設: 30秒)

## 故障排除

### 常見問題

#### 1. Scapy權限錯誤
```bash
# 解決方案1: 使用sudo
sudo python3 pcap_simulator.py input.pcap

# 解決方案2: 設置權限 (Linux)
sudo setcap cap_net_raw=eip /usr/bin/python3
```

#### 2. OpenAI API錯誤
```bash
# 檢查API密鑰是否正確設置
echo $OPENAI_API_KEY

# 測試API連接
python3 -c "import openai; print(openai.api_key)"
```

#### 3. 模組導入錯誤
```bash
# 安裝缺失的依賴
pip install -r requirements.txt

# 檢查Python版本 (需要3.7+)
python3 --version
```

#### 4. PCAP檔案讀取錯誤
- 確保PCAP檔案未損壞
- 檢查檔案權限
- 嘗試用Wireshark打開檔案驗證

### 性能優化

#### 處理大型PCAP檔案
```python
# 限制分析的封包數量
analyzer.extract_packet_summaries(max_packets=1000)

# 分批處理
def process_large_pcap(filename, batch_size=10000):
    packets = rdpcap(filename)
    for i in range(0, len(packets), batch_size):
        batch = packets[i:i+batch_size]
        # 處理批次
```

## 示例使用場景

### 1. 網路安全研究
```python
# 分析惡意流量模式
simulator = PCAPSimulator()
results = simulator.run_full_pipeline("malware_traffic.pcap")

# 生成類似的測試流量
# 用於安全工具測試
```

### 2. 網路性能測試
```python
# 生成高負載流量
generator = SyntheticPacketGenerator()
stress_packets = generator.generate_realistic_traffic({}, duration=300)
generator.save_to_pcap("stress_test.pcap")
```

### 3. 教育和培訓
```python
# 創建教學用的網路流量
demo_packets = create_educational_traffic()
# 用於網路課程演示
```

## 貢獻指南

歡迎貢獻代碼！請遵循以下步驟：

1. Fork這個專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟Pull Request

## 授權

此專案採用MIT授權 - 詳見LICENSE檔案

## 聯絡資訊

如有問題或建議，請：
- 開啟GitHub Issue
- 發送郵件至: [your-email@example.com]

## 更新日誌

### v1.0.0 (2024-01-XX)
- 初始版本發布
- 支援基本PCAP分析
- 合成封包生成
- OpenAI集成
- 完整的演示系統

---

**注意**: 此工具僅供教育和研究目的使用。在生產環境中使用時請謹慎，並遵守相關法律法規。 