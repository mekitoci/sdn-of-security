#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業網路拓撲模擬 - 20主機/5交換機環境
用於測試AI攻擊檢測和防禦機制

拓撲架構:
- 5個部門子網 (每個子網4台主機)
- 5台OpenFlow交換機
- 1個外部Ryu控制器
- 階層式網路結構 (核心-匯聚-接入)
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.topo import Topo
import time
import os
import argparse
import random
import subprocess
from threading import Thread

class EnterpriseNetworkTopo(Topo):
    """企業網路拓撲 - 5個部門，20台主機"""
    
    def build(self):
        # 創建核心層交換機
        core_switch = self.addSwitch('s1', protocols='OpenFlow13')
        
        # 創建匯聚層交換機
        aggregation_switches = []
        for i in range(2, 4):  # s2, s3
            switch = self.addSwitch(f's{i}', protocols='OpenFlow13')
            aggregation_switches.append(switch)
            # 連接到核心交換機
            self.addLink(core_switch, switch, bw=10, delay='2ms')
        
        # 創建接入層交換機和主機
        for i in range(4, 7):  # s4, s5, s6
            access_switch = self.addSwitch(f's{i}', protocols='OpenFlow13')
            
            # 連接到匯聚層
            # 負載平衡: 奇數交換機連到s2，偶數連到s3
            agg_switch = aggregation_switches[i % 2]
            self.addLink(agg_switch, access_switch, bw=10, delay='2ms')
            
            # 每個接入交換機連接4台主機 (總共 3*4 = 12 台主機)
            dept_id = i - 3  # 部門ID 1-3
            for j in range(1, 5):
                host_id = (i - 4) * 4 + j
                host = self.addHost(f'h{host_id}',
                                   ip=f'10.{dept_id}.0.{j}/24',
                                   mac=f'00:00:{dept_id:02d}:00:00:{j:02d}')
                # 連接主機到接入交換機
                self.addLink(access_switch, host, bw=1, delay='1ms')
        
        # 伺服器子網 (部門4) - 連接到s2
        server_switch = self.addSwitch('s7', protocols='OpenFlow13')
        self.addLink(aggregation_switches[0], server_switch, bw=10, delay='1ms')
        
        # 4台伺服器
        for j in range(1, 5):
            server = self.addHost(f'server{j}',
                               ip=f'10.4.0.{j}/24',
                               mac=f'00:00:04:00:00:{j:02d}')
            self.addLink(server_switch, server, bw=1, delay='1ms')
        
        # 外部網路子網 (部門5) - 連接到s3
        external_switch = self.addSwitch('s8', protocols='OpenFlow13')
        self.addLink(aggregation_switches[1], external_switch, bw=10, delay='5ms')
        
        # 4台外部主機 (可能的攻擊者)
        for j in range(1, 5):
            external = self.addHost(f'ext{j}',
                                 ip=f'10.5.0.{j}/24',
                                 mac=f'00:00:05:00:00:{j:02d}')
            self.addLink(external_switch, external, bw=1, delay='5ms')

def generate_background_traffic(net):
    """
    生成背景流量模擬正常企業網路活動
    基於CICIDS2018資料集的流量模式
    """
    info("*** 生成背景流量\n")
    
    # 獲取主機列表
    hosts = net.hosts
    internal_hosts = [h for h in hosts if not h.name.startswith('ext')]
    servers = [h for h in hosts if h.name.startswith('server')]
    
    # HTTP流量 - 隨機訪問伺服器
    for i in range(10):  # 創建10個HTTP會話
        src = random.choice(internal_hosts)
        dst = random.choice(servers)
        info(f"  HTTP流量: {src.name} -> {dst.name}\n")
        src.cmd(f"wget -q -O /dev/null {dst.IP()}:80 &")
    
    # SSH流量 - 管理連接
    for i in range(3):  # 創建3個SSH會話
        src = random.choice(internal_hosts)
        dst = random.choice(servers)
        info(f"  SSH流量: {src.name} -> {dst.name}\n")
        src.cmd(f"nc -zv {dst.IP()} 22 2>/dev/null &")
    
    # DNS查詢
    for i in range(5):  # 創建5個DNS查詢
        src = random.choice(internal_hosts)
        info(f"  DNS查詢: {src.name}\n")
        src.cmd(f"host -t A example.com &")
    
    # ICMP流量 (ping)
    for i in range(7):  # 創建7個ping會話
        src = random.choice(internal_hosts)
        dst = random.choice(internal_hosts + servers)
        while src == dst:
            dst = random.choice(internal_hosts + servers)
        info(f"  ICMP流量: {src.name} -> {dst.name}\n")
        src.cmd(f"ping -c 5 -i 2 {dst.IP()} > /dev/null &")

