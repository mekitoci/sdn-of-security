#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.lib.packet import vlan, ipv4
import json
import os
import ipaddress

class NetworkSlice(object):
    """網絡切片類：代表一個虛擬網絡切片
    
    包含切片的基本屬性和流量匹配條件
    """
    
    def __init__(self, slice_id, priority, vlans=None, hosts=None):
        self.slice_id = slice_id  # 切片標識
        self.priority = priority  # 優先級
        self.vlans = vlans or []  # VLAN IDs
        self.hosts = []  # IP地址/網段列表
        
        # 解析IP地址/網段
        if hosts:
            for host in hosts:
                try:
                    if '/' in host:
                        # 網段
                        self.hosts.append(ipaddress.IPv4Network(host))
                    else:
                        # 單個IP
                        self.hosts.append(ipaddress.IPv4Address(host))
                except Exception:
                    pass
        
        self.bandwidth = None  # 帶寬限制 (Mbps)
        self.meter_id = None  # 計量表ID
    
    def set_bandwidth(self, bandwidth_mbps):
        """設置切片帶寬限制"""
        self.bandwidth = bandwidth_mbps
    
    def match_packet(self, pkt):
        """檢查封包是否屬於此切片"""
        # 獲取封包協議
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        vlan_pkt = pkt.get_protocol(vlan.vlan)
        
        # 檢查IP地址
        if ip_pkt:
            src_ip = ipaddress.IPv4Address(ip_pkt.src)
            dst_ip = ipaddress.IPv4Address(ip_pkt.dst)
            
            for host in self.hosts:
                # 檢查源IP或目的IP是否匹配
                if isinstance(host, ipaddress.IPv4Network):
                    if src_ip in host or dst_ip in host:
                        return True
                elif src_ip == host or dst_ip == host:
                    return True
        
        # 檢查VLAN標籤
        if vlan_pkt and vlan_pkt.vid in self.vlans:
            return True
            
        return False


