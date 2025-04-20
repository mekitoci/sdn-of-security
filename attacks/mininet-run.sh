sudo python3 mininet-test.py --test basic
: 只測試基本連通性

sudo python3 mininet-test.py --test synflood
: 測試 SYN flood 攻擊檢測

sudo python3 mininet-test.py --test traffic
: 測試不同類型的流量管理

sudo python3 mininet-test.py --test all
: 運行所有測試（默認）