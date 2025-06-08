#!/bin/bash
# 清理Mininet殘留的網絡接口和設置

echo "清理Mininet環境..."

# 停止所有正在運行的Mininet進程
sudo killall -9 controller ovs-controller ovs-testcontroller ovs-vswitchd ofdatapath ofprotocol python3 python mininet 2>/dev/null

# 停止Open vSwitch服務
sudo service openvswitch-switch stop 2>/dev/null

# 刪除所有OVS網橋和接口
sudo ovs-vsctl --if-exists del-br br0
sudo ovs-vsctl --if-exists del-br br1
sudo ovs-vsctl --if-exists del-br br2
sudo ovs-vsctl --if-exists del-br br3

# 刪除所有OVS數據庫
sudo rm -rf /var/run/openvswitch/*
sudo rm -rf /var/log/openvswitch/*
sudo rm -f /etc/openvswitch/conf.db

# 重新初始化OVS數據庫
sudo ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema

# 重啟Open vSwitch服務
sudo service openvswitch-switch start

# 使用Mininet自帶的清理腳本
sudo mn -c

echo "Mininet環境清理完成！"
