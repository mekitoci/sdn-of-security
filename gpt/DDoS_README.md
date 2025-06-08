# DDoS攻擊PCAP生成器

一個專門用於生成各種類型DDoS攻擊流量的工具，整合OpenAI來增強攻擊特徵和多樣性。

## ⚠️ 重要聲明

**此工具僅供教育、研究和網路安全測試目的使用。請勿用於任何非法攻擊活動。**

## 🚀 功能特點

### 📦 支援的攻擊類型

1. **TCP SYN Flood** - 經典的TCP連接耗盡攻擊
2. **UDP Flood** - 大量UDP封包洪水攻擊
3. **ICMP Flood** - ICMP回聲請求洪水攻擊
4. **DNS放大攻擊** - 利用DNS服務器進行流量放大
5. **Slowloris攻擊** - 慢速HTTP連接攻擊
6. **Smurf攻擊** - ICMP廣播放大攻擊
7. **混合攻擊** - 多種攻擊類型組合
8. **AI增強攻擊** - 使用OpenAI生成智能攻擊策略

### 🤖 AI增強功能

- 使用OpenAI GPT模型分析攻擊策略
- 智能化的源IP生成模式
- 動態調整攻擊參數
- 多階段攻擊序列

### 📊 詳細統計

- 攻擊類型分析
- 目標統計
- 封包數量統計
- 自動生成分析報告

## 🛠️ 安裝和配置

### 安裝依賴

```bash
pip install scapy openai
```

### 設置OpenAI API Key (可選)

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 📖 使用方法

### 命令行使用

#### 基本語法
```bash
python ddos_generator.py -t <目標IP> [選項]
```

#### 常用範例

```bash
# 生成混合DDoS攻擊
python ddos_generator.py -t 192.168.1.100

# 生成SYN Flood攻擊
python ddos_generator.py -t 192.168.1.100 --attack-type syn --count 5000

# 生成高強度混合攻擊
python ddos_generator.py -t 192.168.1.100 --intensity extreme

# 使用AI增強攻擊
python ddos_generator.py -t 192.168.1.100 --attack-type ai --api-key your-key

# 指定輸出檔案
python ddos_generator.py -t 192.168.1.100 -o my_attack.pcap
```

#### 命令行參數

- `-t, --target`: 目標IP地址 (必需)
- `-o, --output`: 輸出PCAP檔案名 (預設: ddos_attack.pcap)
- `--attack-type`: 攻擊類型 (syn/udp/icmp/dns/slowloris/smurf/mixed/ai)
- `--intensity`: 攻擊強度 (low/medium/high/extreme)
- `--count`: 封包數量 (預設: 1000)
- `--api-key`: OpenAI API Key

### 互動式演示

```bash
# 運行互動式演示
python ddos_demo.py

# 快速測試
python ddos_demo.py --quick

# 自動運行所有演示
python ddos_demo.py --auto
```

### 程式化使用

```python
from ddos_generator import DDoSAttackGenerator

# 創建生成器
generator = DDoSAttackGenerator()

# 生成SYN Flood攻擊
packets = generator.generate_syn_flood("192.168.1.100", packet_count=1000)

# 生成混合攻擊
generator.generate_mixed_attack("192.168.1.100", intensity="high")

# 保存PCAP
generator.save_attack_pcap("my_attack.pcap")
```

## 🎯 攻擊類型詳解

### 1. TCP SYN Flood
```python
generator.generate_syn_flood(
    target_ip="192.168.1.100",
    target_port=80,
    packet_count=1000,
    source_randomize=True
)
```
- 目標: 耗盡服務器的TCP連接資源
- 特徵: 大量SYN請求，不完成三次握手

### 2. UDP Flood
```python
generator.generate_udp_flood(
    target_ip="192.168.1.100",
    target_port=53,
    packet_count=1000,
    payload_size=1024
)
```
- 目標: 消耗網路帶寬和處理能力
- 特徵: 大量隨機UDP封包

### 3. ICMP Flood
```python
generator.generate_icmp_flood(
    target_ip="192.168.1.100",
    packet_count=1000
)
```
- 目標: Ping of Death，大量ICMP請求
- 特徵: 各種ICMP類型，大payload

