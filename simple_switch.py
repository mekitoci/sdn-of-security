#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
簡化版Ryu SDN控制器
實現基本的第2層交換機功能 - OpenFlow 1.3版本
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp, udp, arp, icmp
import datetime

class SimpleSwitch(app_manager.RyuApp):
    """簡化版L2交換機Ryu應用"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        # MAC地址表 {dpid: {mac地址: 端口}}
        self.mac_table = {}
        self.packet_count = 0
        self.logger.info("="*50)
        self.logger.info("簡單交換機應用初始化 - %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.logger.info("="*50)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """處理交換機特性事件，安裝表缺失流表項"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # 安裝表缺失流表項，轉發到控制器
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info("\n%s\n交換機 %s 連接成功\n%s", "="*30, datapath.id, "="*30)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """添加流表項到交換機"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """處理轉發到控制器的數據包"""
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("數據包被截斷，只接收到 %s 字節，共 %s 字節",
                             ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # 忽略LLDP數據包
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
            
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        # 學習發送方的MAC地址和端口，以避免泛洪
        self.mac_table.setdefault(dpid, {})
        self.mac_table[dpid][src] = in_port
        
        # 如果目的MAC地址已在表中，獲取輸出端口，否則泛洪
        if dst in self.mac_table[dpid]:
            out_port = self.mac_table[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
            
        # 準備轉發動作
        actions = [parser.OFPActionOutput(out_port)]
        
        # 安裝流表以避免下次出現 packet_in
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)
        
        # 發送數據包
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        # 使用 OpenFlow 1.3 的 OFPPacketOut 構造方式
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                              in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
        
        # 增加封包計數
        self.packet_count += 1
        
        # 簡化的日誌記錄 - 只顯示基本信息
        self.logger.info("\n")
        self.logger.info("封包 #%d 資訊:", self.packet_count)
        self.logger.info("交換機 ID: %s", dpid)
        self.logger.info("入口端口: %s", in_port)
        self.logger.info("來源 MAC: %s", src)
        self.logger.info("目標 MAC: %s", dst)
        self.logger.info("輸出端口: %s", out_port)
        
        # 檢查是否有 IPv4 協議並顯示簡單信息
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            self.logger.info("IPv4 - 來源 IP: %s -> 目標 IP: %s", ipv4_pkt.src, ipv4_pkt.dst)
            
            # 顯示 ICMP 信息 (Ping)
            icmp_pkt = pkt.get_protocol(icmp.icmp)
            if icmp_pkt:
                icmp_type = "Echo Request" if icmp_pkt.type == 8 else "Echo Reply" if icmp_pkt.type == 0 else str(icmp_pkt.type)
                self.logger.info("ICMP 類型: %s", icmp_type)
        
        # 檢查是否有 ARP 協議並顯示簡單信息
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            arp_op = "請求" if arp_pkt.opcode == 1 else "回覆"
            self.logger.info("ARP %s - %s -> %s", arp_op, arp_pkt.src_ip, arp_pkt.dst_ip)
        
        # 顯示MAC表狀態
        self.logger.info("MAC表狀態:")
        if dpid in self.mac_table:
            for mac, port in self.mac_table[dpid].items():
                self.logger.info("%s -> 端口 %s", mac, port)
        self.logger.info("="*50)
