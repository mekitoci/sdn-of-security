#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
衛星 SDN 控制器 - 基於 Ryu 框架 (簡化版)
類似 simple_switch_13，專門處理衛星網路的基本轉發功能
"""

import json
import time
import threading
import math
from datetime import datetime, timedelta

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.topology import event, api
from ryu.topology.api import get_switch, get_link
from ryu.lib import hub
from ryu.app.wsgi import ControllerBase, WSGIApplication, route, Response
from ryu.app.rest_topology import TopologyAPI
from ryu.topology.api import get_switch, get_link, get_host
import eventlet
import json as json_module


class SatelliteSDNController(app_manager.RyuApp):
    """衛星 SDN 控制器 - 增強版，支援低軌衛星網路功能"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    # 聲明依賴的 Ryu 應用
    _CONTEXTS = {"wsgi": WSGIApplication}
    
    def __init__(self, *args, **kwargs):
        super(SatelliteSDNController, self).__init__(*args, **kwargs)

        # 初始化 WSGI 應用
        wsgi = kwargs["wsgi"]
        wsgi.register(SatelliteWebController, {"satellite_controller": self})
        
        # 確保 Web 服務在 8080 端口啟動
        self.logger.info("Web 服務註冊完成，端口: 8080")
        self.logger.info("可訪問: http://localhost:8080/satellite/")
        
        # MAC 學習表：{dpid: {mac: port}}
        self.mac_to_port = {}
        
        # 衛星交換機識別
        self.satellite_switches = set()
        
        # 交換機信息
        self.switches = {}
        
        # 衛星位置和地面站信息
        self.satellite_positions = {}  # {dpid: position_info}
        self.ground_stations = {}  # {gs_name: gs_info}
        self.connectivity_matrix = {}  # {dpid: [visible_gs_list]}

        # 地面站連接狀態追蹤
        self.ground_station_status = {}  # {gs_name: {dpid: True/False}}

        # 網路狀態信息（從 topology API 獲取）
        self.network_graph = {}  # 網路拓撲圖
        
        # 新增：QoS 和 Meter 表管理
        self.qos_policies = {}  # QoS 策略
        self.meter_tables = {}  # Meter 表管理
        
        # 新增：Group 表管理（多路徑）
        self.group_tables = {}  # Group 表管理
        self.multipath_routes = {}  # 多路徑路由表
        
        # 端口狀態監控
        self.port_status = {}  # 端口狀態信息
        
        self.logger.info("=== 衛星 SDN 控制器啟動 ===")
        self.logger.info("支援：流表控制、拓撲發現、QoS、多路徑、Web GUI")
    
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
            "datapath": datapath,
            "connected_time": time.time(),
            "is_satellite": self._is_satellite_switch(dpid),
        }
        
        # 標記衛星交換機
        if self.switches[dpid]["is_satellite"]:
            self.satellite_switches.add(dpid)
            self.logger.info(f"衛星交換機 {dpid} 加入網路")
        
        # 安裝表缺失流表：發送到控制器
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info(f"預設流表已安裝到交換機 {dpid}")
    
    def _is_satellite_switch(self, dpid):
        """判斷是否為衛星交換機 - 可根據需要修改判斷邏輯"""
        # 簡化實現：假設所有交換機都是衛星交換機
        # 實際使用時可根據 DPID 範圍或命名規則判斷
        return True
    
    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions,
        buffer_id=None,
        idle_timeout=0,
        hard_timeout=0,
    ):
        """添加流表項"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
                idle_timeout=idle_timeout,
                hard_timeout=hard_timeout,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
                                  idle_timeout=idle_timeout,
                hard_timeout=hard_timeout,
            )
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """處理 Packet-In 事件 - 核心轉發邏輯"""
        # 如果事件來源不匹配，忽略
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug(
                "packet truncated: only %s of %s bytes",
                ev.msg.msg_len,
                ev.msg.total_len,
            )
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]
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
        
        self.logger.debug(
            "packet in dpid=%s src=%s dst=%s in_port=%s", dpid, src, dst, in_port
        )
        
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
        
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
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
        """獲取衛星網路信息（從 topology API 獲取真實數據）"""
        try:
            # 獲取真實拓撲數據
            switches = get_switch(self)
            links = get_link(self)
            hosts = get_host(self)

            return {
                "total_switches": len(self.switches),
                "satellite_switches": len(self.satellite_switches),
                "satellite_dpids": list(self.satellite_switches),
                "mac_tables": dict(self.mac_to_port),
                "topology_switches": [sw.to_dict() for sw in switches],
                "topology_links": [link.to_dict() for link in links],
                "topology_hosts": [host.to_dict() for host in hosts],
            }
        except Exception as e:
            self.logger.warning(f"無法獲取拓撲數據: {e}")
            return {
                "total_switches": len(self.switches),
                "satellite_switches": len(self.satellite_switches),
                "satellite_dpids": list(self.satellite_switches),
                "mac_tables": dict(self.mac_to_port),
                "topology_error": str(e),
            }
    
    def get_network_status(self):
        """獲取網路狀態（包含拓撲和位置信息）"""
        topology_info = self._get_topology_info()
        
        return {
            'timestamp': time.time(),
            'switches': {
                'total': len(self.switches),
                'satellite_switches': len(self.satellite_switches),
                'active': len([s for s in self.satellite_switches if s in self.switches]),
                'topology_switches': len(topology_info['switches']),
                'connected_switches': [sw.dp.id for sw in topology_info['switches']],
            },
            'links': {
                'total': len(topology_info['links']),
                'topology_links': len(topology_info['links']),
                'active': len(topology_info['links']),
            },
            'hosts': {
                'total': len(topology_info['hosts']),
                'connected_hosts': len(topology_info['hosts']),
            },
            'qos_policies': len(self.qos_policies),
            'multipath_routes': len(self.multipath_routes),
            'group_tables': sum(len(groups) for groups in self.group_tables.values()),
            'ground_station_connections': self.ground_station_status,
            'satellite_positions': self.satellite_positions,  # 新增：衛星位置信息
            'ground_stations': self.ground_stations           # 新增：地面站信息
        }

    # ==================== 拓撲感知功能 ====================

    def _get_topology_info(self):
        """從 topology API 獲取拓撲信息"""
        try:
            switches = get_switch(self)
            links = get_link(self)
            hosts = get_host(self)

            return {"switches": switches, "links": links, "hosts": hosts}
        except Exception as e:
            self.logger.error(f"獲取拓撲信息失敗: {e}")
            return {"switches": [], "links": [], "hosts": []}
    
    # ==================== 流表控制功能 ====================
    
    def add_topology_based_flows(self, datapath):
        """基於拓撲信息添加流表"""
        topology_info = self._get_topology_info()

        if topology_info["links"]:
            parser = datapath.ofproto_parser
            ofproto = datapath.ofproto
            
            # 為拓撲中的每個鏈路添加基本轉發規則
            for link in topology_info["links"]:
                src_dpid = link.src.dpid
                dst_dpid = link.dst.dpid
                src_port = link.src.port_no

                if datapath.id == src_dpid:
                    # 添加基於目標交換機的轉發規則
                    match = parser.OFPMatch(eth_type=0x0800)
                    actions = [parser.OFPActionOutput(src_port)]

                    self.add_flow(datapath, priority=10, match=match, actions=actions)
                    self.logger.info(
                        f"為交換機 {src_dpid} 端口 {src_port} 添加拓撲流表"
                    )
    
    def update_flow_with_qos(self, dpid, match_fields, output_port, qos_params):
        """使用 QoS 參數更新流表"""
        if dpid not in self.switches:
            return False
        
        datapath = self.switches[dpid]["datapath"]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # 建立 Meter 表項（如果需要）
        meter_id = None
        if "bandwidth_limit" in qos_params:
            meter_id = self._create_meter(datapath, qos_params["bandwidth_limit"])
        
        # 建立動作
        actions = [parser.OFPActionOutput(output_port)]
        instructions = [
            parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)
        ]
        
        # 添加 Meter 指令
        if meter_id:
            instructions.insert(0, parser.OFPInstructionMeter(meter_id))
        
        # 建立 Match
        match = parser.OFPMatch(**match_fields)
        
        # 添加流表
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=20,
            match=match,
            instructions=instructions,
            idle_timeout=qos_params.get("idle_timeout", 300),
            hard_timeout=qos_params.get("hard_timeout", 600),
        )
        datapath.send_msg(mod)
        
        self.logger.info(f"為 DPID {dpid} 添加 QoS 流表，端口: {output_port}")
        return True
    
    # ==================== QoS 和 Meter 表管理 ====================
    
    def _calculate_link_quality(self, distance):
        """根據距離計算鏈路品質"""
        # 簡化的品質計算模型
        max_distance = 2000  # km
        min_quality = 0.1
        max_quality = 1.0
        
        # 距離越遠，品質越差
        quality_score = max_quality - (distance / max_distance) * (
            max_quality - min_quality
        )
        quality_score = max(min_quality, min(max_quality, quality_score))
        
        # 計算延遲（光速傳播）
        speed_of_light = 299792.458  # km/ms
        latency = (distance * 2) / speed_of_light  # 往返延遲 ms
        
        # 計算可用帶寬（簡化模型）
        max_bandwidth = 1000  # Mbps
        bandwidth = int(max_bandwidth * quality_score)
        
        return {
            "score": quality_score,
            "distance": distance,
            "latency": latency,
            "bandwidth": bandwidth,
            "jitter": latency * 0.1,  # 簡化的抖動模型
            "packet_loss": (1 - quality_score) * 0.05,  # 簡化的丟包率
        }
    
    def _update_link_quality(self):
        """更新所有鏈路的品質信息"""
        for link_key, quality in list(self.link_quality.items()):
            parts = link_key.split("-")
            if len(parts) == 2:
                sat_id = int(parts[0].replace("sat", ""))
                gs_id = parts[1].replace("gs", "")
                
                if sat_id in self.satellite_positions and gs_id in self.ground_stations:
                    sat_pos = self.satellite_positions[sat_id]
                    gs_pos = self.ground_stations[gs_id]
                    distance = self._calculate_distance(sat_pos, gs_pos)
                    
                    # 更新品質
                    new_quality = self._calculate_link_quality(distance)
                    self.link_quality[link_key] = new_quality
                    
                    # 如果品質變化顯著，更新QoS
                    if abs(new_quality["score"] - quality["score"]) > 0.1:
                        self._update_qos_for_link(sat_id, gs_id, new_quality)
    
    def _setup_qos_for_link(self, sat_id, gs_id, quality):
        """為鏈路建立QoS策略"""
        link_key = f"sat{sat_id}-gs{gs_id}"
        
        qos_policy = {
            "bandwidth_limit": quality["bandwidth"],  # Mbps
            "priority": int(quality["score"] * 10),
            "max_latency": quality["latency"] + 100,  # ms
            "created_time": time.time(),
        }
        
        self.qos_policies[link_key] = qos_policy
        
        # 如果交換機已連接，立即應用QoS
        if sat_id in self.switches:
            self._apply_qos_policy(sat_id, qos_policy)
        
        self.logger.info(f"為鏈路 {link_key} 建立QoS策略: {qos_policy}")
    
    def _update_qos_for_link(self, sat_id, gs_id, quality):
        """更新鏈路QoS策略"""
        link_key = f"sat{sat_id}-gs{gs_id}"
        
        if link_key in self.qos_policies:
            old_policy = self.qos_policies[link_key]
            
            # 更新QoS參數
            old_policy["bandwidth_limit"] = quality["bandwidth"]
            old_policy["priority"] = int(quality["score"] * 10)
            old_policy["max_latency"] = quality["latency"] + 100
            old_policy["updated_time"] = time.time()
            
            # 重新應用QoS
            if sat_id in self.switches:
                self._apply_qos_policy(sat_id, old_policy)
            
            self.logger.debug(f"更新鏈路 {link_key} QoS策略")
    
    def _cleanup_qos_for_link(self, sat_id, gs_id):
        """清理鏈路QoS策略"""
        link_key = f"sat{sat_id}-gs{gs_id}"
        
        if link_key in self.qos_policies:
            del self.qos_policies[link_key]
        
        # 移除相關 Meter 表項
        if sat_id in self.switches:
            self._remove_meter_for_link(sat_id, gs_id)
        
        self.logger.info(f"清理鏈路 {link_key} QoS策略")
    
    def _create_meter(self, datapath, bandwidth_mbps):
        """建立 Meter 表項"""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # 生成 Meter ID
        meter_id = len(self.meter_tables.get(datapath.id, {})) + 1
        
        # 建立 Meter Bands
        bands = [
            parser.OFPMeterBandDrop(
                rate=bandwidth_mbps * 1000, burst_size=bandwidth_mbps * 100
            )
        ]
        
        # 建立 Meter Mod
        mod = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=ofproto.OFPMF_KBPS,
            meter_id=meter_id,
            bands=bands,
        )
        datapath.send_msg(mod)
        
        # 記錄 Meter 表
        if datapath.id not in self.meter_tables:
            self.meter_tables[datapath.id] = {}
        self.meter_tables[datapath.id][meter_id] = {
            "bandwidth": bandwidth_mbps,
            "created_time": time.time(),
        }
        
        return meter_id
    
    def _apply_qos_policy(self, dpid, qos_policy):
        """應用QoS策略到交換機"""
        if dpid not in self.switches:
            return
        
        datapath = self.switches[dpid]["datapath"]
        
        # 建立相應的流表和Meter表
        # 這裡可以根據具體需求實現詳細的QoS策略
        self.logger.debug(f"應用QoS策略到交換機 {dpid}")
    
    def _remove_meter_for_link(self, sat_id, gs_id):
        """移除鏈路相關的Meter表項"""
        if sat_id not in self.switches:
            return
        
        datapath = self.switches[sat_id]["datapath"]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # 移除所有Meter（簡化實現）
        if sat_id in self.meter_tables:
            for meter_id in list(self.meter_tables[sat_id].keys()):
                mod = parser.OFPMeterMod(
                    datapath=datapath, command=ofproto.OFPMC_DELETE, meter_id=meter_id
                )
                datapath.send_msg(mod)
            
            del self.meter_tables[sat_id]
        
        self.logger.debug(f"移除衛星 {sat_id} 的Meter表項")
    
    # ==================== 端口狀態監控 ====================
    
    @set_ev_cls(event.EventPortAdd)
    def port_add_handler(self, ev):
        """端口添加事件處理"""
        port = ev.port
        dpid = port.dpid
        port_no = port.port_no
        
        self.logger.info(f"端口添加: DPID={dpid}, Port={port_no}")
        
        # 記錄端口狀態
        if dpid not in self.port_status:
            self.port_status[dpid] = {}
        
        self.port_status[dpid][port_no] = {
            "status": "UP",
            "config": port.config,
            "state": port.state,
            "add_time": time.time(),
        }
        
        # 如果是衛星交換機，可能需要重新計算路由
        if dpid in self.satellite_switches:
            self.logger.info(f"衛星 {dpid} 新增端口 {port_no}，觸發路由重算")
            self._recalculate_routing_for_satellite(dpid)
    
    @set_ev_cls(event.EventPortDelete)
    def port_delete_handler(self, ev):
        """端口刪除事件處理"""
        port = ev.port
        dpid = port.dpid
        port_no = port.port_no
        
        self.logger.info(f"端口刪除: DPID={dpid}, Port={port_no}")
        
        # 更新端口狀態
        if dpid in self.port_status and port_no in self.port_status[dpid]:
            self.port_status[dpid][port_no]["status"] = "DOWN"
            self.port_status[dpid][port_no]["delete_time"] = time.time()
        
        # 如果是衛星交換機，需要清理相關路由和QoS
        if dpid in self.satellite_switches:
            self.logger.info(f"衛星 {dpid} 端口 {port_no} 離線，清理相關配置")
            self._cleanup_port_configurations(dpid, port_no)
    
    @set_ev_cls(event.EventPortModify)
    def port_modify_handler(self, ev):
        """端口修改事件處理"""
        port = ev.port
        dpid = port.dpid
        port_no = port.port_no
        
        self.logger.debug(f"端口修改: DPID={dpid}, Port={port_no}, State={port.state}")
        
        # 更新端口狀態
        if dpid in self.port_status and port_no in self.port_status[dpid]:
            old_state = self.port_status[dpid][port_no].get("state", 0)
            self.port_status[dpid][port_no]["state"] = port.state
            self.port_status[dpid][port_no]["modify_time"] = time.time()
            
            # 檢查是否為重要狀態變化
            if old_state != port.state:
                self._handle_port_state_change(dpid, port_no, old_state, port.state)
    
    def _recalculate_routing_for_satellite(self, sat_id):
        """為衛星重新計算路由"""
        # 簡化實現：重新建立所有可用鏈路的流表
        if sat_id in self.satellite_positions:
            for gs_id in self.ground_stations:
                link_key = f"sat{sat_id}-gs{gs_id}"
                if link_key in self.link_quality:
                    self._update_flows_for_new_link(sat_id, gs_id)
    
    def _cleanup_port_configurations(self, dpid, port_no):
        """清理端口相關配置"""
        # 清理與此端口相關的流表
        if dpid in self.switches:
            datapath = self.switches[dpid]["datapath"]
            parser = datapath.ofproto_parser
            ofproto = datapath.ofproto
            
            # 刪除輸出到此端口的所有流表
            mod = parser.OFPFlowMod(
                datapath=datapath,
                command=ofproto.OFPFC_DELETE,
                out_port=port_no,
                out_group=ofproto.OFPG_ANY,
            )
            datapath.send_msg(mod)
            
            self.logger.info(f"清理 DPID {dpid} 端口 {port_no} 的流表")
    
    def _handle_port_state_change(self, dpid, port_no, old_state, new_state):
        """處理端口狀態變化"""
        # 檢查鏈路是否從 DOWN 變為 UP 或相反
        from ryu.ofproto.ofproto_v1_3 import OFPPS_LINK_DOWN
        
        was_down = (old_state & OFPPS_LINK_DOWN) != 0
        is_down = (new_state & OFPPS_LINK_DOWN) != 0
        
        if was_down and not is_down:
            # 鏈路恢復
            self.logger.info(f"鏈路恢復: DPID={dpid}, Port={port_no}")
            if dpid in self.satellite_switches:
                self._handle_satellite_link_recovery(dpid, port_no)
        elif not was_down and is_down:
            # 鏈路中斷
            self.logger.info(f"鏈路中斷: DPID={dpid}, Port={port_no}")
            if dpid in self.satellite_switches:
                self._handle_satellite_link_failure(dpid, port_no)
    
    def _handle_satellite_link_recovery(self, sat_id, port_no):
        """處理衛星鏈路恢復"""
        # 重新建立此端口的路由
        self._recalculate_routing_for_satellite(sat_id)
    
    def _handle_satellite_link_failure(self, sat_id, port_no):
        """處理衛星鏈路失效"""
        # 切換到備用路徑（如果有）
        self._activate_backup_routes(sat_id, port_no)
    
    # ==================== Group 表和多路徑管理 ====================
    
    def setup_multipath_group(self, dpid, group_id, output_ports, weights=None):
        """建立多路徑 Group 表"""
        if dpid not in self.switches:
            return False
        
        datapath = self.switches[dpid]["datapath"]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # 建立 Buckets
        buckets = []
        if weights is None:
            weights = [1] * len(output_ports)
        
        for port, weight in zip(output_ports, weights):
            actions = [parser.OFPActionOutput(port)]
            bucket = parser.OFPBucket(weight=weight, actions=actions)
            buckets.append(bucket)
        
        # 建立 Group Mod
        mod = parser.OFPGroupMod(
            datapath=datapath,
            command=ofproto.OFPGC_ADD,
            type_=ofproto.OFPGT_SELECT,  # Load balancing
            group_id=group_id,
            buckets=buckets,
        )
        datapath.send_msg(mod)
        
        # 記錄 Group 表
        if dpid not in self.group_tables:
            self.group_tables[dpid] = {}
        
        self.group_tables[dpid][group_id] = {
            "type": "SELECT",
            "ports": output_ports,
            "weights": weights,
            "created_time": time.time(),
        }

        self.logger.info(
            f"為 DPID {dpid} 建立多路徑 Group {group_id}: ports={output_ports}"
        )
        return True
    
    def setup_failover_group(self, dpid, group_id, primary_port, backup_ports):
        """建立故障轉移 Group 表"""
        if dpid not in self.switches:
            return False
        
        datapath = self.switches[dpid]["datapath"]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # 建立 Buckets（Fast Failover）
        buckets = []
        
        # 主要端口
        actions = [parser.OFPActionOutput(primary_port)]
        watch_port = primary_port
        bucket = parser.OFPBucket(watch_port=watch_port, actions=actions)
        buckets.append(bucket)
        
        # 備用端口
        for backup_port in backup_ports:
            actions = [parser.OFPActionOutput(backup_port)]
            watch_port = backup_port
            bucket = parser.OFPBucket(watch_port=watch_port, actions=actions)
            buckets.append(bucket)
        
        # 建立 Group Mod
        mod = parser.OFPGroupMod(
            datapath=datapath,
            command=ofproto.OFPGC_ADD,
            type_=ofproto.OFPGT_FF,  # Fast Failover
            group_id=group_id,
            buckets=buckets,
        )
        datapath.send_msg(mod)
        
        # 記錄 Group 表
        if dpid not in self.group_tables:
            self.group_tables[dpid] = {}
        
        self.group_tables[dpid][group_id] = {
            "type": "FAST_FAILOVER",
            "primary_port": primary_port,
            "backup_ports": backup_ports,
            "created_time": time.time(),
        }

        self.logger.info(
            f"為 DPID {dpid} 建立故障轉移 Group {group_id}: primary={primary_port}, backup={backup_ports}"
        )
        return True
    
    def _optimize_routing(self):
        """優化路由策略"""
        # 檢查是否需要更新多路徑配置
        for sat_id in self.satellite_switches:
            available_links = []
            
            # 找出所有可用的鏈路
            for link_key, quality in self.link_quality.items():
                if link_key.startswith(f"sat{sat_id}-"):
                    gs_id = link_key.split("-")[1]
                    if quality["score"] > 0.3:  # 品質閾值
                        available_links.append(
                            {"gs_id": gs_id, "quality": quality, "link_key": link_key}
                        )
            
            # 如果有多個可用鏈路，設置多路徑
            if len(available_links) > 1:
                self._setup_multipath_for_satellite(sat_id, available_links)
            elif len(available_links) == 1:
                self._setup_single_path_for_satellite(sat_id, available_links[0])
    
    def _setup_multipath_for_satellite(self, sat_id, available_links):
        """為衛星設置多路徑"""
        if sat_id not in self.switches:
            return
        
        # 按品質排序
        available_links.sort(key=lambda x: x["quality"]["score"], reverse=True)
        
        # 建立權重（基於品質）
        ports = []
        weights = []
        
        for link in available_links[:3]:  # 最多3條路徑
            port = 1  # 簡化實現，實際應該根據地面站映射端口
            weight = int(link["quality"]["score"] * 100)
            
            ports.append(port)
            weights.append(weight)
        
        # 建立多路徑 Group
        group_id = sat_id  # 使用衛星ID作為Group ID
        self.setup_multipath_group(sat_id, group_id, ports, weights)
        
        # 記錄多路徑路由
        self.multipath_routes[sat_id] = {
            "type": "multipath",
            "links": available_links,
            "group_id": group_id,
            "updated_time": time.time(),
        }
    
    def _setup_single_path_for_satellite(self, sat_id, link_info):
        """為衛星設置單一路徑"""
        # 清理多路徑配置（如果存在）
        if sat_id in self.multipath_routes:
            del self.multipath_routes[sat_id]
        
        # 記錄單一路徑
        self.multipath_routes[sat_id] = {
            "type": "single_path",
            "link": link_info,
            "updated_time": time.time(),
        }
    
    def _activate_backup_routes(self, sat_id, failed_port):
        """激活備用路由"""
        if sat_id not in self.multipath_routes:
            return
        
        route_info = self.multipath_routes[sat_id]
        
        if route_info["type"] == "multipath":
            # 從多路徑中移除失效鏈路
            self.logger.info(f"衛星 {sat_id} 端口 {failed_port} 失效，重新配置多路徑")
            # 這裡可以實現更複雜的備用路由邏輯
        else:
            # 單一路徑失效，尋找替代路徑
            self.logger.info(f"衛星 {sat_id} 主要路徑失效，搜尋備用路徑")
            self._find_alternative_route(sat_id)
    
    def _find_alternative_route(self, sat_id):
        """為衛星尋找替代路由"""
        # 檢查其他可用的地面站連接
        for gs_id in self.ground_stations:
            link_key = f"sat{sat_id}-gs{gs_id}"
            if link_key in self.link_quality:
                quality = self.link_quality[link_key]
                if quality["score"] > 0.2:  # 降低品質要求
                    self.logger.info(f"找到衛星 {sat_id} 的替代路徑: {gs_id}")
                    self._setup_single_path_for_satellite(
                        sat_id,
                        {"gs_id": gs_id, "quality": quality, "link_key": link_key},
                    )
                    return True
        
        self.logger.warning(f"未找到衛星 {sat_id} 的替代路徑")
        return False
    
    # ==================== API 接口和狀態查詢 ====================
    
    def get_satellite_details(self, sat_id):
        """獲取特定衛星的詳細資訊"""
        if sat_id not in self.satellite_switches:
            return None
        
        # 找出與此衛星相關的鏈路
        related_links = {}
        for link_key, quality in self.link_quality.items():
            if link_key.startswith(f"sat{sat_id}-"):
                related_links[link_key] = quality
        
        # 找出相關的QoS策略
        related_qos = {}
        for qos_key, policy in self.qos_policies.items():
            if qos_key.startswith(f"sat{sat_id}-"):
                related_qos[qos_key] = policy
        
        return {
            "satellite_id": sat_id,
            "position": self.satellite_positions.get(sat_id, {}),
            "switch_info": self.switches.get(sat_id, {}),
            "port_status": self.port_status.get(sat_id, {}),
            "active_links": related_links,
            "qos_policies": related_qos,
            "routing": self.multipath_routes.get(sat_id, {}),
            "group_tables": self.group_tables.get(sat_id, {}),
        }
    
    def get_link_statistics(self):
        """獲取鏈路統計資訊"""
        if not self.link_quality:
            return {}
        
        qualities = [q["score"] for q in self.link_quality.values()]
        latencies = [q["latency"] for q in self.link_quality.values()]
        bandwidths = [q["bandwidth"] for q in self.link_quality.values()]
        
        return {
            "total_links": len(self.link_quality),
            "quality_stats": {
                "avg": sum(qualities) / len(qualities),
                "min": min(qualities),
                "max": max(qualities),
            },
            "latency_stats": {
                "avg": sum(latencies) / len(latencies),
                "min": min(latencies),
                "max": max(latencies),
            },
            "bandwidth_stats": {
                "avg": sum(bandwidths) / len(bandwidths),
                "min": min(bandwidths),
                "max": max(bandwidths),
            },
        }
    
    def force_satellite_handover(self, sat_id, new_gs_id):
        """強制衛星切換到指定地面站"""
        if sat_id not in self.satellite_switches:
            self.logger.error(f"衛星 {sat_id} 不存在")
            return False
        
        if new_gs_id not in self.ground_stations:
            self.logger.error(f"地面站 {new_gs_id} 不存在")
            return False
        
        # 檢查是否有可用連接
        link_key = f"sat{sat_id}-gs{new_gs_id}"
        if link_key not in self.link_quality:
            # 強制建立連接（僅用於測試）
            sat_pos = self.satellite_positions.get(sat_id)
            gs_pos = self.ground_stations.get(new_gs_id)
            
            if sat_pos and gs_pos:
                distance = self._calculate_distance(sat_pos, gs_pos)
                if distance <= 2000:  # 在範圍內
                    self._handle_satellite_enter_coverage(sat_id, new_gs_id, distance)
                    self.logger.info(
                        f"強制建立衛星 {sat_id} 到地面站 {new_gs_id} 的連接"
                    )
                    return True
        
        # 切換到新的地面站
        self._update_flows_for_new_link(sat_id, new_gs_id)
        self.logger.info(f"衛星 {sat_id} 已切換到地面站 {new_gs_id}")
        return True
    
    def update_position_manually(self, sat_id, latitude, longitude, altitude=550):
        """手動更新衛星位置（用於測試）"""
        if sat_id not in self.satellite_switches:
            return False
        
        self.satellite_positions[sat_id] = {
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "velocity": 7.8,
            "last_update": time.time(),
            "manual_update": True,
        }
        
        self.logger.info(f"手動更新衛星 {sat_id} 位置: ({latitude}, {longitude})")
        
        # 重新檢查覆蓋範圍
        self._check_coverage_changes()
        return True
    
    def adjust_simulation_speed(self, speed_multiplier):
        """調整模擬速度"""
        self.position_update_interval = max(1, int(30 / speed_multiplier))
        self.logger.info(
            f"模擬速度調整為 {speed_multiplier}x，更新間隔: {self.position_update_interval}秒"
        )
    
    def export_network_state(self, filename=None):
        """匯出網路狀態到文件"""
        if filename is None:
            filename = f"satellite_network_state_{int(time.time())}.json"
        
        network_state = {
            "timestamp": time.time(),
            "satellite_positions": self.satellite_positions,
            "ground_stations": self.ground_stations,
            "link_quality": self.link_quality,
            "qos_policies": self.qos_policies,
            "multipath_routes": self.multipath_routes,
            "switches": {
                dpid: {
                    "connected_time": info["connected_time"],
                    "is_satellite": info["is_satellite"],
                }
                for dpid, info in self.switches.items()
            },
            "port_status": self.port_status,
        }
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(network_state, f, indent=2, ensure_ascii=False, default=str)
            self.logger.info(f"網路狀態已匯出到: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"匯出網路狀態失敗: {e}")
            return None
    
    def get_performance_metrics(self):
        """獲取性能指標"""
        current_time = time.time()
        
        # 計算系統運行時間
        start_times = [info["connected_time"] for info in self.switches.values()]
        system_uptime = current_time - min(start_times) if start_times else 0
        
        # 計算鏈路切換次數（簡化實現）
        handover_count = len(
            [
                route
                for route in self.multipath_routes.values()
                if "updated_time" in route
            ]
        )
        
        return {
            "system_uptime": system_uptime,
            "active_satellites": len(
                [s for s in self.satellite_switches if s in self.switches]
            ),
            "active_links": len(self.link_quality),
            "handover_count": handover_count,
            "qos_policies_active": len(self.qos_policies),
            "avg_link_quality": (
                sum(q["score"] for q in self.link_quality.values())
                / len(self.link_quality)
                if self.link_quality
                else 0
            ),
            "simulation_performance": {
                "update_interval": self.position_update_interval,
                "last_update": current_time,
            },
        }


# ==================== Web GUI 控制器 ====================


class SatelliteWebController(ControllerBase):
    """衛星 SDN 控制器的 Web GUI"""

    def __init__(self, req, link, data, **config):
        super(SatelliteWebController, self).__init__(req, link, data, **config)
        self.satellite_controller = data["satellite_controller"]

    @route("satellite", "/", methods=["GET"])
    def index(self, req, **kwargs):
        """主頁面 - 衛星網路監控儀表板"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>衛星 SDN 控制器 - 監控儀表板</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .header { 
            background-color: #2c3e50; 
            color: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .card { 
            background: white; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
        }
        .stat-item { 
            text-align: center; 
            padding: 15px; 
            background: #ecf0f1; 
            border-radius: 8px; 
        }
        .stat-number { 
            font-size: 2em; 
            font-weight: bold; 
            color: #3498db; 
        }
        .controls { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        button { 
            padding: 10px 20px; 
            border: none; 
            border-radius: 5px; 
            background-color: #3498db; 
            color: white; 
            cursor: pointer; 
        }
        button:hover { 
            background-color: #2980b9; 
        }
        .refresh-btn { 
            background-color: #27ae60; 
        }
        .export-btn { 
            background-color: #e74c3c; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 10px; 
        }
        th, td { 
            padding: 10px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }
        th { 
            background-color: #f8f9fa; 
        }
        .status-active { 
            color: #27ae60; 
            font-weight: bold; 
        }
        .status-inactive { 
            color: #e74c3c; 
            font-weight: bold; 
        }
        .quality-high { 
            color: #27ae60; 
        }
        .quality-medium { 
            color: #f39c12; 
        }
        .quality-low { 
            color: #e74c3c; 
        }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
                 function exportState() {
             fetch('/export')
                .then(response => response.json())
                .then(data => {
                    alert('網路狀態已匯出: ' + data.filename);
                })
                .catch(error => {
                    alert('匯出失敗: ' + error);
                });
        }
        
        function adjustSpeed() {
                         const speed = prompt('請輸入模擬速度倍數 (例如: 2 表示2倍速):', '1');
             if (speed && !isNaN(speed)) {
                 fetch('/speed', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ speed: parseFloat(speed) })
                })
                .then(response => response.json())
                .then(data => {
                    alert('模擬速度已調整為 ' + speed + 'x');
                });
            }
        }
        
        function updateSatellitePositions(data) {
            // 更新衛星位置信息顯示
            if (data.satellite_positions && Object.keys(data.satellite_positions).length > 0) {
                console.log('收到衛星位置數據:', data.satellite_positions);
                
                // 如果有位置信息容器，更新它
                const positionContainer = document.getElementById('satellite-positions');
                if (positionContainer) {
                    let positionHtml = '<h3>🛰️ 衛星即時位置</h3>';
                    positionHtml += '<table><tr><th>衛星</th><th>緯度</th><th>經度</th><th>高度 (km)</th><th>可見地面站</th></tr>';
                    
                    for (const [dpid, satData] of Object.entries(data.satellite_positions)) {
                        const lat = satData.latitude ? satData.latitude.toFixed(2) : 'N/A';
                        const lon = satData.longitude ? satData.longitude.toFixed(2) : 'N/A';
                        const alt = satData.altitude || 'N/A';
                        const visibleStations = satData.visible_stations || [];
                        
                        const visibleStationsDisplay = visibleStations.length > 0 ? 
                            visibleStations.map(station => getStationDisplayName(station)).join(', ') : 
                            '無可見站點';
                        
                        positionHtml += `
                            <tr>
                                <td>🛰️ ${satData.id || 'SAT-' + dpid}</td>
                                <td>${lat}°</td>
                                <td>${lon}°</td>
                                <td>${alt}</td>
                                <td>${visibleStationsDisplay}</td>
                            </tr>
                        `;
                    }
                    
                    positionHtml += '</table>';
                    positionContainer.innerHTML = positionHtml;
                }
            }
        }
        
        function getStationDisplayName(stationName) {
            // 地面站顯示名稱映射
            const displayNames = {
                'Taipei': '📡 台北',
                'Tokyo': '📡 東京', 
                'Seoul': '📡 首爾',
                'Singapore': '📡 新加坡',
                'Sydney': '📡 雪梨',
                'Mumbai': '📡 孟買',
                'Bangkok': '📡 曼谷',
                'Manila': '📡 馬尼拉',
                'Kuala Lumpur': '📡 吉隆坡',
                'Jakarta': '📡 雅加達',
                'Hanoi': '📡 河內',
                'Phnom Penh': '📡 金邊',
                'Yangon': '📡 仰光'
            };
            
            return displayNames[stationName] || `📡 ${stationName}`;
        }
        
        // 自動刷新
        setInterval(refreshData, 30000); // 每30秒刷新一次
    </script>
