#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
動態衛星 SDN 網路模擬器 - 主啟動腳本
整合衛星拓撲、控制器和流量模擬器
"""

import sys
import os
import time
import threading
import subprocess
import argparse
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite_sdn_simulator import DynamicSatelliteTopology, custom_cli_commands
from traffic_simulator import SatelliteTrafficSimulator, cli_interface
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class SatelliteSDNManager:
    """衛星 SDN 系統管理器"""
    
    def __init__(self, config_file='leo_config.yaml'):
        self.config_file = config_file
        self.topology = None
        self.traffic_simulator = None
        self.controller_process = None
        self.running = False
    
    def start_controller(self, controller_ip='192.168.1.101', controller_port=6653):
        """啟動 Ryu 控制器"""
        print("=== 啟動 Ryu 衛星 SDN 控制器 ===")
        
        # 檢查控制器文件是否存在
        controller_file = 'satellite_sdn_controller.py'
        if not os.path.exists(controller_file):
            print(f"錯誤: 找不到控制器文件 {controller_file}")
            return False
        
        try:
            # 啟動 Ryu 控制器
            cmd = [
                'ryu-manager',
                '--ofp-tcp-listen-port', str(controller_port),
                '--verbose',
                controller_file
            ]
            
            print(f"啟動命令: {' '.join(cmd)}")
            self.controller_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待控制器啟動
            time.sleep(3)
            
            if self.controller_process.poll() is None:
                print(f"Ryu 控制器已啟動 (PID: {self.controller_process.pid})")
                print(f"控制器監聽地址: {controller_ip}:{controller_port}")
                return True
            else:
                print("控制器啟動失敗")
                stdout, stderr = self.controller_process.communicate()
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
                
        except FileNotFoundError:
            print("錯誤: 找不到 ryu-manager 命令")
            print("請確認 Ryu 已正確安裝: pip install ryu")
            return False
        except Exception as e:
            print(f"啟動控制器時發生錯誤: {e}")
            return False
    
    def start_topology(self):
        """啟動動態衛星拓撲"""
        print("=== 啟動動態衛星拓撲 ===")
        
        try:
            # 創建拓撲
            self.topology = DynamicSatelliteTopology(self.config_file)
            
            # 啟動模擬
            self.topology.start_simulation()
            
            print("動態衛星拓撲已啟動")
            return True
            
        except Exception as e:
            print(f"啟動拓撲時發生錯誤: {e}")
            return False
    
    def start_traffic_simulator(self):
        """啟動流量模擬器"""
        print("=== 啟動流量模擬器 ===")
        
        if not self.topology:
            print("錯誤: 請先啟動拓撲")
            return False
        
        try:
            self.traffic_simulator = SatelliteTrafficSimulator(self.topology)
            self.traffic_simulator.start_simulation()
            
            print("流量模擬器已啟動")
            return True
            
        except Exception as e:
            print(f"啟動流量模擬器時發生錯誤: {e}")
            return False
    
    def start_full_simulation(self):
        """啟動完整模擬（控制器 + 拓撲 + 流量）"""
        print("=== 啟動完整衛星 SDN 模擬環境 ===")
        
        # 1. 啟動控制器
        if not self.start_controller():
            print("控制器啟動失敗，終止啟動流程")
            return False
        
        # 2. 啟動拓撲
        if not self.start_topology():
            print("拓撲啟動失敗，終止啟動流程")
            self.stop()
            return False
        
        # 3. 啟動流量模擬器
        if not self.start_traffic_simulator():
            print("流量模擬器啟動失敗，但拓撲仍可用")
        
        self.running = True
        print("\n=== 衛星 SDN 模擬環境已完全啟動 ===")
        print("您現在可以使用以下功能:")
        print("1. 基本 Mininet 命令 (pingall, iperf, etc.)")
        print("2. 衛星模擬命令 (simulate, add_satellite, remove_satellite)")
        print("3. 流量測試命令 (輸入 'traffic' 進入流量測試模式)")
        print("\n輸入 'help' 查看所有可用命令")
        
        return True
    
    def enter_cli(self):
        """進入交互式命令行界面"""
        if not self.topology:
            print("錯誤: 拓撲未啟動")
            return
        
        # 添加自定義命令
        custom_cli_commands(self.topology)
        
        # 添加流量測試命令
        def do_traffic(self, line):
            """進入流量測試模式"""
            if self.traffic_simulator:
                cli_interface(self.traffic_simulator)
            else:
                print("流量模擬器未啟動")
        
        def do_status(self, line):
            """顯示系統狀態"""
            status = self.topology.get_network_status()
            print(f"\n=== 系統狀態 ===")
            print(f"模擬時間: {status['simulation_time']:.1f}s")
            print(f"活躍衛星: {len(status['active_satellites'])}")
            print(f"地面站: {len(status['ground_stations'])}")
            print(f"活躍連接: {len(status['active_connections'])}")
            print()
        
        def do_demo(self, line):
            """執行演示腳本"""
            self._run_demo()
        
        # 綁定命令
        CLI.do_traffic = lambda self, line: do_traffic(self, line)
        CLI.do_status = lambda self, line: do_status(self, line)
        CLI.do_demo = lambda self, line: do_demo(self, line)
        
        # 啟動 CLI
        CLI(self.topology.net)
    
    def _run_demo(self):
        """運行演示腳本"""
        print("\n=== 啟動衛星網路演示 ===")
        
        # 顯示初始狀態
        status = self.topology.get_network_status()
        print(f"初始狀態: {len(status['active_satellites'])} 顆衛星，{len(status['active_connections'])} 個連接")
        
        # 測試基本連通性
        print("\n1. 測試基本連通性...")
        self.topology.net.pingAll()
        
        # 演示衛星動態加入
        print("\n2. 演示衛星動態加入...")
        self.topology.add_satellite("SAT4")
        time.sleep(2)
        
        status = self.topology.get_network_status()
        print(f"加入 SAT4 後: {len(status['active_satellites'])} 顆衛星")
        
        # 演示衛星離開
        print("\n3. 演示衛星離開...")
        self.topology.remove_satellite("SAT2")
        time.sleep(2)
        
        status = self.topology.get_network_status()
        print(f"移除 SAT2 後: {len(status['active_satellites'])} 顆衛星")
        
        # 測試連通性恢復
        print("\n4. 測試連通性恢復...")
        self.topology.net.pingAll()
        
        # 如果有流量模擬器，執行流量測試
        if self.traffic_simulator:
            print("\n5. 執行吞吐量測試...")
            self.traffic_simulator.run_traffic_pattern("throughput_test")
        
        print("\n=== 演示完成 ===")
    
    def stop(self):
        """停止所有組件"""
        print("\n=== 停止衛星 SDN 模擬環境 ===")
        
        # 停止流量模擬器
        if self.traffic_simulator:
            self.traffic_simulator.stop_simulation()
        
        # 停止拓撲
        if self.topology:
            self.topology.stop_simulation()
        
        # 停止控制器
        if self.controller_process:
            print("停止 Ryu 控制器...")
            self.controller_process.terminate()
            time.sleep(2)
            if self.controller_process.poll() is None:
                self.controller_process.kill()
            print("控制器已停止")
        
        self.running = False
        print("所有組件已停止")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='動態衛星 SDN 網路模擬器')
    parser.add_argument('--config', default='leo_config.yaml', 
                       help='配置文件路徑 (預設: leo_config.yaml)')
    parser.add_argument('--controller-only', action='store_true',
                       help='只啟動控制器')
    parser.add_argument('--topology-only', action='store_true',
                       help='只啟動拓撲 (假設控制器已運行)')
    parser.add_argument('--demo', action='store_true',
                       help='啟動後自動運行演示')
    parser.add_argument('--verbose', action='store_true',
                       help='詳細輸出模式')
    
    args = parser.parse_args()
    
    # 設置日誌級別
    if args.verbose:
        setLogLevel('debug')
    else:
        setLogLevel('info')
    
    print("=== 動態衛星 SDN 網路模擬器 ===")
    print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"配置文件: {args.config}")
    
    # 檢查配置文件
    if not os.path.exists(args.config):
        print(f"錯誤: 找不到配置文件 {args.config}")
        return 1
    
    # 創建管理器
    manager = SatelliteSDNManager(args.config)
    
    try:
        if args.controller_only:
            # 只啟動控制器
            if manager.start_controller():
                print("控制器已啟動，按 Ctrl+C 停止")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        
        elif args.topology_only:
            # 只啟動拓撲（假設控制器已運行）
            if manager.start_topology():
                if args.demo:
                    manager._run_demo()
                manager.enter_cli()
        
        else:
            # 啟動完整模擬
            if manager.start_full_simulation():
                if args.demo:
                    time.sleep(2)  # 等待系統穩定
                    manager._run_demo()
                manager.enter_cli()
    
    except KeyboardInterrupt:
        print("\n收到中斷信號")
    except Exception as e:
        print(f"運行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.stop()
    
    return 0


if __name__ == '__main__':
    sys.exit(main()) 