#!/usr/bin/env python
# -*- coding: utf-8 -*-

class FlowUtils(object):
    """流表操作工具：提供流表操作的輔助功能
    
    此模塊實現了流表操作的通用功能，包括：
    1. 生成流表項
    2. 解析流表項
    3. 刪除流表項
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
    
    def create_match(self, datapath, fields):
        """創建匹配條件
        
        參數:
            datapath: 交換機
            fields: 匹配欄位 (dict)
                可包含: eth_type, eth_src, eth_dst, ipv4_src, ipv4_dst,
                ip_proto, tcp_src, tcp_dst, udp_src, udp_dst 等
        
        返回:
            parser.OFPMatch 對象
        """
        parser = datapath.ofproto_parser
        return parser.OFPMatch(**fields)
    
    def create_flow_mod(self, datapath, priority, match, actions, 
                        command=None, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """創建流表修改消息
        
        參數:
            datapath: 交換機
            priority: 優先級
            match: 匹配條件 (parser.OFPMatch)
            actions: 動作列表
            command: 命令 (ADD, MODIFY, DELETE)
            buffer_id: 緩衝ID
            idle_timeout: 閒置超時
            hard_timeout: 硬超時
        
        返回:
            parser.OFPFlowMod 對象
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        if command is None:
            command = ofproto.OFPFC_ADD
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            return parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
                command=command,
                idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
        else:
            return parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
                command=command,
                idle_timeout=idle_timeout,
                hard_timeout=hard_timeout
            )
    
    def delete_flow(self, datapath, match, priority=0):
        """刪除指定流表項
        
        參數:
            datapath: 交換機
            match: 匹配條件
            priority: 優先級
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        mod = parser.OFPFlowMod(
            datapath=datapath,
            match=match,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=priority
        )
        datapath.send_msg(mod)
    
    def delete_all_flows(self, datapath):
        """刪除所有流表項
        
        參數:
            datapath: 交換機
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 刪除所有流表項
        match = parser.OFPMatch()
        self.delete_flow(datapath, match)
        
        # 安裝 table-miss 流表項
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.app.add_flow(datapath, 0, match, actions)
    
    def create_meter_band(self, datapath, rate, burst_size=None, type="DROP"):
        """創建計量器頻帶
        
        參數:
            datapath: 交換機
            rate: 速率 (kbps)
            burst_size: 突發大小
            type: 頻帶類型 ("DROP" 或 "DSCP_REMARK")
        
        返回:
            OFPMeterBand* 對象
        """
        parser = datapath.ofproto_parser
        
        if burst_size is None:
            burst_size = rate // 10
        
        if type == "DROP":
            return parser.OFPMeterBandDrop(rate=rate, burst_size=burst_size)
        elif type == "DSCP_REMARK":
            return parser.OFPMeterBandDscpRemark(rate=rate, burst_size=burst_size, prec_level=1)
        else:
            raise ValueError(f"不支持的計量器頻帶類型: {type}")
    
    def create_meter(self, datapath, meter_id, bands, flags=None):
        """創建計量器
        
        參數:
            datapath: 交換機
            meter_id: 計量器ID
            bands: 頻帶列表
            flags: 標誌
        
        返回:
            OFPMeterMod 對象
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        if flags is None:
            flags = ofproto.OFPMF_KBPS
        
        return parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=flags,
            meter_id=meter_id,
            bands=bands
        )
    
    def delete_meter(self, datapath, meter_id):
        """刪除計量器
        
        參數:
            datapath: 交換機
            meter_id: 計量器ID
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        mod = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_DELETE,
            meter_id=meter_id
        )
        datapath.send_msg(mod)
    
    def parse_flow_stats(self, stat):
        """解析流表統計數據
        
        參數:
            stat: 流表統計數據
        
        返回:
            解析後的流表統計信息 (dict)
        """
        match = stat.match
        
        # 提取基本信息
        flow_info = {
            'table_id': stat.table_id,
            'duration_sec': stat.duration_sec,
            'duration_nsec': stat.duration_nsec,
            'priority': stat.priority,
            'idle_timeout': stat.idle_timeout,
            'hard_timeout': stat.hard_timeout,
            'packet_count': stat.packet_count,
            'byte_count': stat.byte_count,
            'match': {}
        }
        
        # 提取匹配條件
        for field in match:
            flow_info['match'][field] = match[field]
        
        return flow_info
    
    def get_flow_id(self, stat):
        """生成流標識
        
        參數:
            stat: 流表統計數據
        
        返回:
            流標識字符串
        """
        match = stat.match
        
        # 提取以太網類型
        eth_type = match.get('eth_type', 'unknown')
        
        if eth_type == 0x0800:  # IPv4
            # 提取IP地址
            src_ip = match.get('ipv4_src', 'unknown')
            dst_ip = match.get('ipv4_dst', 'unknown')
            
            # 提取協議
            if 'ip_proto' in match:
                ip_proto = match['ip_proto']
                proto_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
                proto = proto_map.get(ip_proto, str(ip_proto))
                
                # 提取端口
                if ip_proto == 6:  # TCP
                    src_port = match.get('tcp_src', 'unknown')
                    dst_port = match.get('tcp_dst', 'unknown')
                    return f"{src_ip}:{src_port}->{dst_ip}:{dst_port}[TCP]"
                elif ip_proto == 17:  # UDP
                    src_port = match.get('udp_src', 'unknown')
                    dst_port = match.get('udp_dst', 'unknown')
                    return f"{src_ip}:{src_port}->{dst_ip}:{dst_port}[UDP]"
                else:
                    return f"{src_ip}->{dst_ip}[{proto}]"
            else:
                return f"{src_ip}->{dst_ip}[IPv4]"
        elif eth_type == 0x0806:  # ARP
            src_ip = match.get('arp_spa', 'unknown')
            dst_ip = match.get('arp_tpa', 'unknown')
            return f"{src_ip}->{dst_ip}[ARP]"
        else:
            # 使用MAC地址
            src_mac = match.get('eth_src', 'unknown')
            dst_mac = match.get('eth_dst', 'unknown')
            return f"{src_mac}->{dst_mac}[0x{eth_type:04x}]"