def run_attack(net, attack_type, src_name, dst_name, **kwargs):
    """
    從指定主機發起攻擊
    
    參數:
        net: Mininet網路對象
        attack_type: 攻擊類型 (syn_flood, http_flood, etc.)
        src_name: 攻擊源主機名稱
        dst_name: 攻擊目標主機名稱
        **kwargs: 攻擊參數
            - count: 發送的封包數量
            - interval: 封包發送間隔(秒)
            - port: 目標端口
            - pattern: 攻擊模式 ('standard', 'fixed_port', 'sequence', 'aggressive')
            - burst: 每次發送的封包數量
    """
    info(f"*** 開始攻擊: {attack_type} 從 {src_name} 到 {dst_name}\n")
    
    # 獲取源和目標主機
    src_host = net.get(src_name)
    dst_host = net.get(dst_name)
    
    if not src_host or not dst_host:
        info(f"錯誤: 找不到主機 {src_name} 或 {dst_name}\n")
        return
    
    # 根據攻擊類型執行不同攻擊
    if attack_type == 'syn_flood':
        # 獲取攻擊參數
        count = kwargs.get('count', 500)
        interval = kwargs.get('interval', 0.01)
        port = kwargs.get('port', 80)
        pattern = kwargs.get('pattern', 'aggressive')  # 預設使用更易被檢測的模式
        burst = kwargs.get('burst', 10)  # 預設每次發送10個封包
        
        # 構造SYN攻擊命令
        attack_cmd = f"python3 syn_flood.py "
        attack_cmd += f"--src {src_host.IP()} --dst {dst_host.IP()} "
        attack_cmd += f"--port {port} --count {count} --interval {interval} "
        attack_cmd += f"--pattern {pattern} --burst {burst}"
        
        info(f"  執行命令: {attack_cmd}\n")
        src_host.cmd(attack_cmd + " &")
        
        # 提示用戶攻擊已開始
        info(f"  SYN Flood攻擊已開始: {src_host.IP()} -> {dst_host.IP()}:{port}\n")
        info(f"  模式: {pattern}, 發送 {count} 個SYN封包，間隔 {interval} 秒\n")
        
    elif attack_type == 'syn_flood_multi':
        # 多源SYN Flood攻擊 - 從多個外部主機發起
        count = kwargs.get('count', 200)  # 每個主機發送的封包數
        interval = kwargs.get('interval', 0.01)
        port = kwargs.get('port', 80)
        pattern = kwargs.get('pattern', 'aggressive')
        
        # 獲取外部主機
        external_hosts = [h for h in net.hosts if h.name.startswith('ext')]
        
        # 從每個外部主機發起攻擊
        for ext_host in external_hosts:
            attack_cmd = f"python3 syn_flood.py "
            attack_cmd += f"--src {ext_host.IP()} --dst {dst_host.IP()} "
            attack_cmd += f"--port {port} --count {count} --interval {interval} "
            attack_cmd += f"--pattern {pattern}"
            
            info(f"  從 {ext_host.name} 執行: {attack_cmd}\n")
            ext_host.cmd(attack_cmd + " &")
        
        info(f"  多源 SYN Flood攻擊已開始: {len(external_hosts)} 個主機 -> {dst_host.IP()}:{port}\n")
        info(f"  每個主機發送 {count} 個封包，總共 {count * len(external_hosts)} 個\n")
        
    elif attack_type == 'port_scan':
        # 端口掃描攻擊 - 掃描目標主機的多個端口
        start_port = kwargs.get('start_port', 1)
        end_port = kwargs.get('end_port', 1024)
        
        # 使用nmap進行端口掃描
        scan_cmd = f"nmap -T4 -p {start_port}-{end_port} {dst_host.IP()} > /dev/null &"
        
        info(f"  執行端口掃描: {scan_cmd}\n")
        src_host.cmd(scan_cmd)
        
        info(f"  端口掃描已開始: {src_host.IP()} -> {dst_host.IP()} (端口 {start_port}-{end_port})\n")
        
    elif attack_type == 'http_flood':
        info("  HTTP Flood功能尚未實現\n")
    else:
        info(f"  未知攻擊類型: {attack_type}\n")