</head>
<body>
         <div class="header">
         <h1>🛰️ Satellite-SDN </h1>
     </div>
    
    <div class="stats">
                 <div class="stat-item">
             <div class="stat-number" id="satellite-count">載入中...</div>
             <div>在軌衛星</div>
         </div>
                 <div class="stat-item">
             <div class="stat-number" id="link-count">載入中...</div>
             <div>衛星間鏈路</div>
         </div>
                 <div class="stat-item">
             <div class="stat-number" id="avg-quality">載入中...</div>
             <div>拓撲狀態</div>
         </div>
        <div class="stat-item">
            <div class="stat-number" id="qos-policies">載入中...</div>
            <div>QoS 策略</div>
        </div>
    </div>
    
         <div class="card">
         <h2>🛰️ 衛星狀態</h2>
         <div id="satellite-status">載入中...</div>
     </div>
    
         <div class="card">
         <h2>🛰️↔️🛰️ 衛星間鏈路</h2>
         <div id="link-quality">載入中...</div>
     </div>
    
         <div class="card">
         <h2>📡 地面站狀態</h2>
         <div id="ground-stations">載入中...</div>
     </div>
     
     <div class="card">
         <h2>🛰️ 衛星即時位置</h2>
         <div id="satellite-positions">🔍 等待位置數據...</div>
     </div>
     
     <div class="card">
         <h2>🔌 實際拓撲狀態 (Topology API)</h2>
         <div id="topology-status">載入中...</div>
     </div>
    
    <script>
        // 載入初始數據
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                                 // 更新統計數據
                 document.getElementById('satellite-count').textContent = data.switches ? data.switches.active || 0 : 0;
                 document.getElementById('link-count').textContent = data.links ? data.links.active || 0 : 0;
                 document.getElementById('avg-quality').textContent = 
                     data.topology && data.topology.switches ? data.topology.switches.length + ' 在軌衛星' : '0 在軌衛星';
                 document.getElementById('qos-policies').textContent = data.qos_policies || 0;
                
                                 // 更新衛星狀態表格（基於真實拓撲）
                 let switchHtml = '<table><tr><th>衛星 ID</th><th>軌道狀態</th><th>天線埠</th><th>衛星類型</th></tr>';
                 if (data.topology && data.topology.switches) {
                     for (let sw of data.topology.switches) {
                         const isActive = true; // 如果在 topology 中就是活躍的
                         const portCount = sw.ports ? sw.ports.length : 0;
                         switchHtml += `
                             <tr>
                                 <td>🛰️ SAT-${sw.dpid}</td>
                                 <td class="status-active">🟢 在軌運行</td>
                                 <td>${portCount}</td>
                                 <td>低軌衛星</td>
                             </tr>
                         `;
                     }
                 }
                                   if (!data.topology || !data.topology.switches || data.topology.switches.length === 0) {
                      switchHtml += '<tr><td colspan="4">無在軌衛星</td></tr>';
                  }
                 switchHtml += '</table>';
                 document.getElementById('satellite-status').innerHTML = switchHtml;
                
                                 // 更新衛星間鏈路品質表格（基於真實拓撲鏈路）
                 let linkHtml = '<table><tr><th>衛星間鏈路</th><th>來源衛星</th><th>目標衛星</th><th>來源天線</th><th>目標天線</th></tr>';
                 if (data.topology && data.topology.links && data.topology.links.length > 0) {
                     for (let link of data.topology.links) {
                         linkHtml += `
                             <tr>
                                 <td>🛰️↔️🛰️ SAT-${link.src.dpid}-SAT-${link.dst.dpid}</td>
                                 <td>🛰️ SAT-${link.src.dpid}</td>
                                 <td>🛰️ SAT-${link.dst.dpid}</td>
                                 <td>天線-${link.src.port_no}</td>
                                 <td>天線-${link.dst.port_no}</td>
                             </tr>
                         `;
                     }
                 } else {
                     linkHtml += '<tr><td colspan="5">無衛星間鏈路</td></tr>';
                 }
                 linkHtml += '</table>';
                 document.getElementById('link-quality').innerHTML = linkHtml;
                
                                 // 更新主機狀態（地面站）
                 let hostHtml = '<table><tr><th>地面站</th><th>IP 地址</th><th>MAC 地址</th><th>連接衛星</th><th>連接狀態</th></tr>';
                 
                 // 地面站地理位置映射
                 const groundStationNames = [
                     '📡 台北', '📡 東京', '📡 首爾', '📡 新加坡', 
                     '📡 雪梨', '📡 曼谷', '📡 馬尼拉', '📡 吉隆坡',
                     '📡 雅加達', '📡 河內', '📡 金邊', '📡 仰光'
                 ];
                 
                 if (data.topology && data.topology.hosts && data.topology.hosts.length > 0) {
                     for (let i = 0; i < data.topology.hosts.length; i++) {
                         const host = data.topology.hosts[i];
                         const hostIpv4 = host.ipv4 && host.ipv4.length > 0 ? host.ipv4[0] : 'N/A';
                         const hostMac = host.mac || 'N/A';
                         const hostPort = host.port ? host.port.dpid : 'N/A';
                         const stationName = groundStationNames[i % groundStationNames.length] || `📡 地面站-${i+1}`;
                         
                         // 檢查連接狀態
                         let connectionStatus = '❌ 無連接';
                         
                         // 使用實際的地面站名稱 (taipei, tokyo, seoul, singapore 等)
                         const gsNames = ['taipei', 'tokyo', 'seoul', 'singapore', 'sydney', 'bangkok', 'manila', 'kualalumpur', 'jakarta', 'hanoi', 'phnompenh', 'yangon'];
                         const actualGsName = gsNames[i] || `station_${i}`;
                         
                         if (data.ground_station_connections && data.ground_station_connections[actualGsName]) {
                             const connections = data.ground_station_connections[actualGsName];
                             const connectedSats = Object.entries(connections)
                                 .filter(([dpid, connected]) => connected)
                                 .map(([dpid, connected]) => `SAT-${dpid}`);
                             
                             if (connectedSats.length > 0) {
                                 connectionStatus = `🟢 在區域內 (${connectedSats.join(', ')})`;
                             } else {
                                 connectionStatus = '🔴 不在區域內';
                             }
                         }
                         
                         hostHtml += `
                             <tr>
                                 <td>${stationName}</td>
                                 <td>${hostIpv4}</td>
                                 <td>${hostMac}</td>
                                 <td>🛰️ SAT-${hostPort}</td>
                                 <td>${connectionStatus}</td>
                             </tr>
                         `;
                     }
                 } else {
                     hostHtml += '<tr><td colspan="5">無連接的地面站</td></tr>';
                 }
                 hostHtml += '</table>';
                 document.getElementById('ground-stations').innerHTML = hostHtml;
                
                // 顯示衛星位置信息
                updateSatellitePositions(data);
                
                // 顯示 topology 數據
                if (data.topology && !data.topology.error) {
                    let topoHtml = '<h3>🛰️ 在軌衛星 (' + data.topology.switches.length + ')</h3>';
                    topoHtml += '<table><tr><th>衛星 ID</th><th>天線埠數</th><th>連接時間</th></tr>';
                    
                    for (let sw of data.topology.switches) {
                        const dpid = sw.dpid || 'Unknown';
                        const portCount = sw.ports ? sw.ports.length : 0;
                        topoHtml += `
                            <tr>
                                <td>🛰️ SAT-${dpid}</td>
                                <td>${portCount}</td>
                                <td>${new Date().toLocaleTimeString()}</td>
                            </tr>
                        `;
                    }
                    topoHtml += '</table>';
                    
                    topoHtml += '<h3>🛰️↔️🛰️ 衛星間鏈路 (' + data.topology.links.length + ')</h3>';
                    topoHtml += '<table><tr><th>來源衛星</th><th>目標衛星</th><th>來源天線</th><th>目標天線</th></tr>';
                    
                    for (let link of data.topology.links) {
                        topoHtml += `
                            <tr>
                                <td>🛰️ SAT-${link.src.dpid}</td>
                                <td>🛰️ SAT-${link.dst.dpid}</td>
                                <td>天線-${link.src.port_no}</td>
                                <td>天線-${link.dst.port_no}</td>
                            </tr>
                        `;
                    }
                    topoHtml += '</table>';
                    
                    document.getElementById('topology-status').innerHTML = topoHtml;
                } else {
                    const errorMsg = data.topology ? data.topology.error : '無 topology 數據';
                    document.getElementById('topology-status').innerHTML = 
                        '<p style="color: orange;">⚠️ ' + errorMsg + '</p>';
                }
            })
            .catch(error => {
                console.error('載入數據失敗:', error);
                document.getElementById('satellite-count').textContent = 'Error';
                document.getElementById('link-count').textContent = 'Error';
                document.getElementById('avg-quality').textContent = 'Error';
                document.getElementById('qos-policies').textContent = 'Error';
                document.getElementById('topology-status').innerHTML = '<p style="color: red;">❌ 載入失敗</p>';
            });
    </script>
