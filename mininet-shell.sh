# 基本用法（1個交換機，2個主機）
sudo python simple_topo.py

# 自定義拓撲（3個交換機，5個主機）
sudo python simple_topo.py --switches 3 --hosts 5

# 設置頻寬和延遲
sudo python simple_topo.py --bandwidth 10 --delay 5ms

# 連接到特定控制器
sudo python simple_topo.py --controller 192.168.1.100

# 保存拓撲圖
sudo python simple_topo.py --graph

# 完整示例
sudo python simple_topo.py --switches 3 --hosts 6 --bandwidth 10 --delay 5ms --controller 127.0.0.1 --port 6653 --graph