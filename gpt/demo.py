#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCAP模擬器演示腳本
展示如何使用各個組件來分析和生成網路封包
"""

import os
import sys
from datetime import datetime
from scapy.all import *
from pcap_simulator import PCAPSimulator, PCAPAnalyzer, SyntheticPacketGenerator

def create_sample_pcap():
    """創建一個示例PCAP檔案用於測試"""
    print("創建示例PCAP檔案...")
    
    packets = []
    
    # 創建各種類型的封包
    # 1. HTTP流量
    for i in range(5):
        pkt = IP(src=f"192.168.1.{10+i}", dst="8.8.8.8") / TCP(sport=32768+i, dport=80, flags="PA") / Raw(load=b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
        packets.append(pkt)
    
    # 2. DNS查詢
    for i in range(3):
        pkt = IP(src=f"192.168.1.{20+i}", dst="8.8.8.8") / UDP(sport=32800+i, dport=53) / Raw(load=b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01")
        packets.append(pkt)
    
    # 3. ICMP Ping
    for i in range(4):
        pkt = IP(src=f"192.168.1.{30+i}", dst=f"8.8.{i+1}.{i+1}") / ICMP(type=8, code=0) / Raw(load=b"A" * 64)
        packets.append(pkt)
    
    # 4. SSH流量
    for i in range(6):
        pkt = IP(src=f"192.168.1.{40+i}", dst=f"10.0.0.{i+1}") / TCP(sport=32850+i, dport=22, flags="PA") / Raw(load=b"SSH-2.0-OpenSSH_8.0")
        packets.append(pkt)
    
    # 保存到PCAP檔案
    sample_file = "sample_traffic.pcap"
    wrpcap(sample_file, packets)
    print(f"示例PCAP檔案已創建: {sample_file} ({len(packets)} 個封包)")
    
    return sample_file

def demo_basic_analysis():
    """演示基本的PCAP分析功能"""
    print("\n=== 演示1: 基本PCAP分析 ===")
    
    # 創建示例檔案
    sample_file = create_sample_pcap()
    
    # 創建分析器
    analyzer = PCAPAnalyzer()
    
    # 載入和分析
    if analyzer.load_pcap(sample_file):
        stats = analyzer.analyze_packets()
        
        print(f"總封包數: {stats['total_packets']}")
        print(f"協議分佈: {stats['protocols']}")
        print(f"唯一源IP數: {len(stats['src_ips'])}")
        print(f"唯一目標IP數: {len(stats['dst_ips'])}")
        print(f"平均封包大小: {sum(stats['packet_sizes'])/len(stats['packet_sizes']):.2f} bytes")
        
        # 顯示前5個封包摘要
        summaries = analyzer.extract_packet_summaries(5)
        print("\n前5個封包摘要:")
        for i, summary in enumerate(summaries, 1):
            print(f"{i}. {summary}")
    
    return sample_file

def demo_synthetic_generation():
    """演示合成封包生成"""
    print("\n=== 演示2: 合成封包生成 ===")
    
    generator = SyntheticPacketGenerator()
    
    # 生成不同類型的流量
    print("生成Web瀏覽流量...")
    web_template = {
        'protocol': 'TCP',
        'src_ip': '192.168.1.100',
        'dst_ip': '216.58.200.142',  # Google
        'src_port': 45678,
        'dst_port': 80,
        'flags': 'PA',
        'payload_size': 512
    }
    web_packets = generator.generate_from_template(web_template, 3)
    print(f"生成了 {len(web_packets)} 個Web流量封包")
    
    print("生成DNS查詢流量...")
    dns_template = {
        'protocol': 'UDP',
        'src_ip': '192.168.1.100',
        'dst_ip': '8.8.8.8',
        'src_port': 54321,
        'dst_port': 53,
        'payload_size': 64
    }
    dns_packets = generator.generate_from_template(dns_template, 2)
    print(f"生成了 {len(dns_packets)} 個DNS查詢封包")
    
    print("生成真實流量模式...")
    realistic_packets = generator.generate_realistic_traffic({}, duration=5)
    print(f"生成了 {len(realistic_packets)} 個真實流量封包")
    
    # 保存所有生成的封包
    synthetic_file = "synthetic_demo.pcap"
    generator.save_to_pcap(synthetic_file)
    print(f"所有合成封包已保存到: {synthetic_file}")
    
    return synthetic_file

def demo_full_pipeline():
    """演示完整的模擬流程"""
    print("\n=== 演示3: 完整模擬流程 ===")
    
    # 創建示例PCAP檔案
    sample_file = create_sample_pcap()
    
    # 創建模擬器 (不使用OpenAI API)
    simulator = PCAPSimulator()
    
    # 運行完整流程
    results = simulator.run_full_pipeline(sample_file, "demo_output")
    
    print("流程完成! 生成的檔案:")
    for key, value in results.items():
        if key != "error":
            print(f"- {key}: {value}")

def demo_comparison():
    """演示原始vs合成流量的比較"""
    print("\n=== 演示4: 原始vs合成流量比較 ===")
    
    # 分析原始流量
    sample_file = create_sample_pcap()
    analyzer1 = PCAPAnalyzer()
    analyzer1.load_pcap(sample_file)
    original_stats = analyzer1.analyze_packets()
    
    # 分析合成流量
    synthetic_file = "synthetic_demo.pcap"
    if os.path.exists(synthetic_file):
        analyzer2 = PCAPAnalyzer()
        analyzer2.load_pcap(synthetic_file)
        synthetic_stats = analyzer2.analyze_packets()
        
        print("原始流量統計:")
        print(f"  封包數: {original_stats['total_packets']}")
        print(f"  協議: {original_stats['protocols']}")
        print(f"  平均大小: {sum(original_stats['packet_sizes'])/len(original_stats['packet_sizes']):.2f}")
        
        print("\n合成流量統計:")
        print(f"  封包數: {synthetic_stats['total_packets']}")
        print(f"  協議: {synthetic_stats['protocols']}")
        print(f"  平均大小: {sum(synthetic_stats['packet_sizes'])/len(synthetic_stats['packet_sizes']):.2f}")

def interactive_demo():
    """互動式演示選單"""
    print("PCAP模擬器演示程式")
    print("=" * 30)
    
    while True:
        print("\n請選擇演示:")
        print("1. 基本PCAP分析")
        print("2. 合成封包生成")
        print("3. 完整模擬流程")
        print("4. 原始vs合成流量比較")
        print("5. 運行所有演示")
        print("0. 退出")
        
        choice = input("\n請輸入選擇 (0-5): ").strip()
        
        if choice == "1":
            demo_basic_analysis()
        elif choice == "2":
            demo_synthetic_generation()
        elif choice == "3":
            demo_full_pipeline()
        elif choice == "4":
            demo_comparison()
        elif choice == "5":
            demo_basic_analysis()
            demo_synthetic_generation()
            demo_full_pipeline()
            demo_comparison()
        elif choice == "0":
            print("再見!")
            break
        else:
            print("無效選擇，請重試")
        
        input("\n按Enter鍵繼續...")

def main():
    """主函數"""
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # 自動運行所有演示
        print("自動運行所有演示...")
        demo_basic_analysis()
        demo_synthetic_generation()
        demo_full_pipeline()
        demo_comparison()
    else:
        # 互動式選單
        interactive_demo()

if __name__ == "__main__":
    main() 