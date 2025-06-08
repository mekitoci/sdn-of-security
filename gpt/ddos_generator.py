#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDoS攻擊PCAP生成器
專門用於生成各種類型的DDoS攻擊流量，並使用OpenAI增強攻擊特徵
"""

import os
import sys
import json
import time
import random
import threading
from datetime import datetime
from typing import List, Dict, Any
import argparse

try:
    from scapy.all import *
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.layers.l2 import Ether
except ImportError:
    print("請安裝scapy: pip install scapy")
    sys.exit(1)

try:
    import openai
except ImportError:
    print("請安裝openai: pip install openai")
    sys.exit(1)

class DDoSAttackGenerator:
    """DDoS攻擊生成器"""
    
    def __init__(self, openai_api_key=None):
        self.attack_packets = []
        self.attack_stats = {}
        
        # 初始化OpenAI
        if openai_api_key:
            openai.api_key = openai_api_key
        else:
            openai.api_key = os.getenv('OPENAI_API_KEY')
        
        self.ai_available = bool(openai.api_key)
        if not self.ai_available:
            print("⚠️  OpenAI API不可用，將使用基本攻擊模式")
    
    def generate_syn_flood(self, target_ip: str, target_port: int = 80, packet_count: int = 1000, 
                          source_randomize: bool = True) -> List:
        """生成TCP SYN Flood攻擊"""
        print(f"🚀 生成SYN Flood攻擊: {target_ip}:{target_port} ({packet_count} 個封包)")
        
        packets = []
        for i in range(packet_count):
            # 隨機源IP或固定源IP
            if source_randomize:
                src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            else:
                src_ip = f"192.168.1.{random.randint(1,254)}"
            
            # 隨機源端口
            src_port = random.randint(1024, 65535)
            
            # 隨機序列號
            seq_num = random.randint(1000000, 4000000000)
            
            # 創建SYN包
            packet = IP(src=src_ip, dst=target_ip) / TCP(
                sport=src_port,
                dport=target_port,
                flags="S",  # SYN flag
                seq=seq_num,
                window=random.randint(1024, 65535)
            )
            
            packets.append(packet)
        
        self.attack_packets.extend(packets)
        print(f"✅ SYN Flood攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_udp_flood(self, target_ip: str, target_port: int = 53, packet_count: int = 1000,
                          payload_size: int = 1024) -> List:
        """生成UDP Flood攻擊"""
        print(f"🚀 生成UDP Flood攻擊: {target_ip}:{target_port} ({packet_count} 個封包)")
        
        packets = []
        for i in range(packet_count):
            # 隨機源IP
            src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            src_port = random.randint(1024, 65535)
            
            # 隨機payload
            payload = os.urandom(payload_size)
            
            packet = IP(src=src_ip, dst=target_ip) / UDP(
                sport=src_port,
                dport=target_port
            ) / Raw(load=payload)
            
            packets.append(packet)
        
        self.attack_packets.extend(packets)
        print(f"✅ UDP Flood攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_icmp_flood(self, target_ip: str, packet_count: int = 1000) -> List:
        """生成ICMP Flood攻擊 (Ping of Death / ICMP Flood)"""
        print(f"🚀 生成ICMP Flood攻擊: {target_ip} ({packet_count} 個封包)")
        
        packets = []
        for i in range(packet_count):
            # 隨機源IP
            src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
            # 不同類型的ICMP攻擊
            icmp_types = [
                (8, 0),   # Echo Request (Ping)
                (13, 0),  # Timestamp Request
                (15, 0),  # Information Request
                (17, 0),  # Address Mask Request
            ]
            
            icmp_type, icmp_code = random.choice(icmp_types)
            
            # 大payload用於Ping of Death
            payload_size = random.randint(64, 65507)  # 最大UDP payload
            payload = b"A" * payload_size
            
            packet = IP(src=src_ip, dst=target_ip) / ICMP(
                type=icmp_type,
                code=icmp_code
            ) / Raw(load=payload)
            
            packets.append(packet)
        
        self.attack_packets.extend(packets)
        print(f"✅ ICMP Flood攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_dns_amplification(self, target_ip: str, dns_servers: List[str] = None, 
                                 packet_count: int = 500) -> List:
        """生成DNS放大攻擊"""
        if not dns_servers:
            dns_servers = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "208.67.222.222"]
        
        print(f"🚀 生成DNS放大攻擊: {target_ip} ({packet_count} 個封包)")
        
        packets = []
        
        # DNS查詢域名（用於放大效果）
        amplification_domains = [
            "isc.org",
            "ripe.net", 
            "google.com",
            "cloudflare.com",
            "any.example.com"
        ]
        
        for i in range(packet_count):
            dns_server = random.choice(dns_servers)
            domain = random.choice(amplification_domains)
            
            # 偽造源IP為目標IP (source spoofing)
            packet = IP(src=target_ip, dst=dns_server) / UDP(
                sport=random.randint(1024, 65535),
                dport=53
            ) / DNS(
                id=random.randint(1, 65535),
                qr=0,  # Query
                opcode=0,
                rd=1,  # Recursion Desired
                qd=DNSQR(qname=domain, qtype="ANY")  # ANY查詢用於放大
            )
            
            packets.append(packet)
        
        self.attack_packets.extend(packets)
        print(f"✅ DNS放大攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_slowloris_attack(self, target_ip: str, target_port: int = 80, 
                                connection_count: int = 100) -> List:
        """生成Slowloris慢速攻擊"""
        print(f"🚀 生成Slowloris攻擊: {target_ip}:{target_port} ({connection_count} 個連接)")
        
        packets = []
        
        for i in range(connection_count):
            src_ip = f"192.168.{random.randint(1,255)}.{random.randint(1,254)}"
            src_port = random.randint(1024, 65535)
            
            # TCP三次握手 - SYN
            syn_packet = IP(src=src_ip, dst=target_ip) / TCP(
                sport=src_port,
                dport=target_port,
                flags="S",
                seq=1000 + i
            )
            packets.append(syn_packet)
            
            # TCP三次握手 - ACK (假設SYN-ACK收到)
            ack_packet = IP(src=src_ip, dst=target_ip) / TCP(
                sport=src_port,
                dport=target_port,
                flags="A",
                seq=1001 + i,
                ack=2000 + i
            )
            packets.append(ack_packet)
            
            # 不完整的HTTP請求
            http_partial = IP(src=src_ip, dst=target_ip) / TCP(
                sport=src_port,
                dport=target_port,
                flags="PA",
                seq=1001 + i,
                ack=2000 + i
            ) / Raw(load=b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\nUser-Agent: Mozilla/5.0\r\n")
            
            packets.append(http_partial)
        
        self.attack_packets.extend(packets)
        print(f"✅ Slowloris攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_smurf_attack(self, target_ip: str, broadcast_networks: List[str] = None,
                            packet_count: int = 200) -> List:
        """生成Smurf攻擊 (ICMP廣播放大)"""
        if not broadcast_networks:
            broadcast_networks = [
                "192.168.1.255",
                "192.168.0.255", 
                "10.0.0.255",
                "172.16.0.255"
            ]
        
        print(f"🚀 生成Smurf攻擊: {target_ip} ({packet_count} 個封包)")
        
        packets = []
        
        for i in range(packet_count):
            broadcast_ip = random.choice(broadcast_networks)
            
            # 偽造源IP為目標，發送到廣播地址
            packet = IP(src=target_ip, dst=broadcast_ip) / ICMP(
                type=8,  # Echo Request
                code=0
            ) / Raw(load=b"A" * random.randint(32, 1024))
            
            packets.append(packet)
        
        self.attack_packets.extend(packets)
        print(f"✅ Smurf攻擊生成完成: {len(packets)} 個封包")
        return packets
    
    def generate_ai_enhanced_attack(self, target_ip: str, attack_type: str = "mixed") -> List:
        """使用AI生成增強版攻擊"""
        if not self.ai_available:
            print("❌ OpenAI API不可用，無法生成AI增強攻擊")
            return []
        
        print(f"🤖 使用AI生成增強版{attack_type}攻擊...")
        
        # 向AI詢問攻擊策略
        prompt = f"""
