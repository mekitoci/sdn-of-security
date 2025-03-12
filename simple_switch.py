#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
簡化版Ryu SDN控制器
實現基本的第2層交換機功能
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp, udp, arp, icmp
from ryu.lib.packet import arp, ipv6, icmpv6, vlan, dhcp
import datetime
import mysql.connector
from mysql.connector import Error
import pandas as pd

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
        
        # MySQL 連接設定
        try:
            self.mysql_conn = mysql.connector.connect(
                host='localhost',       # MySQL伺服器地址
                user='myuser',         # Docker指定的使用者名稱
                password='mypassword', # Docker指定的密碼
                database='mydb'        # Docker指定的資料庫名稱
            )
            
            self.logger.info("MySQL 資料庫連接成功")

            
        except Error as e:
            self.logger.error("MySQL 連接錯誤: %s", e)
            self.mysql_conn = None

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
        # 如果是可禁用的交換機，則直接忽略
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
            
        # 初始化各協議變數
        vlan_pkt = None
        arp_pkt = None
        ipv4_pkt = None
        icmp_pkt = None
        tcp_pkt = None
        udp_pkt = None
        dhcp_pkt = None
        ipv6_pkt = None
        icmpv6_pkt = None

        # 增加封包計數
        self.packet_count += 1
        
        # 添加分隔線和封包編號
        self.logger.info("\n%s\n封包 #%d - %s\n%s", 
                        "*"*80, 
                        self.packet_count,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                        "*"*80)
        
        # 基本封包資訊 - 使用表格式格式
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│ 基本資訊                                                    │")
        self.logger.info("├─────────────────────────────────────────────────────────────┤")
        self.logger.info("│ 交換機 ID    : %-45s │", dpid)
        self.logger.info("│ 入口端口     : %-45s │", in_port)
        self.logger.info("│ 來源 MAC     : %-45s │", src)
        self.logger.info("│ 目標 MAC     : %-45s │", dst)
        self.logger.info("│ 乙太網類型   : 0x%04x %-40s │", eth.ethertype, self._get_ethertype_name(eth.ethertype))
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # 檢查是否有 VLAN 標籤
        vlan_pkt = pkt.get_protocol(vlan.vlan)
        if vlan_pkt:
            self.logger.info("┌─────────────────────────────────────────────────────────────┐")
            self.logger.info("│ VLAN 資訊                                                   │")
            self.logger.info("├─────────────────────────────────────────────────────────────┤")
            self.logger.info("│ VLAN ID      : %-45s │", vlan_pkt.vid)
            self.logger.info("│ 優先級       : %-45s │", vlan_pkt.pcp)
            self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # 檢查是否有 ARP 協議
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            arp_op = "請求" if arp_pkt.opcode == 1 else "回覆"
            self.logger.info("┌─────────────────────────────────────────────────────────────┐")
            self.logger.info("│ ARP 資訊                                                    │")
            self.logger.info("├─────────────────────────────────────────────────────────────┤")
            self.logger.info("│ 操作         : %-45s │", arp_op)
            self.logger.info("│ 來源 IP      : %-45s │", arp_pkt.src_ip)
            self.logger.info("│ 來源 MAC     : %-45s │", arp_pkt.src_mac)
            self.logger.info("│ 目標 IP      : %-45s │", arp_pkt.dst_ip)
            self.logger.info("│ 目標 MAC     : %-45s │", arp_pkt.dst_mac)
            self.logger.info("└─────────────────────────────────────────────────────────────┘")
            
        # 檢查是否有 IPv4 協議
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            self.logger.info("┌─────────────────────────────────────────────────────────────┐")
            self.logger.info("│ IPv4 資訊                                                   │")
            self.logger.info("├─────────────────────────────────────────────────────────────┤")
            self.logger.info("│ 版本         : %-45s │", ipv4_pkt.version)
            self.logger.info("│ 來源 IP      : %-45s │", ipv4_pkt.src)
            self.logger.info("│ 目標 IP      : %-45s │", ipv4_pkt.dst)
            self.logger.info("│ 協議         : %-3d %-41s │", ipv4_pkt.proto, self._get_ip_proto_name(ipv4_pkt.proto))
            self.logger.info("│ TTL          : %-45s │", ipv4_pkt.ttl)
            self.logger.info("│ 服務類型     : %-45s │", ipv4_pkt.tos)
            self.logger.info("│ 識別碼       : %-45s │", ipv4_pkt.identification)
            self.logger.info("│ 標誌         : %-45s │", ipv4_pkt.flags)
            self.logger.info("└─────────────────────────────────────────────────────────────┘")
            
            # 檢查是否有 ICMP 協議
            icmp_pkt = pkt.get_protocol(icmp.icmp)
            if icmp_pkt:
                icmp_type = "Echo Request" if icmp_pkt.type == 8 else "Echo Reply" if icmp_pkt.type == 0 else str(icmp_pkt.type)
                self.logger.info("┌─────────────────────────────────────────────────────────────┐")
                self.logger.info("│ ICMP 資訊                                                   │")
                self.logger.info("├─────────────────────────────────────────────────────────────┤")
                self.logger.info("│ 類型         : %-3d %-41s │", icmp_pkt.type, icmp_type)
                self.logger.info("│ 代碼         : %-45s │", icmp_pkt.code)
                self.logger.info("│ 校驗和       : %-45s │", icmp_pkt.csum)
                self.logger.info("└─────────────────────────────────────────────────────────────┘")
                
            # 檢查是否有 TCP 協議
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            if tcp_pkt:
                self.logger.info("┌─────────────────────────────────────────────────────────────┐")
                self.logger.info("│ TCP 資訊                                                    │")
                self.logger.info("├─────────────────────────────────────────────────────────────┤")
                self.logger.info("│ 來源端口     : %-5d %-39s │", tcp_pkt.src_port, self._get_port_name(tcp_pkt.src_port))
                self.logger.info("│ 目標端口     : %-5d %-39s │", tcp_pkt.dst_port, self._get_port_name(tcp_pkt.dst_port))
                self.logger.info("│ 序列號       : %-45s │", tcp_pkt.seq)
                self.logger.info("│ 確認號       : %-45s │", tcp_pkt.ack)
                self.logger.info("│ 資料偏移     : %-45s │", tcp_pkt.offset)
                self.logger.info("│ 視窗大小     : %-45s │", tcp_pkt.window_size)
                
                # TCP 標誌
                flags = []
                if tcp_pkt.has_flags(tcp.TCP_SYN):
                    flags.append("SYN")
                if tcp_pkt.has_flags(tcp.TCP_ACK):
                    flags.append("ACK")
                if tcp_pkt.has_flags(tcp.TCP_FIN):
                    flags.append("FIN")
                if tcp_pkt.has_flags(tcp.TCP_RST):
                    flags.append("RST")
                if tcp_pkt.has_flags(tcp.TCP_PSH):
                    flags.append("PSH")
                if tcp_pkt.has_flags(tcp.TCP_URG):
                    flags.append("URG")
                
                self.logger.info("│ 標誌         : %-45s │", ", ".join(flags))
                self.logger.info("└─────────────────────────────────────────────────────────────┘")
                
            # 檢查是否有 UDP 協議
            udp_pkt = pkt.get_protocol(udp.udp)
            if udp_pkt:
                self.logger.info("┌─────────────────────────────────────────────────────────────┐")
                self.logger.info("│ UDP 資訊                                                    │")
                self.logger.info("├─────────────────────────────────────────────────────────────┤")
                self.logger.info("│ 來源端口     : %-5d %-39s │", udp_pkt.src_port, self._get_port_name(udp_pkt.src_port))
                self.logger.info("│ 目標端口     : %-5d %-39s │", udp_pkt.dst_port, self._get_port_name(udp_pkt.dst_port))
                self.logger.info("│ 長度         : %-45s │", udp_pkt.total_length)
                self.logger.info("│ 校驗和       : %-45s │", udp_pkt.csum)
                self.logger.info("└─────────────────────────────────────────────────────────────┘")
                
                # 檢查是否有 DHCP 協議
                dhcp_pkt = pkt.get_protocol(dhcp.dhcp)
                if dhcp_pkt:
                    dhcp_message_type = ""
                    for option in dhcp_pkt.options.option_list:
                        if option.tag == dhcp.DHCP_MESSAGE_TYPE_OPT:
                            message_type = ord(option.value)
                            if message_type == 1:
                                dhcp_message_type = "DISCOVER"
                            elif message_type == 2:
                                dhcp_message_type = "OFFER"
                            elif message_type == 3:
                                dhcp_message_type = "REQUEST"
                            elif message_type == 4:
                                dhcp_message_type = "DECLINE"
                            elif message_type == 5:
                                dhcp_message_type = "ACK"
                            elif message_type == 6:
                                dhcp_message_type = "NAK"
                            elif message_type == 7:
                                dhcp_message_type = "RELEASE"
                            elif message_type == 8:
                                dhcp_message_type = "INFORM"
                    
                    self.logger.info("┌─────────────────────────────────────────────────────────────┐")
                    self.logger.info("│ DHCP 資訊                                                   │")
                    self.logger.info("├─────────────────────────────────────────────────────────────┤")
                    self.logger.info("│ 訊息類型     : %-45s │", dhcp_message_type)
                    self.logger.info("│ 交易 ID     : %-45s │", dhcp_pkt.xid)
                    self.logger.info("│ 客戶端 MAC   : %-45s │", dhcp_pkt.chaddr)
                    self.logger.info("│ 客戶端 IP    : %-45s │", dhcp_pkt.ciaddr)
                    self.logger.info("│ 您的 IP      : %-45s │", dhcp_pkt.yiaddr)
                    self.logger.info("│ 服務器 IP    : %-45s │", dhcp_pkt.siaddr)
                    self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # 檢查是否有 IPv6 協議
        ipv6_pkt = pkt.get_protocol(ipv6.ipv6)
        if ipv6_pkt:
            self.logger.info("┌─────────────────────────────────────────────────────────────┐")
            self.logger.info("│ IPv6 資訊                                                   │")
            self.logger.info("├─────────────────────────────────────────────────────────────┤")
            self.logger.info("│ 版本         : %-45s │", ipv6_pkt.version)
            self.logger.info("│ 來源 IP      : %-45s │", ipv6_pkt.src)
            self.logger.info("│ 目標 IP      : %-45s │", ipv6_pkt.dst)
            self.logger.info("│ 下一個標頭   : %-45s │", ipv6_pkt.nxt)
            self.logger.info("│ 躍點限制     : %-45s │", ipv6_pkt.hop_limit)
            self.logger.info("└─────────────────────────────────────────────────────────────┘")
            
            # 檢查是否有 ICMPv6 協議
            icmpv6_pkt = pkt.get_protocol(icmpv6.icmpv6)
            if icmpv6_pkt:
                icmpv6_type = ""
                if icmpv6_pkt.type_ == icmpv6.ND_NEIGHBOR_SOLICIT:
                    icmpv6_type = "Neighbor Solicitation"
                elif icmpv6_pkt.type_ == icmpv6.ND_NEIGHBOR_ADVERT:
                    icmpv6_type = "Neighbor Advertisement"
                elif icmpv6_pkt.type_ == icmpv6.ICMPV6_ECHO_REQUEST:
                    icmpv6_type = "Echo Request"
                elif icmpv6_pkt.type_ == icmpv6.ICMPV6_ECHO_REPLY:
                    icmpv6_type = "Echo Reply"
                else:
                    icmpv6_type = str(icmpv6_pkt.type_)
                
                self.logger.info("┌─────────────────────────────────────────────────────────────┐")
                self.logger.info("│ ICMPv6 資訊                                                 │")
                self.logger.info("├─────────────────────────────────────────────────────────────┤")
                self.logger.info("│ 類型         : %-3d %-41s │", icmpv6_pkt.type_, icmpv6_type)
                self.logger.info("│ 代碼         : %-45s │", icmpv6_pkt.code)
                self.logger.info("│ 校驗和       : %-45s │", icmpv6_pkt.csum)
                self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # 顯示MAC表狀態
        self.logger.info("┌─────────────────────────────────────────────────────────────┐")
        self.logger.info("│ MAC表狀態                                                   │")
        self.logger.info("├─────────────────────────────────────────────────────────────┤")
        if dpid in self.mac_table:
            for mac, port in self.mac_table[dpid].items():
                self.logger.info("│ %-17s -> 端口 %-35s │", mac, port)
        if not self.mac_table.get(dpid, {}):
            self.logger.info("│ 交換機 %s 的MAC表為空                                    │", dpid)
        self.logger.info("└─────────────────────────────────────────────────────────────┘")
        
        # 將封包資料寫入MySQL資料庫
        if self.mysql_conn:
            try:
                self._insert_packet_data(dpid, in_port, src, dst, eth.ethertype, 
                                    out_port, out_port == ofproto.OFPP_FLOOD,
                                    vlan_pkt, arp_pkt, ipv4_pkt, icmp_pkt, tcp_pkt, udp_pkt, dhcp_pkt, ipv6_pkt, icmpv6_pkt, pkt)
                self.logger.info("MySQL: 封包數據已寫入資料庫")
            except Error as e:
                self.logger.error("MySQL 封包資料寫入錯誤: %s", e)

    def _insert_packet_data(self, dpid, in_port, src_mac, dst_mac, ethertype, out_port, is_flood,
                         vlan_pkt, arp_pkt, ipv4_pkt, icmp_pkt, tcp_pkt, udp_pkt, dhcp_pkt, ipv6_pkt, icmpv6_pkt, pkt=None):
        """將封包數據插入到MySQL資料庫 - 使用動態SQL查詢，只插入有數據的欄位"""
        try:
            import pandas as pd
            
            # 建立資料字典
            data = {}
            
            # 基本封包信息 - 必須欄位
            data['switch_id'] = dpid
            data['in_port'] = in_port
            data['src_mac'] = str(src_mac)
            data['dst_mac'] = str(dst_mac)
            data['ethertype'] = ethertype
            data['ethertype_name'] = self._get_ethertype_name(ethertype)
            # Ensure out_port is within MySQL INT range (-2147483648 to 2147483647)
            # If out_port is too large, use a safe value
            if isinstance(out_port, int) and (out_port < -2147483648 or out_port > 2147483647):
                self.logger.warning(f"Out_port value {out_port} is out of MySQL INT range. Using 0 instead.")
                data['out_port'] = 0
            else:
                data['out_port'] = out_port
            data['is_flood'] = is_flood
            data['decision_reason'] = "目標MAC未知" if is_flood else "MAC表中找到匹配項"
            data['flow_installed'] = out_port != 0
            data['capture_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # 原始封包數據
            if pkt:
                try:
                    if hasattr(pkt, 'data'):
                        data['raw_packet_data'] = pkt.data
                    else:
                        data['raw_packet_data'] = bytes(pkt)
                except:
                    pass  # 如果無法取得封包數據則跳過
            
            # VLAN信息（如果有的話）
            if vlan_pkt is not None:
                data['has_vlan'] = True
                data['vlan_id'] = vlan_pkt.vid
                data['vlan_priority'] = vlan_pkt.pcp
            
            # ARP信息（如果有的話）
            if arp_pkt is not None:
                data['is_arp'] = True
                data['arp_operation'] = arp_pkt.opcode
                data['arp_operation_name'] = "Request" if arp_pkt.opcode == 1 else ("Reply" if arp_pkt.opcode == 2 else None)
                data['arp_src_ip'] = str(arp_pkt.src_ip)
                data['arp_src_mac'] = arp_pkt.src_mac
                data['arp_dst_ip'] = str(arp_pkt.dst_ip)
                data['arp_dst_mac'] = arp_pkt.dst_mac
            
            # IPv4信息（如果有的話）
            if ipv4_pkt is not None:
                data['is_ipv4'] = True
                data['ipv4_version'] = ipv4_pkt.version
                data['ipv4_src'] = str(ipv4_pkt.src)
                data['ipv4_dst'] = str(ipv4_pkt.dst)
                data['ipv4_proto'] = ipv4_pkt.proto
                data['ipv4_proto_name'] = self._get_ip_proto_name(ipv4_pkt.proto)
                data['ipv4_ttl'] = ipv4_pkt.ttl
                data['ipv4_tos'] = ipv4_pkt.tos
                data['ipv4_identification'] = ipv4_pkt.identification
                data['ipv4_flags'] = ipv4_pkt.flags
            
            # ICMP信息（如果有的話）
            if icmp_pkt is not None:
                data['is_icmp'] = True
                data['icmp_type'] = icmp_pkt.type
                data['icmp_type_name'] = self._get_icmp_type_name(icmp_pkt.type)
                data['icmp_code'] = icmp_pkt.code
            
            # TCP信息（如果有的話）
            if tcp_pkt is not None:
                data['is_tcp'] = True
                data['tcp_src_port'] = tcp_pkt.src_port
                data['tcp_src_service'] = self._get_port_name(tcp_pkt.src_port)
                data['tcp_dst_port'] = tcp_pkt.dst_port
                data['tcp_dst_service'] = self._get_port_name(tcp_pkt.dst_port)
                data['tcp_seq_num'] = tcp_pkt.seq
                data['tcp_ack_num'] = tcp_pkt.ack
                data['tcp_flags'] = self._get_tcp_flags_string(tcp_pkt)
                data['tcp_window_size'] = tcp_pkt.window_size
            
            # UDP信息（如果有的話）
            if udp_pkt is not None:
                data['is_udp'] = True
                data['udp_src_port'] = udp_pkt.src_port
                data['udp_src_service'] = self._get_port_name(udp_pkt.src_port)
                data['udp_dst_port'] = udp_pkt.dst_port
                data['udp_dst_service'] = self._get_port_name(udp_pkt.dst_port)
                data['udp_length'] = udp_pkt.total_length
                data['udp_checksum'] = udp_pkt.csum
            
            # DHCP信息（如果有的話）
            if dhcp_pkt is not None:
                data['is_dhcp'] = True
                data['dhcp_message_type'] = self._get_dhcp_message_type(dhcp_pkt)
                data['dhcp_transaction_id'] = dhcp_pkt.xid
                data['dhcp_client_mac'] = dhcp_pkt.chaddr
                data['dhcp_client_ip'] = dhcp_pkt.ciaddr
                data['dhcp_your_ip'] = dhcp_pkt.yiaddr
                data['dhcp_server_ip'] = dhcp_pkt.siaddr
            
            # IPv6信息（如果有的話）
            if ipv6_pkt is not None:
                data['is_ipv6'] = True
                data['ipv6_version'] = ipv6_pkt.version
                data['ipv6_src'] = str(ipv6_pkt.src)
                data['ipv6_dst'] = str(ipv6_pkt.dst)
                data['ipv6_next_header'] = ipv6_pkt.nxt
                data['ipv6_hop_limit'] = ipv6_pkt.hop_limit
            
            # ICMPv6信息（如果有的話）
            if icmpv6_pkt is not None:
                data['is_icmpv6'] = True
                data['icmpv6_type'] = icmpv6_pkt.type_
                data['icmpv6_type_name'] = self._get_icmpv6_type_name(icmpv6_pkt.type_)
                data['icmpv6_code'] = icmpv6_pkt.code
                data['icmpv6_checksum'] = icmpv6_pkt.csum
            
            # 轉換為 pandas DataFrame 進行數據處理
            df = pd.DataFrame([data])
            
            # 刪除所有 None 值的列
            df = df.dropna(axis=1, how='all')
            
            # 構建動態 SQL 查詢
            columns = df.columns.tolist()
            placeholders = ', '.join(['%s'] * len(columns))
            column_str = ', '.join(columns)
            
            # 最終的 SQL 查詢
            insert_query = f"INSERT INTO raw_packet_data ({column_str}) VALUES ({placeholders})"
            
            # 執行查詢
            cursor = self.mysql_conn.cursor()
            # 先轉換為Python原生類型再傳給MySQL並確保數據類型範圍正確
            values = []
            for i, val in enumerate(df.iloc[0].values.tolist()):
                # 先將NumPy類型轉換為Python原生類型
                if hasattr(val, 'item'):
                    val = val.item()
                
                # 檢查整數類型是否超出MySQL INT範圍 (-2147483648 到 2147483647)
                if isinstance(val, int) and not isinstance(val, bool):
                    # 檢查列名是否包含 'seq_num' 或 'ack_num' - 這些可能是BIGINT類型
                    column_name = df.columns[i] if i < len(df.columns) else ''
                    is_bigint_column = 'seq_num' in column_name or 'ack_num' in column_name
                    
                    # 如果不是BIGINT列且值超出INT範圍，則進行截斷
                    if not is_bigint_column and (val < -2147483648 or val > 2147483647):
                        self.logger.warning(f"Value {val} for column {column_name} is out of MySQL INT range. Clamping to range.")
                        val = max(-2147483648, min(val, 2147483647))
                
                values.append(val)
                
            cursor.execute(insert_query, values)
            self.mysql_conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error("MySQL 插入封包數據錯誤: %s", e)
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _get_icmp_type_name(self, icmp_type):
        """獲取ICMP類型名稱"""
        icmp_types = {
            0: "Echo Reply",
            3: "Destination Unreachable",
            4: "Source Quench",
            5: "Redirect",
            8: "Echo Request",
            9: "Router Advertisement",
            10: "Router Solicitation",
            11: "Time Exceeded",
            12: "Parameter Problem",
            13: "Timestamp",
            14: "Timestamp Reply",
            15: "Information Request",
            16: "Information Reply",
            17: "Address Mask Request",
            18: "Address Mask Reply"
        }
        return icmp_types.get(icmp_type, "Unknown")
    
    def _get_icmpv6_type_name(self, icmpv6_type):
        """獲取ICMPv6類型名稱"""
        icmpv6_types = {
            1: "Destination Unreachable",
            2: "Packet Too Big",
            3: "Time Exceeded",
            4: "Parameter Problem",
            128: "Echo Request",
            129: "Echo Reply",
            130: "Multicast Listener Query",
            131: "Multicast Listener Report",
            132: "Multicast Listener Done",
            133: "Router Solicitation",
            134: "Router Advertisement",
            135: "Neighbor Solicitation",
            136: "Neighbor Advertisement",
            137: "Redirect Message"
        }
        return icmpv6_types.get(icmpv6_type, "Unknown")
    
    def _get_tcp_flags_string(self, tcp_pkt):
        """獲取TCP標誌字串"""
        flags = []
        if tcp_pkt.has_flags(tcp.TCP_FIN):
            flags.append("FIN")
        if tcp_pkt.has_flags(tcp.TCP_SYN):
            flags.append("SYN")
        if tcp_pkt.has_flags(tcp.TCP_RST):
            flags.append("RST")
        if tcp_pkt.has_flags(tcp.TCP_PSH):
            flags.append("PSH")
        if tcp_pkt.has_flags(tcp.TCP_ACK):
            flags.append("ACK")
        if tcp_pkt.has_flags(tcp.TCP_URG):
            flags.append("URG")
        if tcp_pkt.has_flags(tcp.TCP_ECE):
            flags.append("ECE")
        if tcp_pkt.has_flags(tcp.TCP_CWR):
            flags.append("CWR")
        return ", ".join(flags)
    
    def _get_dhcp_message_type(self, dhcp_pkt):
        """獲取DHCP訊息類型"""
        if not dhcp_pkt or not dhcp_pkt.options:
            return None
            
        for opt in dhcp_pkt.options.option_list:
            if opt.tag == 53:  # DHCP Message Type
                msg_type = ord(opt.value)
                types = {
                    1: "DISCOVER",
                    2: "OFFER",
                    3: "REQUEST",
                    4: "DECLINE",
                    5: "ACK",
                    6: "NAK",
                    7: "RELEASE",
                    8: "INFORM"
                }
                return types.get(msg_type, "UNKNOWN")
        return None

    def _get_ethertype_name(self, ethertype):
        """獲取乙太網類型的名稱"""
        ethertype_map = {
            ether_types.ETH_TYPE_IP: "IPv4",
            ether_types.ETH_TYPE_ARP: "ARP",
            ether_types.ETH_TYPE_IPV6: "IPv6",
            ether_types.ETH_TYPE_LLDP: "LLDP",
            ether_types.ETH_TYPE_SLOW: "SLOW",
            ether_types.ETH_TYPE_8021Q: "VLAN",
            ether_types.ETH_TYPE_MPLS: "MPLS",
            ether_types.ETH_TYPE_8021AD: "802.1ad",
            0x0842: "Wake-on-LAN",
            0x22F0: "AVTP",
            0x22F3: "TRILL",
            0x8035: "RARP",
            0x8102: "SLPP",
            0x8808: "Ethernet Flow Control",
            0x8847: "MPLS unicast",
            0x8848: "MPLS multicast",
            0x8863: "PPPoE Discovery",
            0x8864: "PPPoE Session",
            0x888E: "EAP over LAN",
            0x88A8: "Provider Bridging",
            0x88CC: "LLDP",
            0x88E5: "MAC Security",
            0x88F7: "PTP"
        }
        return ethertype_map.get(ethertype, "Unknown")
        
    def _get_ip_proto_name(self, proto):
        """獲取IP協議編號的名稱"""
        proto_map = {
            1: "ICMP",
            2: "IGMP",
            6: "TCP",
            17: "UDP",
            50: "ESP",
            51: "AH",
            58: "ICMPv6",
            89: "OSPF",
            132: "SCTP"
        }
        return proto_map.get(proto, "Unknown")
    
    def _get_port_name(self, port):
        """獲取常見端口號的名稱"""
        port_map = {
            20: "FTP Data",
            21: "FTP Control",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            67: "DHCP Server",
            68: "DHCP Client",
            69: "TFTP",
            80: "HTTP",
            110: "POP3",
            119: "NNTP",
            123: "NTP",
            143: "IMAP",
            161: "SNMP",
            162: "SNMP Trap",
            179: "BGP",
            389: "LDAP",
            443: "HTTPS",
            465: "SMTPS",
            514: "Syslog",
            636: "LDAPS",
            993: "IMAPS",
            995: "POP3S",
            1433: "MS SQL",
            1521: "Oracle",
            1812: "RADIUS Auth",
            1813: "RADIUS Acct",
            3306: "MySQL",
            3389: "RDP",
            5060: "SIP",
            5061: "SIPS",
            5432: "PostgreSQL",
            6633: "OpenFlow",
            6653: "OpenFlow"
        }
        return port_map.get(port, "")
    