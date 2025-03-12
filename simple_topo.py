#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
簡單的Mininet拓撲腳本，用於測試Ryu控制器
可創建自定義大小的網絡拓撲，並提供性能測試功能
"""

import time
import argparse

# import matplotlib.pyplot as plt
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.term import makeTerm

controller_ip = "10.101.9.222"
controller_port = 6653

def create_topo(
    switch_count=1,
    host_count=2,
    controller_ip=controller_ip,
    controller_port=controller_port,
    bandwidth=None,
    delay=None,
    save_topo=False,
):
    """創建自定義網絡拓撲並啟動

    參數:
        switch_count (int): 交換機數量
        host_count (int): 主機數量
        controller_ip (str): 控制器IP地址
        controller_port (int): 控制器端口
        bandwidth (int): 鏈路頻寬 (Mbps)
        delay (str): 鏈路延遲 (例如 '10ms')
        save_topo (bool): 是否保存拓撲圖
    """

    # 創建網絡，使用外部控制器
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

    # 測試連通性
    info("\n*** 測試網絡連通性\n")
    net.pingAll()

    # 如果需要保存拓撲圖
    # if save_topo:
    #     save_topology_graph(net, 'network_topology.png')

    # 啟動命令行界面
    info("\n*** 啟動Mininet CLI\n")
    info("*** 可用命令:\n")
    info("***   pingall - 測試所有主機間連通性\n")
    info("***   h1 ping h2 - 測試特定主機間連通性\n")
    info("***   iperf h1 h2 - 測試h1和h2之間的頻寬\n")
    info("***   monitor - 監控網絡流量\n")
    info("***   exit - 退出\n")

    # 添加自定義命令到CLI
    CLI.do_iperf = do_iperf
    CLI.do_monitor = do_monitor

    CLI(net)

    # 停止網絡
    info("\n*** 停止網絡\n")
    net.stop()


def do_iperf(self, line):
    """運行iperf測試兩個主機之間的頻寬
    用法: iperf 主機1 主機2
    例如: iperf h1 h2
    """
    args = line.split()
    if len(args) != 2:
        info("用法: iperf 主機1 主機2\n")
        return

    host1_name, host2_name = args
    net = self.mn

    if host1_name not in net or host2_name not in net:
        info(f"錯誤: 找不到主機 {host1_name} 或 {host2_name}\n")
        return

    host1, host2 = net.get(host1_name), net.get(host2_name)
    info(f"*** 測試 {host1_name} 和 {host2_name} 之間的頻寬\n")

    # 在host2上啟動iperf服務器
    server = host2.popen("iperf -s")
    time.sleep(0.5)  # 給服務器啟動的時間

    # 在host1上運行iperf客戶端
    client_output = host1.cmd("iperf -c", host2.IP())
    info(client_output)

    # 停止服務器
    server.terminate()


def do_monitor(self, line):
    """監控網絡流量
    用法: monitor [時間(秒)]
    例如: monitor 10
    """
    args = line.split()
    duration = 10  # 默認監控10秒

    if len(args) == 1:
        try:
            duration = int(args[0])
        except ValueError:
            info("錯誤: 時間必須是整數\n")
            return

    net = self.mn
    info(f"*** 監控網絡流量 {duration} 秒...\n")

    # 在每個交換機上運行tcpdump
    for switch in net.switches:
        term = makeTerm(switch, "tcpdump -i any -n")
        info(f"在 {switch.name} 上啟動了tcpdump\n")

    info(f"監控將持續 {duration} 秒，請觀察彈出的終端窗口\n")
    time.sleep(duration)


def save_topology_graph(net, filename):
    """保存網絡拓撲圖"""
    try:
        plt.figure(figsize=(12, 8))

        # 繪製節點
        positions = {}
        for i, switch in enumerate(net.switches):
            x = i * 2
            y = 0
            positions[switch] = (x, y)
            plt.plot(x, y, "bs", markersize=10)  # 藍色方形表示交換機
            plt.text(x, y - 0.3, switch.name, horizontalalignment="center")

        host_y = 2  # 主機的y坐標
        for i, host in enumerate(net.hosts):
            # 找到連接到這個主機的交換機
            for link in net.links:
                if host in (link.intf1.node, link.intf2.node):
                    # 獲取連接的另一端
                    other_end = (
                        link.intf2.node if link.intf1.node == host else link.intf1.node
                    )
                    if other_end in net.switches:
                        # 將主機放在交換機上方
                        switch_x = positions[other_end][0]
                        host_x = switch_x + (i % 3 - 1) * 0.5  # 在交換機周圍分散主機
                        positions[host] = (host_x, host_y)
                        # 繪製主機
                        plt.plot(host_x, host_y, "ro", markersize=8)  # 紅色圓形表示主機
                        plt.text(
                            host_x,
                            host_y + 0.2,
                            host.name,
                            horizontalalignment="center",
                        )
                        # 繪製連接線
                        plt.plot([host_x, switch_x], [host_y, 0], "k-")  # 黑色線條
                        break

        # 繪製交換機之間的連接
        for link in net.links:
            if link.intf1.node in net.switches and link.intf2.node in net.switches:
                x1, y1 = positions[link.intf1.node]
                x2, y2 = positions[link.intf2.node]
                plt.plot([x1, x2], [y1, y2], "g-", linewidth=2)  # 綠色線條

        plt.title("網絡拓撲圖")
        plt.axis("off")  # 不顯示坐標軸
        plt.savefig(filename)
        info(f"\n*** 拓撲圖已保存到 {filename}\n")
    except Exception as e:
        info(f"\n*** 保存拓撲圖時出錯: {e}\n")


if __name__ == "__main__":
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="創建自定義Mininet拓撲")
    parser.add_argument("-s", "--switches", type=int, default=1, help="交換機數量")
    parser.add_argument("-n", "--hosts", type=int, default=2, help="主機數量")
    parser.add_argument(
        "-c", "--controller", type=str, default=controller_ip, help="控制器IP地址"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=controller_port, help="控制器端口"
    )
    parser.add_argument("-b", "--bandwidth", type=int, help="鏈路頻寬 (Mbps)")
    parser.add_argument("-d", "--delay", type=str, help='鏈路延遲 (例如 "10ms")')
    parser.add_argument("-g", "--graph", action="store_true", help="保存拓撲圖")

    args = parser.parse_args()

    # 設置日誌級別
    setLogLevel("info")

    # 創建拓撲
    create_topo(
        switch_count=args.switches,
        host_count=args.hosts,
        controller_ip=args.controller,
        controller_port=args.port,
        bandwidth=args.bandwidth,
        delay=args.delay,
        save_topo=args.graph,
    )