作為網路安全研究專家，請為針對IP {target_ip} 的DDoS攻擊提供策略建議。
攻擊類型: {attack_type}

請提供以下資訊:
1. 推薦的源IP範圍和模式
2. 最佳的攻擊時間間隔
3. 封包大小建議
4. 攻擊變化模式
5. 特殊的攻擊技巧

請以JSON格式回應:
{{
  "source_ip_pattern": "描述源IP生成模式",
  "timing_strategy": "攻擊時間策略",
  "packet_sizes": [最小值, 最大值],
  "attack_phases": ["階段1描述", "階段2描述"],
  "special_techniques": ["技巧1", "技巧2"]
}}
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_strategy = response.choices[0].message.content.strip()
            print(f"🧠 AI策略: {ai_strategy}")
            
            # 根據AI建議生成攻擊
            return self._generate_from_ai_strategy(target_ip, ai_strategy)
            
        except Exception as e:
            print(f"❌ AI生成失敗: {e}")
            # 回退到基本攻擊
            return self.generate_mixed_attack(target_ip)
    
    def _generate_from_ai_strategy(self, target_ip: str, strategy: str) -> List:
        """根據AI策略生成攻擊"""
        packets = []
        
        # 解析AI策略並生成相應攻擊
        # 這裡可以根據AI的回應來調整攻擊參數
        
        # 多階段攻擊
        print("📈 執行多階段AI增強攻擊...")
        
        # 階段1: 快速SYN flood
        packets.extend(self.generate_syn_flood(target_ip, 80, 500, True))
        
        # 階段2: UDP flood
        packets.extend(self.generate_udp_flood(target_ip, 53, 300, 1024))
        
        # 階段3: ICMP flood 
        packets.extend(self.generate_icmp_flood(target_ip, 200))
        
        print(f"🤖 AI增強攻擊完成: {len(packets)} 個封包")
        return packets
    
    def generate_mixed_attack(self, target_ip: str, intensity: str = "high") -> List:
        """生成混合攻擊"""
        print(f"💥 生成混合DDoS攻擊: {target_ip} (強度: {intensity})")
        
        packets = []
        
        # 根據強度調整封包數量
        multiplier = {"low": 0.5, "medium": 1.0, "high": 2.0, "extreme": 5.0}
        factor = multiplier.get(intensity, 1.0)
        
        # 多種攻擊類型組合
        packets.extend(self.generate_syn_flood(target_ip, 80, int(1000 * factor)))
        packets.extend(self.generate_syn_flood(target_ip, 443, int(800 * factor))) 
        packets.extend(self.generate_udp_flood(target_ip, 53, int(600 * factor)))
        packets.extend(self.generate_icmp_flood(target_ip, int(400 * factor)))
        packets.extend(self.generate_dns_amplification(target_ip, packet_count=int(300 * factor)))
        packets.extend(self.generate_slowloris_attack(target_ip, 80, int(100 * factor)))
        
        print(f"💥 混合攻擊完成: {len(packets)} 個封包")
        return packets
    
    def save_attack_pcap(self, filename: str, packets: List = None) -> bool:
        """保存攻擊PCAP檔案"""
        if packets is None:
            packets = self.attack_packets
        
        if not packets:
            print("❌ 沒有攻擊封包可保存")
            return False
        
        try:
            # 打亂封包順序，模擬真實攻擊
            random.shuffle(packets)
            
            wrpcap(filename, packets)
            print(f"💾 攻擊PCAP已保存: {filename} ({len(packets)} 個封包)")
            
            # 生成攻擊統計
            self._generate_attack_stats(packets, filename)
            return True
            
        except Exception as e:
            print(f"❌ 保存PCAP失敗: {e}")
            return False
    
    def _generate_attack_stats(self, packets: List, filename: str):
        """生成攻擊統計資訊"""
        stats = {
            "total_packets": len(packets),
            "attack_types": {},
            "target_analysis": {},
            "timing_info": {
                "generation_time": datetime.now().isoformat(),
                "filename": filename
            }
        }
        
        # 分析攻擊類型
        tcp_count = sum(1 for p in packets if p.haslayer(TCP))
        udp_count = sum(1 for p in packets if p.haslayer(UDP))
        icmp_count = sum(1 for p in packets if p.haslayer(ICMP))
        
        stats["attack_types"] = {
            "TCP_attacks": tcp_count,
            "UDP_attacks": udp_count, 
            "ICMP_attacks": icmp_count
        }
        
        # 分析目標
        targets = {}
        for packet in packets:
            if packet.haslayer(IP):
                dst = packet[IP].dst
                targets[dst] = targets.get(dst, 0) + 1
        
        stats["target_analysis"] = targets
        
        # 保存統計檔案
        stats_file = filename.replace('.pcap', '_stats.json')
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"📊 攻擊統計已保存: {stats_file}")
        except Exception as e:
            print(f"⚠️  統計保存失敗: {e}")
    
    def clear_packets(self):
        """清除已生成的封包"""
        self.attack_packets = []
        print("🗑️  封包緩存已清除")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="DDoS攻擊PCAP生成器")
    parser.add_argument("-t", "--target", required=True, help="目標IP地址")
    parser.add_argument("-o", "--output", default="ddos_attack.pcap", help="輸出PCAP檔案名")
    parser.add_argument("--attack-type", choices=["syn", "udp", "icmp", "dns", "slowloris", "smurf", "mixed", "ai"], 
                       default="mixed", help="攻擊類型")
    parser.add_argument("--intensity", choices=["low", "medium", "high", "extreme"], 
                       default="high", help="攻擊強度")
    parser.add_argument("--api-key", help="OpenAI API Key")
    parser.add_argument("--count", type=int, default=1000, help="封包數量")
    
    args = parser.parse_args()
    
    print("💀 DDoS攻擊PCAP生成器啟動")
    print("=" * 50)
    print(f"🎯 目標: {args.target}")
    print(f"⚔️  攻擊類型: {args.attack_type}")
    print(f"💪 強度: {args.intensity}")
    print(f"📦 輸出: {args.output}")
    print("=" * 50)
    
    # 創建生成器
    generator = DDoSAttackGenerator(args.api_key)
    
    # 根據攻擊類型生成
    if args.attack_type == "syn":
        generator.generate_syn_flood(args.target, packet_count=args.count)
    elif args.attack_type == "udp":
        generator.generate_udp_flood(args.target, packet_count=args.count)
    elif args.attack_type == "icmp":
        generator.generate_icmp_flood(args.target, packet_count=args.count)
    elif args.attack_type == "dns":
        generator.generate_dns_amplification(args.target, packet_count=args.count)
    elif args.attack_type == "slowloris":
        generator.generate_slowloris_attack(args.target, connection_count=args.count//3)
    elif args.attack_type == "smurf":
        generator.generate_smurf_attack(args.target, packet_count=args.count)
    elif args.attack_type == "ai":
        generator.generate_ai_enhanced_attack(args.target)
    else:  # mixed
        generator.generate_mixed_attack(args.target, args.intensity)
    
    # 保存攻擊PCAP
    if generator.save_attack_pcap(args.output):
        print("🎉 DDoS攻擊PCAP生成完成!")
        print(f"📁 檔案位置: {os.path.abspath(args.output)}")
        print("⚠️  注意: 此工具僅供教育和研究目的使用!")
    else:
        print("❌ 生成失敗!")

if __name__ == "__main__":
    main() 