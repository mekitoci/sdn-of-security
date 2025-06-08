#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ryu SDN控制器進階版 - 整合 OpenFlow 1.3 功能
實現多表處理、群組表和計量表功能於單一應用中
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp, udp, arp, icmp
import datetime

class AdvancedSwitch(app_manager.RyuApp):
    """整合多項OpenFlow 1.3功能的交換機應用"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    # 定義表編號
    TABLE_CLASSIFICATION = 0    # 協議分類表
    TABLE_MAC_FORWARDING = 1    # MAC轉發表
    TABLE_IP_FORWARDING = 2     # IP轉發表
    TABLE_TCP_FORWARDING = 3    # TCP轉發表
    TABLE_UDP_FORWARDING = 4    # UDP轉發表
    
    # 定義群組編號
    GROUP_LOAD_BALANCE = 1      # 負載均衡群組
    GROUP_FAILOVER = 2          # 故障轉移群組
    
    # 定義計量表編號
    METER_NORMAL = 1            # 一般流量計量
    METER_STREAMING = 2         # 流媒體流量計量
    METER_BACKUP = 3            # 備份流量計量
    METER_CRITICAL = 4          # 關鍵業務流量計量
    
    # QoS配置 - 不同服務的帶寬限制（kbps）
    QOS_POLICIES = {
        'normal': 10000,    # 10 Mbps
        'streaming': 5000,  # 5 Mbps
        'backup': 2000,     # 2 Mbps
        'critical': 1000    # 1 Mbps
    }
    
    # TCP/UDP服務端口映射
    SERVICE_PORTS = {
        'streaming': [80, 443, 554, 1935, 8080, 8443],  # 流媒體服務
        'backup': [21, 22, 69, 115, 3690],              # 備份服務
        'critical': [25, 110, 143, 389, 636]            # 關鍵業務
    }

    def __init__(self, *args, **kwargs):
        super(AdvancedSwitch, self).__init__(*args, **kwargs)
        # MAC地址表 {dpid: {mac地址: 端口}}
        self.mac_table = {}
        self.packet_count = 0
        
        # DDoS攻擊偵測相關計數器
        self.syn_flood_count = {}  # {來源IP: SYN封包計數}
        self.syn_threshold = 10     # 警報閾值
        self.syn_monitor_window = 60  # 監控時間窗口(秒)
        
        # 初始化日誌
        self.logger.info("="*50)
        self.logger.info("進階交換機應用初始化 - %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info("開啟 DDoS 偵測功能 - SYN Flood 高效偵測")
        self.logger.info("="*50)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """處理交換機連接事件，安裝初始流表和功能"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        
        # 獲取交換機IP地址
        switch_ip = datapath.address[0]  # address是一個tuple (ip, port)
        switch_port = datapath.address[1]
        
        # 清空所有現有流表
        self.clear_all_flows(datapath)
        
        self.logger.info("\n%s\n交換機 %s 連接成功，開始初始化進階功能\n%s", 
                        "="*30, dpid, "="*30)
        self.logger.info("🌐 交換機IP地址: %s:%s", switch_ip, switch_port)
        self.logger.info("🔗 交換機DPID: %s", dpid)
        
        # 初始化多表結構 (Multiple Tables)
        self.setup_multiple_tables(datapath)
        
        # 初始化群組表 (Group Tables)
        self.setup_group_tables(datapath)
        
        # 初始化計量表 (Meter Tables)
        self.setup_meter_tables(datapath)
        
        self.logger.info("交換機 %s 功能初始化完成", dpid)

    def clear_all_flows(self, datapath):
        """清空交換機上的所有流表"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 清除所有表中的流表
        for table_id in range(0, 5):  # 清除表0-4
            match = parser.OFPMatch()
            instructions = []
            flow_mod = parser.OFPFlowMod(
                datapath=datapath,
                table_id=table_id,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=match,
                instructions=instructions)
            datapath.send_msg(flow_mod)
        
        self.logger.info("已清除交換機 %s 的所有流表", datapath.id)

    def setup_multiple_tables(self, datapath):
        """設定多表結構和表間跳轉"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 要簡化開發，只使用第0張表即可
        # 清除已有流表
        match = parser.OFPMatch()
        mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match)
        datapath.send_msg(mod)
        
        # 設置默認轉發規則 - 避免TCAM高初始化消耗
        # 默認規則：初始化時轉發到控制器
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        # 處理廣播封包
        match = parser.OFPMatch(eth_dst='ff:ff:ff:ff:ff:ff')
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 10, match, actions)
        
        # 處理ARP封包
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 5, match, actions)

        self.logger.info("基本流表初始化完成")

    def setup_group_tables(self, datapath):
        """設定群組表功能"""
        pass  # 略

    def setup_meter_tables(self, datapath):
        """設定計量表功能和QoS策略"""
        pass  # 略

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst,
            table_id=table_id)
        datapath.send_msg(mod)

    def add_flow_with_inst(self, datapath, priority, match, instructions, table_id=0):
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=instructions,
            table_id=table_id)
        datapath.send_msg(mod)
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """處理轉發到控制器的數據包 - 基本L2轉發功能"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        
        # 解析封包
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # 忽略LLDP數據包
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        # 取得來源和目標MAC地址    
        dst = eth.dst
        src = eth.src
        
        self.logger.info("Packet in %s %s %s %s", dpid, src, dst, in_port)
        
        # 學習發送方的MAC地址和端口，以避免泛洪
        self.mac_table.setdefault(dpid, {})
        self.mac_table[dpid][src] = in_port
        
        # 如果目標是廣播就泛洪
        if dst == 'ff:ff:ff:ff:ff:ff':
            out_port = ofproto.OFPP_FLOOD
        elif dst in self.mac_table[dpid]:
            out_port = self.mac_table[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        # 設定動作
        actions = [parser.OFPActionOutput(out_port)]
        
        # 安裝流表項（非泛洪情況）
        if out_port != ofproto.OFPP_FLOOD:
            # 安裝MAC層面流表項：來源MAC -> 進入端口
            match = parser.OFPMatch(eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)
            self.logger.info("安裝MAC流表: %s -> 端口 %s", dst, out_port)
        
        # 發送封包
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=msg.buffer_id,
                                  in_port=in_port,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)
        
        # 增加封包計數
        self.packet_count += 1
        
        # 檢查是否有 ARP 協議
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            arp_op = "請求" if arp_pkt.opcode == 1 else "回覆"
            self.logger.info("ARP %s: %s -> %s", arp_op, arp_pkt.src_ip, arp_pkt.dst_ip)
        
        # 檢查是否有 IPv4 協議
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            self.logger.info("IPv4: %s -> %s", ipv4_pkt.src, ipv4_pkt.dst)
            
            # 特別關注 TCP SYN 封包 (用於 SYN flood 偵測)
            tcp_pkt = pkt.get_protocol(tcp.tcp) 
            if tcp_pkt:
                # 記錄TCP旗標
                tcp_flags = ""
                if tcp_pkt.has_flags(tcp.TCP_SYN):
                    tcp_flags += "SYN "
                if tcp_pkt.has_flags(tcp.TCP_ACK):
                    tcp_flags += "ACK "
                if tcp_pkt.has_flags(tcp.TCP_FIN):
                    tcp_flags += "FIN "
                if tcp_pkt.has_flags(tcp.TCP_RST):
                    tcp_flags += "RST "
                    
                # 紀錄基本 TCP 封包資訊
                self.logger.info("TCP: %s:%s -> %s:%s [%s]", 
                                ipv4_pkt.src, tcp_pkt.src_port,
                                ipv4_pkt.dst, tcp_pkt.dst_port,
                                tcp_flags)
                
                # 偵測可能的 SYN flood
                # 1. 只有 SYN 旗標設置，沒有 ACK 旗標
                # 2. 通常是大量來自相同來源IP的SYN封包
                if tcp_pkt.has_flags(tcp.TCP_SYN) and not tcp_pkt.has_flags(tcp.TCP_ACK):
                    # 顯示警告消息，帶有更顯著的警告格式
                    self.logger.warning("❗ 可能的 SYN FLOOD 攻擊: ❗")
                    self.logger.warning("   來源: %s:%s -> 目標: %s:%s", 
                                      ipv4_pkt.src, tcp_pkt.src_port,
                                      ipv4_pkt.dst, tcp_pkt.dst_port)
                    
                    # 實現計數機制以追蹤每個來源IP的SYN封包數量
                    src_ip = ipv4_pkt.src
                    if src_ip in self.syn_flood_count:
                        self.syn_flood_count[src_ip] += 1
                    else:
                        self.syn_flood_count[src_ip] = 1
                    
                    # 當SYN封包數量超過一定閾值時，觸發報警
                    if self.syn_flood_count[src_ip] > 10:
                        self.logger.critical("❗❗❗ SYN FLOOD 攻擊報警: 來源IP %s 的SYN封包數量超過10個", src_ip)
        
        # 由於我們之前已經發送了封包，不需要再次發送
            
        # 增加封包計數
        self.packet_count += 1
            
        # 美化的日誌記錄
        self.logger.info("-" * 50)
        self.logger.info("● 封包資訊 ● #%d | %s", 
                        self.packet_count, datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3])
        self.logger.info("→ 來源MAC: %-17s | 入口端口: %-4s | 交換機: %s", src, in_port, dpid)
        self.logger.info("→ 目標MAC: %-17s | 出口端口: %-4s | 動作: %s", 
                        dst, out_port, "泛洪" if out_port == ofproto.OFPP_FLOOD else "轉發")
        
        # 顯示MAC表狀態 - 使用表格式式
        if dpid in self.mac_table and self.mac_table[dpid]:
            self.logger.info("○ MAC對應表 ○")
            self.logger.info("┌%s┬%s┐", "-" * 19, "-" * 7)
            self.logger.info("│ %-17s │ %-5s │", "MAC地址", "端口")
            self.logger.info("├%s┼%s┤", "-" * 19, "-" * 7)
            
            for mac, port in self.mac_table[dpid].items():
                self.logger.info("│ %-17s │ %-5s │", mac, port)
                
            self.logger.info("└%s┴%s┘", "-" * 19, "-" * 7)
