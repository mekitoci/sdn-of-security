#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
import time

class StatsCollector(object):
    """統計數據收集工具：收集交換機的各種統計數據
    
    此模塊實現了高級的統計數據收集功能，包括：
    1. 流表統計
    2. 端口統計
    3. 表格統計
    4. 計量表統計
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
        self.stats_reply_handlers = {}  # 統計回復處理器映射
        self.flow_stats = {}  # 流表統計 {dpid: [stats]}
        self.port_stats = {}  # 端口統計 {dpid: {port_no: stats}}
        self.last_request_time = {}  # 最後一次請求時間 {dpid: timestamp}
    
    def request_stats(self, datapath):
        """從交換機請求統計數據"""
        try:
            self._request_flow_stats(datapath)
            self._request_port_stats(datapath)
            self._request_table_stats(datapath)
            self.last_request_time[datapath.id] = time.time()
        except Exception as e:
            self.app.logger.error("請求統計數據時發生錯誤: %s", e)
    
    def _request_flow_stats(self, datapath):
        """請求流表統計"""
        parser = datapath.ofproto_parser
        ofp = datapath.ofproto
        
        req = parser.OFPFlowStatsRequest(
            datapath=datapath,
            table_id=ofp.OFPTT_ALL,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            match=parser.OFPMatch()
        )
        datapath.send_msg(req)
    
    def _request_port_stats(self, datapath):
        """請求端口統計"""
        parser = datapath.ofproto_parser
        ofp = datapath.ofproto
        
        req = parser.OFPPortStatsRequest(
            datapath=datapath,
            port_no=ofp.OFPP_ANY
        )
        datapath.send_msg(req)
    
    def _request_table_stats(self, datapath):
        """請求表格統計"""
        parser = datapath.ofproto_parser
        
        req = parser.OFPTableStatsRequest(datapath)
        datapath.send_msg(req)
    
    def register_stats_reply_handler(self, event_type, handler):
        """註冊統計回復處理器"""
        self.stats_reply_handlers[event_type] = handler
    
    def process_flow_stats(self, ev):
        """處理流表統計回復"""
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        
        # 更新流表統計
        self.flow_stats[dpid] = msg.body
        
        # 處理流量異常檢測
        if hasattr(self.app, 'anomaly_detector'):
            for stat in msg.body:
                # 提取流標識資訊
                match = stat.match
                if 'ipv4_src' in match and 'ipv4_dst' in match:
                    flow_id = f"{match['ipv4_src']}->{match['ipv4_dst']}"
                    
                    # 添加協議資訊
                    if 'ip_proto' in match:
                        proto_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
                        proto = proto_map.get(match['ip_proto'], str(match['ip_proto']))
                        flow_id += f":{proto}"
                        
                        # 添加端口資訊 (TCP/UDP)
                        if match['ip_proto'] == 6 and 'tcp_src' in match and 'tcp_dst' in match:
                            flow_id += f"/{match['tcp_src']}-{match['tcp_dst']}"
                        elif match['ip_proto'] == 17 and 'udp_src' in match and 'udp_dst' in match:
                            flow_id += f"/{match['udp_src']}-{match['udp_dst']}"
                    
                    # 分析流量是否異常
                    self.app.anomaly_detector.analyze_flow(
                        dpid,
                        flow_id,
                        stat.packet_count,
                        stat.byte_count,
                        stat.duration_sec,
                        stat.duration_nsec
                    )
        
        # 調用自定義處理器
        if ofp_event.EventOFPFlowStatsReply in self.stats_reply_handlers:
            self.stats_reply_handlers[ofp_event.EventOFPFlowStatsReply](ev)
    
    def process_port_stats(self, ev):
        """處理端口統計回復"""
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        
        # 更新端口統計
        if dpid not in self.port_stats:
            self.port_stats[dpid] = {}
            
        for stat in msg.body:
            self.port_stats[dpid][stat.port_no] = stat
        
        # 調用自定義處理器
        if ofp_event.EventOFPPortStatsReply in self.stats_reply_handlers:
            self.stats_reply_handlers[ofp_event.EventOFPPortStatsReply](ev)
    
    def process_table_stats(self, ev):
        """處理表格統計回復"""
        # 調用自定義處理器
        if ofp_event.EventOFPTableStatsReply in self.stats_reply_handlers:
            self.stats_reply_handlers[ofp_event.EventOFPTableStatsReply](ev)
    
    def get_flow_stats(self, dpid=None):
        """獲取流表統計數據"""
        if dpid is None:
            return self.flow_stats
        return self.flow_stats.get(dpid, [])
    
    def get_port_stats(self, dpid=None, port_no=None):
        """獲取端口統計數據"""
        if dpid is None:
            return self.port_stats
        
        if port_no is None:
            return self.port_stats.get(dpid, {})
        
        return self.port_stats.get(dpid, {}).get(port_no, None)
    
    def get_port_speed(self, dpid, port_no):
        """計算端口速率 (bps)"""
        if dpid not in self.port_stats or port_no not in self.port_stats[dpid]:
            return 0, 0
        
        curr_stat = self.port_stats[dpid][port_no]
        last_request_time = self.last_request_time.get(dpid, time.time())
        curr_time = time.time()
        
        # 如果是第一次統計或時間差太小，則返回 0
        if not hasattr(curr_stat, '_last') or curr_time - last_request_time < 1:
            return 0, 0
        
        last_stat = curr_stat._last
        interval = curr_time - last_request_time
        
        # 計算速率
        rx_speed = (curr_stat.rx_bytes - last_stat.rx_bytes) * 8 / interval
        tx_speed = (curr_stat.tx_bytes - last_stat.tx_bytes) * 8 / interval
        
        return rx_speed, tx_speed
