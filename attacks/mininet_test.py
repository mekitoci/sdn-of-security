#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mininet測試腳本
用於測試Ryu控制器與Mininet的連接和功能
"""

import os
import time
import argparse
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

# 默認控制器設置
DEFAULT_CONTROLLER_IP = "192.168.1.102"
DEFAULT_CONTROLLER_PORT = 6653
DEFAULT_OF_VERSION = "OpenFlow13"  # 使用與您的控制器兼容的OpenFlow版本


class SingleSwitchTopo(Topo):
    """單交換機拓撲"""
    
    def build(self, n=2):
        # 添加一個交換機
        switch = self.addSwitch('s1')
        
        # 添加n個主機並連接到交換機
        for h in range(1, n + 1):
            host = self.addHost(f'h{h}', ip=f'10.0.0.{h}/24')
            self.addLink(host, switch)


class LinearTopo(Topo):
    """線性拓撲"""
    
    def build(self, n=3):
        # 添加n個交換機，形成一條線
        switches = []
        for s in range(1, n + 1):
            switch = self.addSwitch(f's{s}')
            switches.append(switch)
            
            # 為每個交換機添加一個主機
            host = self.addHost(f'h{s}', ip=f'10.0.0.{s}/24')
            self.addLink(host, switch)
        
        # 將交換機連接成一條線
        for i in range(len(switches) - 1):
            self.addLink(switches[i], switches[i + 1])


class TreeTopo(Topo):
    """樹狀拓撲"""
    
    def build(self, depth=2, fanout=2):
        # 添加根交換機
        root_switch = self.addSwitch('s1')
        
        # 遞歸構建樹
        self._build_tree(root_switch, depth, fanout, 1, 1)
    
    def _build_tree(self, parent, depth, fanout, switch_num, host_num):
        if depth == 0:
            return switch_num, host_num
        
        for _ in range(fanout):
            # 添加子交換機
            switch_num += 1
            child_switch = self.addSwitch(f's{switch_num}')
            self.addLink(parent, child_switch)
            
            # 為每個交換機添加一個主機
            host = self.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/24')
            self.addLink(child_switch, host)
            host_num += 1
            
            # 遞歸構建子樹
            switch_num, host_num = self._build_tree(child_switch, depth - 1, fanout, switch_num, host_num)
        
        return switch_num, host_num


def run_tests(net):
    """運行一系列網絡測試"""
    info("\n*** 運行基本連通性測試\n")
    
    # 測試基本連通性
    info("*** 測試所有主機間的連通性\n")
    net.pingAll(timeout=1)
    
    # 測試帶寬和延遲
    info("\n*** 測試兩個主機間的帶寬\n")
    h1, h2 = net.get('h1', 'h2')
    
    # 在h2上啟動iperf服務器
    h2.cmd('iperf -s -u &')
    time.sleep(1)
    
    # 從h1發送流量到h2
    info(f"*** 從 {h1.name} 到 {h2.name} 的帶寬測試\n")
    result = h1.cmd(f'iperf -c {h2.IP()} -u -b 10M -t 5')
    info(f"*** 結果: {result}\n")
    
    # 停止iperf服務器
    h2.cmd('kill %iperf')
    
    # 測試延遲
    info("\n*** 測試主機間的延遲\n")
    for i in range(1, len(net.hosts)):
        src = net.hosts[0]
        dst = net.hosts[i]
        if src != dst:
            info(f"*** 從 {src.name} 到 {dst.name} 的延遲測試\n")
            result = src.cmd(f'ping -c 3 {dst.IP()}')
            info(f"*** 結果: {result}\n")


def create_network(topo_type='single', controller_ip=DEFAULT_CONTROLLER_IP, 
                  controller_port=DEFAULT_CONTROLLER_PORT, of_version=DEFAULT_OF_VERSION,
                  hosts=2, depth=2, fanout=2, run_cli=True):
    """創建並啟動Mininet網絡
    
    參數:
        topo_type: 拓撲類型 ('single', 'linear', 'tree')
        controller_ip: Ryu控制器IP地址
        controller_port: Ryu控制器端口
        of_version: OpenFlow版本
        hosts: 主機數量 (對於single和linear拓撲)
        depth: 樹深度 (對於tree拓撲)
        fanout: 每個節點的子節點數 (對於tree拓撲)
        run_cli: 是否啟動Mininet CLI
    """
    # 在啟動前先清理環境
    info("*** 清理舊的Mininet環境\n")
    os.system("sudo mn -c")
    
    # 創建拓撲
    if topo_type == 'single':
        topo = SingleSwitchTopo(n=hosts)
        info(f"*** 創建單交換機拓撲，{hosts}個主機\n")
    elif topo_type == 'linear':
        topo = LinearTopo(n=hosts)
        info(f"*** 創建線性拓撲，{hosts}個交換機和主機\n")
    elif topo_type == 'tree':
        topo = TreeTopo(depth=depth, fanout=fanout)
        info(f"*** 創建樹狀拓撲，深度={depth}，分支因子={fanout}\n")
    else:
        info(f"*** 錯誤: 未知的拓撲類型 '{topo_type}'\n")
        return
    
    # 創建網絡
    info(f"*** 使用外部控制器: {controller_ip}:{controller_port}\n")
    info(f"*** OpenFlow版本: {of_version}\n")
    
    # 創建交換機類，設置 OpenFlow 版本
    class OVSWithProtocol(OVSSwitch):
        """Open vSwitch with specified OpenFlow protocol"""
        def __init__(self, *args, **kwargs):
            kwargs.update(protocols=of_version)
            OVSSwitch.__init__(self, *args, **kwargs)
    
    # 創建控制器
    controller = RemoteController('c0', ip=controller_ip, port=controller_port)
    
    # 創建網絡
    net = Mininet(
        topo=topo,
        controller=controller,
        switch=OVSWithProtocol,
        link=TCLink
    )
    
    info(f"\n*** 使用 {of_version} 創建網絡\n")
    
    # 啟動網絡
    net.start()
    
    # 打印節點連接信息
    info("\n*** 打印節點連接信息\n")
    dumpNodeConnections(net.hosts)
    dumpNodeConnections(net.switches)
    
    # 運行測試
    run_tests(net)
    
    # 啟動CLI
    if run_cli:
        info("\n*** 啟動Mininet CLI\n")
        info("*** 可用命令:\n")
        info("***   pingall - 測試所有主機間連通性\n")
        info("***   iperf - 測試帶寬\n")
        info("***   h1 ping h2 - 測試特定主機間連通性\n")
        info("***   exit - 退出\n")
        CLI(net)
    
    # 停止網絡
    info("\n*** 停止網絡\n")
    net.stop()


if __name__ == "__main__":
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="測試Ryu控制器的Mininet腳本")
    parser.add_argument(
        "-t", "--topology", type=str, default="single",
        choices=["single", "linear", "tree"],
        help="拓撲類型: single (單交換機), linear (線性), tree (樹狀)"
    )
    parser.add_argument(
        "-c", "--controller", type=str, default=DEFAULT_CONTROLLER_IP,
        help="控制器IP地址"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_CONTROLLER_PORT,
        help="控制器端口"
    )
    parser.add_argument(
        "-v", "--version", type=str, default=DEFAULT_OF_VERSION,
        help="OpenFlow版本 (例如 OpenFlow13, OpenFlow15)"
    )
    parser.add_argument(
        "-n", "--hosts", type=int, default=2,
        help="主機數量 (對於single和linear拓撲)"
    )
    parser.add_argument(
        "--depth", type=int, default=2,
        help="樹深度 (對於tree拓撲)"
    )
    parser.add_argument(
        "--fanout", type=int, default=2,
        help="每個節點的分支數 (對於tree拓撲)"
    )
    parser.add_argument(
        "--no-cli", action="store_true",
        help="不啟動Mininet CLI，僅運行測試"
    )
    
    args = parser.parse_args()
    
    # 設置日誌級別
    setLogLevel("info")
    
    # 創建網絡
    create_network(
        topo_type=args.topology,
        controller_ip=args.controller,
        controller_port=args.port,
        of_version=args.version,
        hosts=args.hosts,
        depth=args.depth,
        fanout=args.fanout,
        run_cli=not args.no_cli
    )