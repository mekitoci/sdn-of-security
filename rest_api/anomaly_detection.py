#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import os
from collections import defaultdict
from statistics import mean, stdev

class AnomalyDetector(object):
    """流量異常檢測模塊：提供高級的統計分析和流量異常檢測
    
    此模塊實現了以下功能：
    1. 流量基線學習
    2. 流量突變檢測
    3. 異常流量模式識別
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
        self.flow_stats_history = defaultdict(list)  # {flow_id: [stats1, stats2...]}
        self.baseline = {}  # 基線 {flow_id: {'mean': mean, 'std': std, ...}}
        self.anomaly_threshold = 3.0  # 標準差閾值
        self.learning_mode = True  # 學習模式
        self.learning_period = 300  # 學習期(秒)
        self.learning_start_time = time.time()
        self.anomaly_history = []  # 異常歷史
    
    def analyze_flow(self, datapath_id, flow_id, packet_count, byte_count, duration_sec, duration_nsec):
        """分析流量統計數據，檢測異常
        
        參數:
            datapath_id: 交換機ID
            flow_id: 流標識，如 "10.0.0.1->10.0.0.2:TCP"
            packet_count: 封包數
            byte_count: 位元組數
            duration_sec: 持續時間(秒)
            duration_nsec: 持續時間(納秒)
            
        返回值:
            (is_anomaly, anomaly_type, description)
        """
        # 計算速率
        duration = duration_sec + duration_nsec / 1e9
        if duration == 0:
            return False, None, None
            
        packet_rate = packet_count / duration if duration > 0 else 0
        byte_rate = byte_count / duration if duration > 0 else 0
        
        timestamp = time.time()
        stat = {
            'timestamp': timestamp,
            'packet_count': packet_count,
            'byte_count': byte_count,
            'packet_rate': packet_rate,
            'byte_rate': byte_rate,
            'duration': duration
        }
        
        # 保存統計數據
        self.flow_stats_history[flow_id].append(stat)
        
        # 保留最近30分鐘的歷史數據
        history = self.flow_stats_history[flow_id]
        cutoff_time = timestamp - 1800  # 30分鐘
        while history and history[0]['timestamp'] < cutoff_time:
            history.pop(0)
        
        # 學習模式下不檢測異常
        if self.learning_mode:
            if timestamp - self.learning_start_time > self.learning_period:
                self.learning_mode = False
                self._establish_baseline()
                self.app.logger.info("異常檢測: 學習期結束，建立流量基線")
            return False, None, None
        
        # 檢測流量異常
        return self._detect_anomaly(datapath_id, flow_id, stat)
    
    def _establish_baseline(self):
        """建立流量基線"""
        for flow_id, history in self.flow_stats_history.items():
            if len(history) < 10:  # 數據點太少
                continue
                
            try:
                packet_rates = [stat['packet_rate'] for stat in history]
                byte_rates = [stat['byte_rate'] for stat in history]
                
                self.baseline[flow_id] = {
                    'packet_rate_mean': mean(packet_rates),
                    'packet_rate_std': stdev(packet_rates) if len(packet_rates) > 1 else 0,
                    'byte_rate_mean': mean(byte_rates),
                    'byte_rate_std': stdev(byte_rates) if len(byte_rates) > 1 else 0,
                    'sample_count': len(history)
                }
                
                self.app.logger.debug(
                    "流量基線 [%s]: 封包率 %.2f±%.2f pps, 位元組率 %.2f±%.2f Bps",
                    flow_id,
                    self.baseline[flow_id]['packet_rate_mean'],
                    self.baseline[flow_id]['packet_rate_std'],
                    self.baseline[flow_id]['byte_rate_mean'],
                    self.baseline[flow_id]['byte_rate_std']
                )
            except Exception as e:
                self.app.logger.error("建立基線錯誤 [%s]: %s", flow_id, e)
    
    def _detect_anomaly(self, datapath_id, flow_id, stat):
        """檢測流量異常"""
        # 如果沒有基線，嘗試建立
        if flow_id not in self.baseline and len(self.flow_stats_history[flow_id]) >= 10:
            try:
                packet_rates = [s['packet_rate'] for s in self.flow_stats_history[flow_id]]
                byte_rates = [s['byte_rate'] for s in self.flow_stats_history[flow_id]]
                
                self.baseline[flow_id] = {
                    'packet_rate_mean': mean(packet_rates),
                    'packet_rate_std': stdev(packet_rates) if len(packet_rates) > 1 else 1,
                    'byte_rate_mean': mean(byte_rates),
                    'byte_rate_std': stdev(byte_rates) if len(byte_rates) > 1 else 1,
                    'sample_count': len(self.flow_stats_history[flow_id])
                }
            except Exception:
                return False, None, None
        
        # 如果仍沒有基線，無法檢測
        if flow_id not in self.baseline:
            return False, None, None
        
        baseline = self.baseline[flow_id]
        
        # 計算 Z 分數
        packet_rate_z = 0
        if baseline['packet_rate_std'] > 0:
            packet_rate_z = abs(stat['packet_rate'] - baseline['packet_rate_mean']) / baseline['packet_rate_std']
            
        byte_rate_z = 0
        if baseline['byte_rate_std'] > 0:
            byte_rate_z = abs(stat['byte_rate'] - baseline['byte_rate_mean']) / baseline['byte_rate_std']
        
        # 檢測異常
        is_anomaly = False
        anomaly_type = None
        description = None
        
        if packet_rate_z > self.anomaly_threshold:
            is_anomaly = True
            if stat['packet_rate'] > baseline['packet_rate_mean']:
                anomaly_type = "Traffic Spike"
                description = (
                    f"流量激增 [{flow_id}]: 當前封包率 {stat['packet_rate']:.2f} pps, "
                    f"基線 {baseline['packet_rate_mean']:.2f}±{baseline['packet_rate_std']:.2f} pps, "
                    f"Z分數 {packet_rate_z:.2f}"
                )
            else:
                anomaly_type = "Traffic Drop"
                description = (
                    f"流量下降 [{flow_id}]: 當前封包率 {stat['packet_rate']:.2f} pps, "
                    f"基線 {baseline['packet_rate_mean']:.2f}±{baseline['packet_rate_std']:.2f} pps, "
                    f"Z分數 {packet_rate_z:.2f}"
                )
        elif byte_rate_z > self.anomaly_threshold:
            is_anomaly = True
            if stat['byte_rate'] > baseline['byte_rate_mean']:
                anomaly_type = "Bandwidth Spike"
                description = (
                    f"頻寬激增 [{flow_id}]: 當前速率 {stat['byte_rate']:.2f} Bps, "
                    f"基線 {baseline['byte_rate_mean']:.2f}±{baseline['byte_rate_std']:.2f} Bps, "
                    f"Z分數 {byte_rate_z:.2f}"
                )
            else:
                anomaly_type = "Bandwidth Drop"
                description = (
                    f"頻寬下降 [{flow_id}]: 當前速率 {stat['byte_rate']:.2f} Bps, "
                    f"基線 {baseline['byte_rate_mean']:.2f}±{baseline['byte_rate_std']:.2f} Bps, "
                    f"Z分數 {byte_rate_z:.2f}"
                )
        
        if is_anomaly:
            self._add_anomaly(datapath_id, flow_id, anomaly_type, description, stat)
            self.app.logger.warning("異常檢測警報: %s", description)
            
        return is_anomaly, anomaly_type, description
    
    def _add_anomaly(self, datapath_id, flow_id, anomaly_type, description, stat):
        """添加異常記錄"""
        anomaly = {
            "timestamp": time.time(),
            "datapath_id": datapath_id,
            "flow_id": flow_id,
            "type": anomaly_type,
            "description": description,
            "stats": stat
        }
        self.anomaly_history.append(anomaly)
        
        # 保持異常記錄不超過1000條
        if len(self.anomaly_history) > 1000:
            self.anomaly_history = self.anomaly_history[-1000:]
    
    def get_anomalies(self, count=10):
        """獲取最近的異常記錄"""
        return self.anomaly_history[-count:]
    
    def save_anomalies(self, anomaly_file=None):
        """保存異常記錄到文件"""
        if anomaly_file is None:
            anomaly_file = os.path.join('config', 'anomaly_history.json')
            
        try:
            os.makedirs(os.path.dirname(anomaly_file), exist_ok=True)
            with open(anomaly_file, 'w') as f:
                json.dump(self.anomaly_history, f, indent=4)
            self.app.logger.info("已保存 %d 條異常記錄", len(self.anomaly_history))
        except Exception as e:
            self.app.logger.error("無法保存異常記錄: %s", e)
    
    def reset_learning(self):
        """重置學習模式"""
        self.learning_mode = True
        self.learning_start_time = time.time()
        self.flow_stats_history.clear()
        self.baseline.clear()
        self.app.logger.info("異常檢測: 重置學習模式")