### 4. DNS放大攻擊
```python
generator.generate_dns_amplification(
    target_ip="192.168.1.100",
    dns_servers=["8.8.8.8", "1.1.1.1"],
    packet_count=500
)
```
- 目標: 利用DNS服務器放大攻擊流量
- 特徵: 偽造源IP，ANY查詢

### 5. Slowloris攻擊
```python
generator.generate_slowloris_attack(
    target_ip="192.168.1.100",
    target_port=80,
    connection_count=100
)
```
- 目標: 長時間占用HTTP連接
- 特徵: 不完整的HTTP請求

### 6. AI增強攻擊
```python
generator.generate_ai_enhanced_attack(
    target_ip="192.168.1.100",
    attack_type="mixed"
)
```
- 使用GPT分析最佳攻擊策略
- 智能調整攻擊參數
- 多階段攻擊序列

## 📊 輸出文件

生成的文件包括：

```
ddos_attack.pcap          # 主要攻擊流量檔案
ddos_attack_stats.json    # 攻擊統計分析
```

### 統計文件格式
```json
{
  "total_packets": 5000,
  "attack_types": {
    "TCP_attacks": 3000,
    "UDP_attacks": 1500,
    "ICMP_attacks": 500
  },
  "target_analysis": {
    "192.168.1.100": 5000
  },
  "timing_info": {
    "generation_time": "2024-01-01T12:00:00",
    "filename": "ddos_attack.pcap"
  }
}
```

## 🔧 進階配置

### 自定義攻擊模式

```python
# 創建自定義SYN攻擊
generator = DDoSAttackGenerator()

# 針對多個端口
for port in [80, 443, 8080, 3000]:
    generator.generate_syn_flood("target.com", port, 1000)

# 時間分散攻擊
import time
for i in range(10):
    generator.generate_udp_flood("target.com", 53, 100)
    time.sleep(1)  # 每秒發送一波

generator.save_attack_pcap("distributed_attack.pcap")
```

### AI策略自定義

```python
generator = DDoSAttackGenerator(api_key="your-key")

# 自定義AI提示
custom_prompt = """
針對Web服務器的專門攻擊策略：
1. 重點攻擊HTTP/HTTPS端口
2. 模擬來自不同地理位置的攻擊
3. 包含慢速攻擊和洪水攻擊的組合
"""

# 這裡可以擴展AI功能
```

## 🛡️ 防護建議

生成的攻擊PCAP可用於：

1. **防火牆測試** - 測試DDoS防護規則
2. **IDS/IPS測試** - 驗證入侵檢測系統
3. **流量分析** - 研究攻擊模式
4. **員工培訓** - 網路安全意識培訓

### 常見防護措施

- **流量限制** - 設置連接數和帶寬限制
- **源IP驗證** - 過濾偽造IP地址
- **速率限制** - 限制每IP的請求頻率
- **黑洞路由** - 將攻擊流量路由到空路由

## 🚨 法律聲明

1. **僅限授權測試** - 只能在自己的網路或獲得明確授權的環境中使用
2. **教育用途** - 用於學習網路安全和攻擊防護
3. **責任免除** - 使用者自行承擔使用責任
4. **合規使用** - 遵守當地法律法規

## 📝 使用範例

### 基礎測試
```bash
# 小規模測試
python ddos_generator.py -t 127.0.0.1 --count 100

# 查看生成的封包
tcpdump -r ddos_attack.pcap | head -20
```

### 性能測試
```bash
# 大規模攻擊模擬
python ddos_generator.py -t 192.168.1.100 --intensity extreme

# 使用Wireshark分析
wireshark ddos_attack.pcap
```

### 研究分析
```bash
# 生成不同類型攻擊進行對比
python ddos_generator.py -t target.com --attack-type syn -o syn_attack.pcap
python ddos_generator.py -t target.com --attack-type udp -o udp_attack.pcap
python ddos_generator.py -t target.com --attack-type icmp -o icmp_attack.pcap
```

## 🤝 貢獻

歡迎提交Issues和Pull Requests來改善這個工具。

## 📄 授權

此專案採用MIT授權。請注意責任使用。

---

**記住：強大的工具需要負責任的使用。請將此工具用於正當的安全研究和防護測試。** 