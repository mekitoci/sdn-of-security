#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDoS攻擊生成器演示腳本
快速體驗各種DDoS攻擊的生成
"""

import os
from ddos_generator import DDoSAttackGenerator

def demo_basic_attacks():
    """演示基本攻擊類型"""
    print("🔥 DDoS攻擊生成器演示")
    print("=" * 40)
    
    # 目標IP (使用測試IP)
    target_ip = "192.168.1.100"
    
    # 創建生成器
    generator = DDoSAttackGenerator()
    
    print(f"🎯 攻擊目標: {target_ip}")
    print("⚠️  注意: 這僅為教育演示，請勿用於實際攻擊!")
    print()
    
    # 1. SYN Flood攻擊
    print("1️⃣  生成SYN Flood攻擊...")
    generator.generate_syn_flood(target_ip, target_port=80, packet_count=500)
    
    # 2. UDP Flood攻擊
    print("\n2️⃣  生成UDP Flood攻擊...")
    generator.generate_udp_flood(target_ip, target_port=53, packet_count=300)
    
    # 3. ICMP Flood攻擊
    print("\n3️⃣  生成ICMP Flood攻擊...")
    generator.generate_icmp_flood(target_ip, packet_count=200)
    
    # 4. DNS放大攻擊
    print("\n4️⃣  生成DNS放大攻擊...")
    generator.generate_dns_amplification(target_ip, packet_count=150)
    
    # 5. Slowloris攻擊
    print("\n5️⃣  生成Slowloris攻擊...")
    generator.generate_slowloris_attack(target_ip, connection_count=50)
    
    # 保存演示PCAP
    output_file = "demo_ddos_attack.pcap"
    print(f"\n💾 保存攻擊PCAP到: {output_file}")
    generator.save_attack_pcap(output_file)
    
    return output_file

def demo_mixed_attack():
    """演示混合攻擊"""
    print("\n🔥 混合DDoS攻擊演示")
    print("=" * 40)
    
    target_ip = "10.0.0.50"
    generator = DDoSAttackGenerator()
    
    # 生成不同強度的混合攻擊
    print("📈 生成高強度混合攻擊...")
    generator.generate_mixed_attack(target_ip, intensity="high")
    
    output_file = "mixed_ddos_attack.pcap"
    generator.save_attack_pcap(output_file)
    
    return output_file

def demo_ai_enhanced_attack():
    """演示AI增強攻擊"""
    print("\n🤖 AI增強DDoS攻擊演示")
    print("=" * 40)
    
    target_ip = "172.16.0.10"
    
    # 檢查是否有OpenAI API Key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  未設置OPENAI_API_KEY，跳過AI增強演示")
        print("   設置方法: export OPENAI_API_KEY='your-key'")
        return None
    
    generator = DDoSAttackGenerator(api_key)
    
    print("🧠 使用AI生成智能攻擊策略...")
    generator.generate_ai_enhanced_attack(target_ip)
    
    output_file = "ai_enhanced_ddos.pcap"
    generator.save_attack_pcap(output_file)
    
    return output_file

def interactive_demo():
    """互動式演示"""
    print("💀 DDoS攻擊生成器 - 互動演示")
    print("=" * 50)
    
    while True:
        print("\n請選擇演示:")
        print("1. 基本DDoS攻擊類型")
        print("2. 混合攻擊")
        print("3. AI增強攻擊")
        print("4. 自定義攻擊")
        print("0. 退出")
        
        choice = input("\n請輸入選擇 (0-4): ").strip()
        
        if choice == "1":
            demo_basic_attacks()
        elif choice == "2":
            demo_mixed_attack()
        elif choice == "3":
            demo_ai_enhanced_attack()
        elif choice == "4":
            custom_attack_demo()
        elif choice == "0":
            print("👋 再見!")
            break
        else:
            print("❌ 無效選擇，請重試")
        
        input("\n按Enter鍵繼續...")

def custom_attack_demo():
    """自定義攻擊演示"""
    print("\n⚙️  自定義DDoS攻擊")
    print("=" * 30)
    
    try:
        target_ip = input("🎯 輸入目標IP (預設: 192.168.1.10): ").strip()
        if not target_ip:
            target_ip = "192.168.1.10"
        
        attack_type = input("⚔️  選擇攻擊類型 (syn/udp/icmp/mixed): ").strip().lower()
        if attack_type not in ["syn", "udp", "icmp", "mixed"]:
            attack_type = "mixed"
        
        packet_count = input("📦 封包數量 (預設: 1000): ").strip()
        if not packet_count.isdigit():
            packet_count = 1000
        else:
            packet_count = int(packet_count)
        
        output_file = input("💾 輸出檔案名 (預設: custom_attack.pcap): ").strip()
        if not output_file:
            output_file = "custom_attack.pcap"
        
        # 生成攻擊
        generator = DDoSAttackGenerator()
        
        if attack_type == "syn":
            generator.generate_syn_flood(target_ip, packet_count=packet_count)
        elif attack_type == "udp":
            generator.generate_udp_flood(target_ip, packet_count=packet_count)
        elif attack_type == "icmp":
            generator.generate_icmp_flood(target_ip, packet_count=packet_count)
        else:
            generator.generate_mixed_attack(target_ip, intensity="high")
        
        generator.save_attack_pcap(output_file)
        print(f"✅ 自定義攻擊生成完成: {output_file}")
        
    except KeyboardInterrupt:
        print("\n❌ 用戶中斷")
    except Exception as e:
        print(f"❌ 生成失敗: {e}")

def quick_test():
    """快速測試"""
    print("⚡ 快速測試DDoS生成器")
    print("生成小規模演示攻擊...")
    
    generator = DDoSAttackGenerator()
    target_ip = "127.0.0.1"  # 本地測試
    
    # 生成少量封包進行測試
    generator.generate_syn_flood(target_ip, packet_count=50)
    generator.generate_udp_flood(target_ip, packet_count=30)
    generator.generate_icmp_flood(target_ip, packet_count=20)
    
    output_file = "quick_test_ddos.pcap"
    generator.save_attack_pcap(output_file)
    
    print(f"✅ 快速測試完成: {output_file}")
    return output_file

def main():
    """主函數"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 快速測試模式
        quick_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # 自動演示模式
        print("🚀 自動運行所有演示...")
        demo_basic_attacks()
        demo_mixed_attack()
        demo_ai_enhanced_attack()
        print("\n🎉 所有演示完成!")
    else:
        # 互動模式
        interactive_demo()

if __name__ == "__main__":
    main() 