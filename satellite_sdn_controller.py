#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
衛星 SDN 控制器 - 基於 Ryu 框架 (簡化版)
類似 simple_switch_13，專門處理衛星網路的基本轉發功能
"""

import json
import time
from datetime import datetime

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.topology import event


class SatelliteSDNController(app_manager.RyuApp):
    """衛星 SDN 控制器 - 簡化版，專注於基本轉發功能"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(SatelliteSDNController, self).__init__(*args, **kwargs)
        
        # MAC 學習表：{dpid: {mac: port}}
        self.mac_to_port = {}
        
        # 衛星交換機識別
        self.satellite_switches = set()
        
        # 交換機信息
        self.switches = {}
        
        self.logger.info("=== 衛星 SDN 控制器啟動 (簡化版) ===")
        self.logger.info("基於 simple_switch_13 架構，專注於基本轉發功能")
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """處理交換機連接事件 - 安裝預設流表"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        
        self.logger.info(f"交換機連接: DPID={dpid}")
        
        # 記錄交換機信息
        self.switches[dpid] = {
            'datapath': datapath,
            'connected_time': time.time(),
            'is_satellite': self._is_satellite_switch(dpid)
        }
        
        # 標記衛星交換機
        if self.switches[dpid]['is_satellite']:
            self.satellite_switches.add(dpid)
            self.logger.info(f"衛星交換機 {dpid} 加入網路")
        
        # 安裝表缺失流表：發送到控制器
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                        ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info(f"預設流表已安裝到交換機 {dpid}")
    
    def _is_satellite_switch(self, dpid):
        """判斷是否為衛星交換機 - 可根據需要修改判斷邏輯"""
        # 簡化實現：假設所有交換機都是衛星交換機
        # 實際使用時可根據 DPID 範圍或命名規則判斷
        return True
    
    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        """添加流表項"""
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
    def _packet_in_handler(self, ev):
        """處理 Packet-In 事件 - 核心轉發邏輯"""
        # 如果事件來源不匹配，忽略
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                            ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        
        # 解析封包
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        # 忽略 LLDP 封包
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        dst = eth.dst
        src = eth.src
        
        # 初始化 MAC 表
        self.mac_to_port.setdefault(dpid, {})
        
        self.logger.debug("packet in dpid=%s src=%s dst=%s in_port=%s", 
                         dpid, src, dst, in_port)
        
        # MAC 學習：記錄來源 MAC 和端口的對應關係
        self.mac_to_port[dpid][src] = in_port
        
        # 查找目標 MAC 對應的輸出端口
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            # 未知目的地址，洪氾
            out_port = ofproto.OFPP_FLOOD
        
        # 構建動作列表
        actions = [parser.OFPActionOutput(out_port)]
        
        # 如果我們知道輸出端口，安裝流表避免下次 packet_in
        if out_port != ofproto.OFPP_FLOOD:
            # 驗證端口不是輸入端口（避免迴圈）
            if out_port == in_port:
                self.logger.info("out port is same as in_port. drop packet")
                return
            
            # 安裝流表
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            
            # 驗證是否有有效的 buffer_id，如果有則一併處理緩衝的封包
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        # 發送封包
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    # 拓撲變化處理（可選）
    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        """交換機進入事件"""
        switch = ev.switch
        dpid = switch.dp.id
        self.logger.info(f"拓撲變化: 交換機 {dpid} 加入")
    
    @set_ev_cls(event.EventSwitchLeave)
    def switch_leave_handler(self, ev):
        """交換機離開事件"""
        switch = ev.switch
        dpid = switch.dp.id
        self.logger.info(f"拓撲變化: 交換機 {dpid} 離開")
        
        # 清理相關資料
        if dpid in self.mac_to_port:
            del self.mac_to_port[dpid]
        if dpid in self.switches:
            del self.switches[dpid]
        if dpid in self.satellite_switches:
            self.satellite_switches.remove(dpid)
    
    @set_ev_cls(event.EventLinkAdd)
    def link_add_handler(self, ev):
        """連接添加事件"""
        link = ev.link
        self.logger.info(f"拓撲變化: 連接添加 {link.src.dpid} <-> {link.dst.dpid}")
    
    @set_ev_cls(event.EventLinkDelete)
    def link_delete_handler(self, ev):
        """連接刪除事件"""
        link = ev.link
        self.logger.info(f"拓撲變化: 連接刪除 {link.src.dpid} <-> {link.dst.dpid}")
    
    # 輔助方法
    def get_satellite_info(self):
        """獲取衛星網路信息"""
        return {
            'total_switches': len(self.switches),
            'satellite_switches': len(self.satellite_switches),
            'satellite_dpids': list(self.satellite_switches),
            'mac_tables': dict(self.mac_to_port)
        }


# 用於測試的獨立運行
if __name__ == '__main__':
    from ryu.cmd import manager
    import sys
    
    # 設置日誌級別
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 啟動應用
    sys.argv.append('satellite_sdn_controller.py')
    sys.argv.append('--verbose')
    manager.main() 