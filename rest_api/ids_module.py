#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.lib.packet import tcp, udp, icmp, ipv4
import time
import json
import os

class IDSModule(object):
    """入侵檢測系統模組：提供基本的網絡流量異常檢測
    
    此模組實現了基本的入侵檢測功能，包括：
    1. SYN Flood 檢測
    2. 掃描檢測 (端口掃描)
    3. 異常流量模式檢測
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
        self.connection_tracker = {}  # 連接追踪 {tuple(ip_src, ip_dst, port_src, port_dst): count}
        self.scan_tracker = {}  # 掃描追踪 {ip_src: {dst_port: timestamp}}
        self.alert_history = []  # 警報歷史
        
        # 閾值設定
        self.syn_flood_threshold = 100  # SYN包閾值
        self.scan_threshold = 15  # 掃描閾值(端口數)
        self.scan_window = 5  # 掃描時間窗口(秒)
    
    def analyze_packet(self, datapath, pkt, eth, ip_pkt, tcp_pkt=None, udp_pkt=None, icmp_pkt=None):
        """分析單個封包是否存在可疑行為
        
        返回值:
            (is_threat, threat_type, description)
            is_threat: 是否為威脅
            threat_type: 威脅類型
            description: 威脅描述
        """
        if not ip_pkt:
            return False, None, None
        
        # 檢測 SYN Flood
        syn_flood = self._check_syn_flood(ip_pkt, tcp_pkt)
        if syn_flood[0]:
            self._add_alert(datapath.id, ip_pkt.src, ip_pkt.dst, "SYN Flood", syn_flood[2])
            return syn_flood
        
        # 檢測端口掃描
        port_scan = self._check_port_scan(ip_pkt, tcp_pkt)
        if port_scan[0]:
            self._add_alert(datapath.id, ip_pkt.src, ip_pkt.dst, "Port Scan", port_scan[2])
            return port_scan
        
        return False, None, None
    
    def _check_syn_flood(self, ip_pkt, tcp_pkt):
        """檢測SYN Flood攻擊"""
        if not tcp_pkt or not (tcp_pkt.bits & 0x02):  # 不是SYN包
            return False, None, None
        
        # 生成連接鍵
        conn_key = (ip_pkt.src, ip_pkt.dst)
        
        # 增加計數器
        now = time.time()
        if conn_key in self.connection_tracker:
            count, first_time = self.connection_tracker[conn_key]
            count += 1
            
            # 如果經過超過30秒，重置計數
            if now - first_time > 30:
                self.connection_tracker[conn_key] = (1, now)
            else:
                self.connection_tracker[conn_key] = (count, first_time)
                
                # 檢查是否超過閾值
                if count > self.syn_flood_threshold:
                    description = f"Possible SYN Flood from {ip_pkt.src} to {ip_pkt.dst}, {count} SYNs in {int(now - first_time)}s"
                    return True, "SYN Flood", description
        else:
            self.connection_tracker[conn_key] = (1, now)
        
        # 清理舊記錄
        self._clean_old_records()
        
        return False, None, None
    
    def _check_port_scan(self, ip_pkt, tcp_pkt):
        """檢測端口掃描"""
        if not tcp_pkt:
            return False, None, None
        
        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        dst_port = tcp_pkt.dst_port
        
        now = time.time()
        
        # 初始化掃描追踪
        if src_ip not in self.scan_tracker:
            self.scan_tracker[src_ip] = {}
        
        # 記錄目標端口
        self.scan_tracker[src_ip][f"{dst_ip}:{dst_port}"] = now
        
        # 計算時間窗口內的不同端口數
        scanned_ports = 0
        for port_key, timestamp in list(self.scan_tracker[src_ip].items()):
            if now - timestamp <= self.scan_window:
                scanned_ports += 1
            else:
                # 移除舊記錄
                del self.scan_tracker[src_ip][port_key]
        
        # 檢查是否超過閾值
        if scanned_ports > self.scan_threshold:
            description = f"Port scan detected from {src_ip}: {scanned_ports} ports in {self.scan_window}s"
            return True, "Port Scan", description
        
        return False, None, None
    
    def _clean_old_records(self):
        """清理過期記錄"""
        now = time.time()
        
        # 清理連接追踪
        for conn_key in list(self.connection_tracker.keys()):
            _, first_time = self.connection_tracker[conn_key]
            if now - first_time > 60:
                del self.connection_tracker[conn_key]
    
    def _add_alert(self, datapath_id, src_ip, dst_ip, alert_type, description):
        """添加警報記錄"""
        alert = {
            "timestamp": time.time(),
            "datapath_id": datapath_id,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "type": alert_type,
            "description": description
        }
        self.alert_history.append(alert)
        self.app.logger.warning("IDS警報: %s", description)
        
        # 保持警報歷史不超過1000條
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    def get_alerts(self, count=10):
        """獲取最近的警報記錄"""
        return self.alert_history[-count:]
    
    def save_alerts(self, alert_file=None):
        """保存警報記錄到文件"""
        if alert_file is None:
            alert_file = os.path.join('config', 'ids_alerts.json')
            
        try:
            os.makedirs(os.path.dirname(alert_file), exist_ok=True)
            with open(alert_file, 'w') as f:
                json.dump(self.alert_history, f, indent=4)
            self.app.logger.info("已保存 %d 條IDS警報", len(self.alert_history))
        except Exception as e:
            self.app.logger.error("無法保存IDS警報: %s", e)
