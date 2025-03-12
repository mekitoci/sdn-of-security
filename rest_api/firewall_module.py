#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, tcp, udp, icmp
import json
import os

class FirewallModule(object):
    """防火牆模組：提供封包過濾和訪問控制功能
    
    此模組可以從配置檔讀取防火牆規則，或動態添加規則。
    支持基於源/目的IP、端口、協議的過濾規則。
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
        self.rules = []  # 防火牆規則列表
        self.load_rules()  # 加載預設規則
    
    def load_rules(self, rules_file=None):
        """從JSON文件加載防火牆規則"""
        if rules_file is None:
            rules_file = os.path.join('config', 'firewall_rules.json')
            
        try:
            if os.path.exists(rules_file):
                with open(rules_file, 'r') as f:
                    self.rules = json.load(f)
                self.app.logger.info("已加載 %d 條防火牆規則", len(self.rules))
            else:
                self.app.logger.warning("防火牆規則檔不存在: %s", rules_file)
        except Exception as e:
            self.app.logger.error("無法加載防火牆規則: %s", e)
    
    def save_rules(self, rules_file=None):
        """保存防火牆規則到JSON文件"""
        if rules_file is None:
            rules_file = os.path.join('config', 'firewall_rules.json')
            
        try:
            os.makedirs(os.path.dirname(rules_file), exist_ok=True)
            with open(rules_file, 'w') as f:
                json.dump(self.rules, f, indent=4)
            self.app.logger.info("已保存 %d 條防火牆規則", len(self.rules))
        except Exception as e:
            self.app.logger.error("無法保存防火牆規則: %s", e)
    
    def add_rule(self, rule):
        """添加防火牆規則
        
        規則格式舉例:
        {
            "name": "Block SSH",
            "src_ip": "10.0.0.1/32",
            "dst_ip": "any",
            "protocol": "tcp",
            "dst_port": 22,
            "action": "deny"
        }
        """
        # 檢查規則格式
        required_fields = ["name", "action"]
        for field in required_fields:
            if field not in rule:
                self.app.logger.error("防火牆規則缺少必要欄位: %s", field)
                return False
        
        self.rules.append(rule)
        self.app.logger.info("添加防火牆規則: %s", rule["name"])
        return True
    
    def remove_rule(self, rule_name):
        """根據規則名稱刪除規則"""
        for i, rule in enumerate(self.rules):
            if rule.get("name") == rule_name:
                del self.rules[i]
                self.app.logger.info("刪除防火牆規則: %s", rule_name)
                return True
        
        self.app.logger.warning("找不到防火牆規則: %s", rule_name)
        return False
    
    def install_rules(self, datapath):
        """將防火牆規則安裝到交換機"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 防火牆規則優先度起始值 (高於普通流表項)
        priority = 100
        
        for rule in self.rules:
            match_fields = {}
            match_fields["eth_type"] = 0x0800  # IPv4
            
            # 添加源IP條件
            if rule.get("src_ip") and rule["src_ip"] != "any":
                match_fields["ipv4_src"] = rule["src_ip"]
            
            # 添加目的IP條件
            if rule.get("dst_ip") and rule["dst_ip"] != "any":
                match_fields["ipv4_dst"] = rule["dst_ip"]
            
            # 添加協議條件
            proto_map = {"tcp": 6, "udp": 17, "icmp": 1}
            if rule.get("protocol") and rule["protocol"] in proto_map:
                match_fields["ip_proto"] = proto_map[rule["protocol"]]
                
                # 添加端口條件 (僅TCP和UDP)
                if rule["protocol"] in ["tcp", "udp"]:
                    if rule.get("src_port"):
                        match_fields[rule["protocol"] + "_src"] = rule["src_port"]
                    if rule.get("dst_port"):
                        match_fields[rule["protocol"] + "_dst"] = rule["dst_port"]
            
            match = parser.OFPMatch(**match_fields)
            
            # 設置動作
            actions = []
            if rule.get("action") == "allow":
                actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            # 拒絕操作不添加任何動作，包將被丟棄
            
            # 安裝流表項
            self.app.add_flow(datapath, priority, match, actions)
            self.app.logger.info("安裝防火牆規則: %s", rule["name"])
            
            # 每條規則優先度遞減
            priority -= 1
    
    def check_packet(self, pkt, eth, ip_pkt, tcp_pkt, udp_pkt):
        """檢查封包是否符合防火牆規則
        
        返回值:
            True: 允許通過
            False: 拒絕通過
        """
        # 如果沒有IP封包，默認允許
        if not ip_pkt:
            return True
        
        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        
        for rule in self.rules:
            # 檢查IP
            if rule.get("src_ip") and rule["src_ip"] != "any":
                # 簡單IP匹配，實際應當支持CIDR
                if src_ip != rule["src_ip"]:
                    continue
            
            if rule.get("dst_ip") and rule["dst_ip"] != "any":
                if dst_ip != rule["dst_ip"]:
                    continue
            
            # 檢查協議
            proto_map = {"tcp": 6, "udp": 17, "icmp": 1}
            if rule.get("protocol") and rule["protocol"] in proto_map:
                if ip_pkt.proto != proto_map[rule["protocol"]]:
                    continue
                
                # 檢查端口 (僅TCP和UDP)
                if rule["protocol"] == "tcp" and tcp_pkt:
                    if rule.get("src_port") and tcp_pkt.src_port != rule["src_port"]:
                        continue
                    if rule.get("dst_port") and tcp_pkt.dst_port != rule["dst_port"]:
                        continue
                elif rule["protocol"] == "udp" and udp_pkt:
                    if rule.get("src_port") and udp_pkt.src_port != rule["src_port"]:
                        continue
                    if rule.get("dst_port") and udp_pkt.dst_port != rule["dst_port"]:
                        continue
            
            # 符合規則，返回相應動作
            return rule.get("action") == "allow"
        
        # 默認允許
        return True