class NetworkSliceManager(object):
    """網絡切片管理器：管理多個網絡切片
    
    負責切片的創建、修改、刪除和流量隔離
    """
    
    def __init__(self, app):
        self.app = app  # 引用主應用
        self.slices = {}  # {slice_id: NetworkSlice}
        self.load_slices()  # 加載切片配置
    
    def load_slices(self, config_file=None):
        """從配置文件加載切片設置"""
        if config_file is None:
            config_file = os.path.join('config', 'slice_config.json')
            
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                for slice_config in config.get('slices', []):
                    slice_id = slice_config.get('id')
                    if not slice_id:
                        continue
                        
                    priority = slice_config.get('priority', 10)
                    vlans = slice_config.get('vlans', [])
                    hosts = slice_config.get('hosts', [])
                    
                    # 創建切片
                    network_slice = NetworkSlice(slice_id, priority, vlans, hosts)
                    
                    # 設置帶寬
                    if 'bandwidth' in slice_config:
                        network_slice.set_bandwidth(slice_config['bandwidth'])
                    
                    self.slices[slice_id] = network_slice
                    
                self.app.logger.info("已加載 %d 個網絡切片", len(self.slices))
            else:
                # 創建默認切片
                self._create_default_slices()
        except Exception as e:
            self.app.logger.error("加載網絡切片配置失敗: %s", e)
            # 創建默認切片
            self._create_default_slices()
    
    def _create_default_slices(self):
        """創建默認切片"""
        # 租戶1切片
        tenant1 = NetworkSlice("tenant1", 100, hosts=["10.0.1.0/24"])
        self.slices["tenant1"] = tenant1
        
        # 租戶2切片
        tenant2 = NetworkSlice("tenant2", 90, hosts=["10.0.2.0/24"])
        self.slices["tenant2"] = tenant2
        
        self.app.logger.info("已創建默認網絡切片")
    
    def save_slices(self, config_file=None):
        """保存切片配置到文件"""
        if config_file is None:
            config_file = os.path.join('config', 'slice_config.json')
            
        try:
            slices_config = []
            for slice_id, network_slice in self.slices.items():
                slice_config = {
                    'id': slice_id,
                    'priority': network_slice.priority,
                    'vlans': network_slice.vlans,
                    'hosts': [str(h) for h in network_slice.hosts],
                }
                
                if network_slice.bandwidth:
                    slice_config['bandwidth'] = network_slice.bandwidth
                    
                slices_config.append(slice_config)
            
            config = {'slices': slices_config}
            
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.app.logger.info("已保存 %d 個網絡切片配置", len(self.slices))
        except Exception as e:
            self.app.logger.error("保存網絡切片配置失敗: %s", e)
    
    def create_slice(self, slice_id, priority=10, vlans=None, hosts=None):
        """創建新的網絡切片"""
        if slice_id in self.slices:
            self.app.logger.warning("網絡切片已存在: %s", slice_id)
            return False
            
        self.slices[slice_id] = NetworkSlice(slice_id, priority, vlans, hosts)
        self.app.logger.info("創建網絡切片: %s", slice_id)
        return True
    
    def delete_slice(self, slice_id):
        """刪除網絡切片"""
        if slice_id not in self.slices:
            self.app.logger.warning("網絡切片不存在: %s", slice_id)
            return False
            
        del self.slices[slice_id]
        self.app.logger.info("刪除網絡切片: %s", slice_id)
        return True
    
    def get_slice_for_packet(self, pkt):
        """查找封包所屬的切片"""
        for slice_id, network_slice in sorted(
            self.slices.items(), 
            key=lambda x: x[1].priority, 
            reverse=True
        ):
            if network_slice.match_packet(pkt):
                return slice_id, network_slice
        return None, None
    
    def install_slice_flow(self, datapath, network_slice, match, in_port, out_port):
        """安裝切片特定的流表項"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 基本動作：轉發到出口
        actions = [parser.OFPActionOutput(out_port)]
        
        # 如果切片有帶寬限制，添加計量器
        if network_slice.bandwidth:
            if network_slice.meter_id is None:
                # 創建計量器
                network_slice.meter_id = self._create_meter(
                    datapath, 
                    network_slice.slice_id, 
                    network_slice.bandwidth
                )
            
            # 添加計量器動作
            if network_slice.meter_id:
                meter_action = parser.OFPActionMeter(network_slice.meter_id)
                actions.insert(0, meter_action)
        
        # 安裝流表項
        self.app.add_flow(
            datapath,
            network_slice.priority,
            match,
            actions
        )
        
        self.app.logger.info(
            "為切片 %s 安裝流表: in_port=%s, out_port=%s, 優先級=%d", 
            network_slice.slice_id, 
            in_port, 
            out_port,
            network_slice.priority
        )
    
    def _create_meter(self, datapath, slice_id, bandwidth_mbps):
        """創建帶寬限制計量器"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # 計算速率 (kbps)
        rate_kbps = bandwidth_mbps * 1000
        
        # 生成計量器ID
        # 使用切片ID哈希作為唯一標識
        meter_id = hash(slice_id) % 0xffff
        if meter_id < 1:
            meter_id = 1
        
        # 創建帶寬限制配置
        bands = [
            parser.OFPMeterBandDrop(rate=rate_kbps, burst_size=rate_kbps//10)
        ]
        
        # 發送計量器創建消息
        try:
            req = parser.OFPMeterMod(
                datapath=datapath,
                command=ofproto.OFPMC_ADD,
                flags=ofproto.OFPMF_KBPS,
                meter_id=meter_id,
                bands=bands
            )
            datapath.send_msg(req)
            
            self.app.logger.info(
                "為切片 %s 創建計量器: id=%d, 帶寬=%d Mbps",
                slice_id,
                meter_id,
                bandwidth_mbps
            )
            
            return meter_id
        except Exception as e:
            self.app.logger.error("創建計量器失敗: %s", e)
            return None