def start_network(controller_ip='127.0.0.1', controller_port=6653):
    """
    啟動模擬企業網路
    連接到指定的Ryu控制器
    """
    topo = EnterpriseNetworkTopo()
    
    info(f'*** 連接到控制器 {controller_ip}:{controller_port}\n')
    net = Mininet(topo=topo,
                 controller=RemoteController('c0', ip=controller_ip, port=controller_port),
                 switch=OVSKernelSwitch,
                 link=TCLink,
                 autoSetMacs=True)
    
    info('*** 啟動網路\n')
    net.start()
    
    # 等待控制器連接和初始化
    info('*** 等待控制器初始化 (10秒)...\n')
    time.sleep(10)
    
    # 生成背景流量
    generate_background_traffic(net)
    
    # 測試攻擊環境準備就緒
    info('*** 攻擊測試環境準備就緒. 使用 run_attack()函數發起攻擊\n')
    info('    範例:\n')
    info('    1. 從ext1發起標準SYN Flood攻擊到server1:\n')
    info('       run_attack(net, "syn_flood", "ext1", "server1", count=500, port=80, pattern="standard")\n')
    info('    2. 從ext1發起更易被檢測的攻擊模式:\n')
    info('       run_attack(net, "syn_flood", "ext1", "server1", count=500, port=80, pattern="aggressive")\n')
    info('    3. 從所有外部主機發起分散式攻擊:\n')
    info('       run_attack(net, "syn_flood_multi", "ext1", "server1", port=80)\n')
    
    # 預設執行一個更易被檢測的攻擊
    run_attack(net, "syn_flood", "ext1", "server1", count=500, port=80, pattern="aggressive")
    
    # 顯示網路信息
    info('*** 網路信息\n')
    net.pingAll(timeout=1)
    
    info('*** 網路已啟動，可輸入mininet命令...\n')
    CLI(net)
    
    # 在停止網路前執行清理
    # 殺掉所有背景進程
    for host in net.hosts:
        host.cmd("killall -9 ping wget host nc python3 2>/dev/null")
    
    # 清理
    info('*** 停止網路\n')
    net.stop()

if __name__ == '__main__':
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='企業網路拓撲模擬')
    parser.add_argument('--controller', dest='controller_ip', 
                       default='192.168.1.102', help='Ryu控制器IP (預設: 192.168.1.102)')
    parser.add_argument('--port', dest='controller_port', type=int,
                       default=6653, help='Ryu控制器端口 (預設: 6653)')
    args = parser.parse_args()
    
    # 檢查root權限
    if os.geteuid() != 0:
        info("請使用sudo運行此腳本\n")
        exit(1)
    
    # 設置日誌級別並啟動網路
    setLogLevel('info')
    start_network(args.controller_ip, args.controller_port)