</body>
</html>
        """
        return Response(content_type="text/html", body=html.encode("utf-8"))

    @route("satellite", "/api/status", methods=["GET"])
    def api_status(self, req, **kwargs):
        """API: 獲取系統狀態（整合 topology 數據）"""
        try:
            # 獲取衛星控制器狀態
            status = self.satellite_controller.get_network_status()

            # 獲取 topology API 數據
            try:
                switches = get_switch(self.satellite_controller)
                links = get_link(self.satellite_controller)
                hosts = get_host(self.satellite_controller)

                # 將 topology 數據整合到狀態中
                status["topology"] = {
                    "switches": [switch.to_dict() for switch in switches],
                    "links": [link.to_dict() for link in links],
                    "hosts": [host.to_dict() for host in hosts],
                }

                # 更新交換機數據
                if switches:
                    status["switches"]["topology_switches"] = len(switches)
                    status["switches"]["connected_switches"] = [
                        sw.dp.id for sw in switches
                    ]

                # 更新鏈路數據
                if links:
                    status["links"]["topology_links"] = len(links)

            except Exception as topo_error:
                self.satellite_controller.logger.warning(
                    f"無法獲取 topology 數據: {topo_error}"
                )
                status["topology"] = {"error": str(topo_error)}

            # 添加地面站連接狀態
            status["ground_station_connections"] = (
                self.satellite_controller.ground_station_status
            )

            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    status, indent=2, ensure_ascii=False, default=str
                ).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/api/satellite/<sat_id>", methods=["GET"])
    def api_satellite_detail(self, req, sat_id, **kwargs):
        """API: 獲取特定衛星詳細資訊"""
        try:
            sat_id = int(sat_id)
            detail = self.satellite_controller.get_satellite_details(sat_id)
            if detail:
                return Response(
                    content_type="application/json",
                    body=json_module.dumps(
                        detail, indent=2, ensure_ascii=False, default=str
                    ).encode("utf-8"),
                )
            else:
                error_response = {
                    "error": f"Satellite {sat_id} not found",
                    "status": "not_found",
                }
                return Response(
                    status=404,
                    content_type="application/json",
                    body=json_module.dumps(error_response).encode("utf-8"),
                )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/api/topology", methods=["GET"])
    def api_topology(self, req, **kwargs):
        """API: 獲取 topology 數據（兼容 rest_topology.py 格式）"""
        try:
            switches = get_switch(self.satellite_controller)
            links = get_link(self.satellite_controller)
            hosts = get_host(self.satellite_controller)

            topology_data = {
                "switches": [switch.to_dict() for switch in switches],
                "links": [link.to_dict() for link in links],
                "hosts": [host.to_dict() for host in hosts],
                "summary": {
                    "switch_count": len(switches),
                    "link_count": len(links),
                    "host_count": len(hosts),
                },
            }

            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    topology_data, indent=2, ensure_ascii=False, default=str
                ).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/api/links", methods=["GET"])
    def api_links(self, req, **kwargs):
        """API: 獲取鏈路統計"""
        try:
            stats = self.satellite_controller.get_link_statistics()
            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    stats, indent=2, ensure_ascii=False, default=str
                ).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/api/performance", methods=["GET"])
    def api_performance(self, req, **kwargs):
        """API: 獲取性能指標"""
        try:
            metrics = self.satellite_controller.get_performance_metrics()
            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    metrics, indent=2, ensure_ascii=False, default=str
                ).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/export", methods=["GET"])
    def export_network_state(self, req, **kwargs):
        """API: 匯出網路狀態"""
        try:
            filename = self.satellite_controller.export_network_state()
            if filename:
                response = {"status": "success", "filename": filename}
            else:
                response = {"status": "failed", "error": "Export failed"}
            return Response(
                content_type="application/json",
                body=json_module.dumps(response).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/speed", methods=["POST"])
    def adjust_simulation_speed(self, req, **kwargs):
        """API: 調整模擬速度"""
        try:
            body = req.json
            speed = float(body.get("speed", 1.0))
            self.satellite_controller.adjust_simulation_speed(speed)
            response = {"status": "success", "new_speed": speed}
            return Response(
                content_type="application/json",
                body=json_module.dumps(response).encode("utf-8"),
            )
        except Exception as e:
            error_response = {"error": str(e), "status": "failed"}
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps(error_response).encode("utf-8"),
            )

    @route("satellite", "/api/position_update", methods=["POST"])
    def position_update(self, req, **kwargs):
        """接收來自模擬器的位置更新"""
        try:
            # 解析 JSON 數據
            try:
                position_data = json_module.loads(req.body.decode("utf-8"))
            except:
                return Response(
                    status=400,
                    content_type="application/json",
                    body=json_module.dumps({"error": "Invalid JSON"}).encode("utf-8"),
                )

            # 更新衛星位置信息
            if "satellites" in position_data:
                for dpid, sat_info in position_data["satellites"].items():
                    dpid = int(dpid)  # 確保 DPID 是整數
                    self.satellite_controller.satellite_positions[dpid] = {
                        "id": sat_info["id"],
                        "latitude": sat_info["latitude"],
                        "longitude": sat_info["longitude"],
                        "altitude": sat_info["altitude"],
                        "visible_stations": sat_info.get("visible_stations", []),
                        "last_update": time.time(),
                    }

            # 更新地面站信息
            if "ground_stations" in position_data:
                for gs_name, gs_info in position_data["ground_stations"].items():
                    self.satellite_controller.ground_stations[gs_name] = {
                        "name": gs_info["name"],
                        "latitude": gs_info["latitude"],
                        "longitude": gs_info["longitude"],
                        "detection_range": gs_info.get("detection_range", 1000),
                        "elevation_threshold": gs_info.get("elevation_threshold", 10),
                        "last_update": time.time(),
                    }

            # 更新連接矩陣
            if "satellites" in position_data:
                for dpid, sat_info in position_data["satellites"].items():
                    dpid = int(dpid)
                    self.satellite_controller.connectivity_matrix[dpid] = sat_info.get(
                        "visible_stations", []
                    )

            # 根據位置信息動態調整 QoS 和路由
            self._process_position_based_routing(position_data)

            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    {"status": "success", "timestamp": time.time()}
                ).encode("utf-8"),
            )

        except Exception as e:
            self.satellite_controller.logger.error(f"位置更新處理錯誤: {e}")
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps({"error": str(e)}).encode("utf-8"),
            )

    def _process_position_based_routing(self, position_data):
        """基於位置信息處理路由和 QoS"""
        try:
            # 這裡可以添加基於地理位置的路由邏輯
            # 例如：根據衛星與地面站的距離調整 QoS 參數

            for dpid, sat_info in position_data.get("satellites", {}).items():
                dpid = int(dpid)
                visible_stations = sat_info.get("visible_stations", [])

                # 記錄連接狀態變化
                if dpid in self.satellite_controller.switches:
                    self.satellite_controller.logger.debug(
                        f"衛星 {sat_info['id']} (DPID:{dpid}) 可見地面站: {visible_stations}"
                    )

                # 這裡可以添加動態 QoS 調整邏輯
                # 例如：根據衛星距離地面站的遠近調整帶寬限制

        except Exception as e:
            self.satellite_controller.logger.warning(f"位置路由處理錯誤: {e}")

    @route("satellite", "/topology", methods=["GET"])
    def topology_page(self, req, **kwargs):
        """簡單的拓撲視圖頁面"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>衛星網路拓撲</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .topology-container { 
            background: white; 
            border-radius: 8px; 
            padding: 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .node { 
            display: inline-block; 
            margin: 10px; 
            padding: 15px; 
            border-radius: 50%; 
            text-align: center; 
            font-weight: bold; 
            color: white; 
            min-width: 80px; 
        }
        .satellite { 
            background-color: #3498db; 
        }
        .ground-station { 
            background-color: #27ae60; 
        }
        .link { 
            margin: 5px 0; 
            padding: 5px; 
            background-color: #ecf0f1; 
            border-radius: 4px; 
        }
        .back-button { 
            padding: 10px 20px; 
            background-color: #34495e; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            display: inline-block; 
            margin-bottom: 20px; 
        }
    </style>
</head>
<body>
              <a href="/" class="back-button">← 返回儀表板</a>
    
    <div class="topology-container">
        <h1>🗺️ 衛星網路拓撲圖</h1>
        
        <h2>🛰️ 衛星節點</h2>
        <div id="satellites"></div>
        
        <h2>🏢 地面站節點</h2>
        <div id="ground-stations"></div>
        
        <h2>🔗 活躍鏈路</h2>
        <div id="active-links"></div>
    </div>
    
              <script>
         // 載入狀態數據（衛星數據）
         fetch('/api/status')
             .then(response => response.json())
             .then(data => {
                 // 顯示衛星節點（模擬數據）
                 let satellitesHtml = '';
                 if (data.satellites.positions) {
                     for (let satId of Object.keys(data.satellites.positions)) {
                         satellitesHtml += `<div class="node satellite">衛星 ${satId}</div>`;
                     }
                 }
                 
                 // 顯示實際交換機（topology 數據）
                 if (data.topology && data.topology.switches) {
                     for (let sw of data.topology.switches) {
                         satellitesHtml += `<div class="node satellite">交換機 ${sw.dpid}</div>`;
                     }
                 }
                 
                 document.getElementById('satellites').innerHTML = satellitesHtml || '無節點數據';
                 
                 // 顯示地面站節點
                 let groundStationsHtml = '';
                 if (data.ground_stations.stations) {
                     for (let [gsId, station] of Object.entries(data.ground_stations.stations)) {
                         groundStationsHtml += `<div class="node ground-station">${station.name || gsId}</div>`;
                     }
                 }
                 document.getElementById('ground-stations').innerHTML = groundStationsHtml || '無地面站數據';
                 
                 // 顯示活躍鏈路（衛星模擬鏈路 + 實際拓撲鏈路）
                 let linksHtml = '';
                 
                 // 衛星鏈路
                 if (data.links.quality) {
                     linksHtml += '<h4>衛星鏈路：</h4>';
                     for (let [linkKey, quality] of Object.entries(data.links.quality)) {
                         const qualityPercent = (quality.score * 100).toFixed(1);
                         linksHtml += `
                             <div class="link">
                                 <strong>${linkKey}</strong> - 
                                 品質: ${qualityPercent}%, 
                                 延遲: ${quality.latency.toFixed(2)}ms, 
                                 帶寬: ${quality.bandwidth}Mbps
                             </div>
                         `;
                     }
                 }
                 
                 // 實際拓撲鏈路
                 if (data.topology && data.topology.links) {
                     linksHtml += '<h4>實際拓撲鏈路：</h4>';
                     for (let link of data.topology.links) {
                         linksHtml += `
                             <div class="link">
                                 <strong>拓撲鏈路</strong> - 
                                 來源: ${link.src.dpid}:${link.src.port_no}, 
                                 目標: ${link.dst.dpid}:${link.dst.port_no}
                             </div>
                         `;
                     }
                 }
                 
                 document.getElementById('active-links').innerHTML = linksHtml || '無活躍鏈路';
             })
             .catch(error => {
                 console.error('載入拓撲數據失敗:', error);
             });
    </script>
</body>
</html>
        """
        return Response(content_type="text/html", body=html.encode("utf-8"))

    @route("satellite", "/api/ground_station_update", methods=["POST"])
    def ground_station_update(self, req, **kwargs):
        """接收來自模擬器的地面站連接狀態更新"""
        try:
            # 解析 JSON 數據
            try:
                update_data = json_module.loads(req.body.decode("utf-8"))
            except:
                return Response(
                    status=400,
                    content_type="application/json",
                    body=json_module.dumps({"error": "Invalid JSON"}).encode("utf-8"),
                )

            # 處理連接狀態變化
            if update_data.get("type") == "connection_change":
                satellite = update_data.get("satellite", {})
                ground_station = update_data.get("ground_station", {})
                is_connected = update_data.get("connected", False)

                sat_id = satellite.get("id")
                dpid = satellite.get("dpid")
                gs_name = ground_station.get("name")

                if sat_id and dpid and gs_name:
                    # 初始化地面站狀態（如果不存在）
                    if gs_name not in self.satellite_controller.ground_station_status:
                        self.satellite_controller.ground_station_status[gs_name] = {}

                    # 更新連接狀態
                    self.satellite_controller.ground_station_status[gs_name][
                        dpid
                    ] = is_connected

                    # 記錄狀態變化
                    status_text = "在區域內" if is_connected else "不在區域內"
                    self.satellite_controller.logger.info(
                        f"地面站 {gs_name}: 衛星 {sat_id} (DPID:{dpid}) - {status_text}"
                    )

                    # 根據連接狀態調整 QoS 或路由（可選）
                    self._handle_connection_change(dpid, gs_name, is_connected)

            return Response(
                content_type="application/json",
                body=json_module.dumps(
                    {"status": "success", "timestamp": time.time()}
                ).encode("utf-8"),
            )

        except Exception as e:
            self.satellite_controller.logger.error(f"地面站狀態更新處理錯誤: {e}")
            return Response(
                status=500,
                content_type="application/json",
                body=json_module.dumps({"error": str(e)}).encode("utf-8"),
            )

    def _handle_connection_change(self, dpid: int, gs_name: str, is_connected: bool):
        """處理衛星與地面站的連接狀態變化"""
        try:
            # 這裡可以添加基於連接狀態的路由或 QoS 調整邏輯
            # 例如：當衛星進入地面站區域時，為該衛星設置特定的流表規則

            if dpid in self.satellite_controller.switches:
                datapath = self.satellite_controller.switches[dpid]["datapath"]

                if is_connected:
                    # 衛星進入地面站區域 - 可以添加特定流表規則
                    self.satellite_controller.logger.debug(
                        f"衛星 DPID:{dpid} 進入 {gs_name} 區域，可設置優化路由"
                    )
                else:
                    # 衛星離開地面站區域 - 可以清理相關流表規則
                    self.satellite_controller.logger.debug(
                        f"衛星 DPID:{dpid} 離開 {gs_name} 區域，清理相關配置"
                    )

        except Exception as e:
            self.satellite_controller.logger.warning(f"連接變化處理錯誤: {e}")


# 用於測試的獨立運行
if __name__ == "__main__":
    from ryu.cmd import manager
    import sys
    
    # 設置日誌級別
    import logging

    logging.basicConfig(level=logging.INFO)
    
    # 啟動應用
    sys.argv = ["ryu-manager"]
    sys.argv.append("satellite_sdn_controller.py")
    sys.argv.append("--verbose")
    manager.main() 
