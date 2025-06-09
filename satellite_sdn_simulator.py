#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
動態衛星 SDN 網路模擬器
實現動態拓撲變化、衛星軌道模擬、地面站連接管理
基於成功的 simple_switch_13 測試配置
"""

import time
import json
import yaml
import math
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.link import TCLink


class SatelliteOrbitSimulator:
    """衛星軌道模擬器 - 基於簡化的 LEO 軌道模型"""
    
    def __init__(self, config: dict):
        self.config = config
        self.satellites = {}
        self.ground_stations = []
        self.current_time = 0
        self.earth_radius = 6371  # 地球半徑 (km)
        
        # 初始化地面站
        for gs_config in config['ground_stations']['locations']:
            self.ground_stations.append({
                'name': gs_config['name'],
                'lat': gs_config['latitude'],
                'lon': gs_config['longitude'],
                'elevation_threshold': config['ground_stations']['min_elevation_angle']
            })
        
        # 初始化衛星軌道
        self._initialize_satellite_orbits()
    
    def _initialize_satellite_orbits(self):
        """初始化衛星軌道參數"""
        sat_config = self.config['satellites']
        num_satellites = sat_config['count']
        altitude = sat_config['altitude']
        inclination = sat_config['inclination']
        orbital_period = sat_config['orbital_period']
        
        # 均勻分佈衛星在軌道上
        for i in range(num_satellites):
            satellite_id = f"SAT{i+1}"
            # 計算初始軌道相位
            initial_phase = (2 * math.pi * i) / num_satellites
            
            self.satellites[satellite_id] = {
                'id': satellite_id,
                'altitude': altitude,
                'inclination': math.radians(inclination),
                'orbital_period': orbital_period,
                'initial_phase': initial_phase,
                'active': True,
                'connected_gs': None
            }
    
    def get_satellite_position(self, satellite_id: str, time_offset: float) -> Tuple[float, float, float]:
        """計算衛星在指定時間的位置 (緯度, 經度, 高度)"""
        if satellite_id not in self.satellites:
            return None
        
        sat = self.satellites[satellite_id]
        if not sat['active']:
            return None
        
        # 簡化的軌道計算 - 圓形軌道
        orbital_rate = 2 * math.pi / sat['orbital_period']  # rad/s
        current_angle = sat['initial_phase'] + orbital_rate * time_offset
        
        # 計算衛星位置
        lat = math.degrees(math.asin(math.sin(sat['inclination']) * math.sin(current_angle)))
        lon = math.degrees(current_angle) % 360
        if lon > 180:
            lon -= 360
        
        return lat, lon, sat['altitude']
    
    def calculate_visibility(self, satellite_id: str, time_offset: float) -> List[str]:
        """計算衛星在指定時間對哪些地面站可見"""
        sat_pos = self.get_satellite_position(satellite_id, time_offset)
        if not sat_pos:
            return []
        
        sat_lat, sat_lon, sat_alt = sat_pos
        visible_stations = []
        
        for gs in self.ground_stations:
            # 計算衛星對地面站的仰角
            elevation = self._calculate_elevation_angle(
                sat_lat, sat_lon, sat_alt,
                gs['lat'], gs['lon']
            )
            
            if elevation >= gs['elevation_threshold']:
                visible_stations.append(gs['name'])
        
        return visible_stations
    
    def _calculate_elevation_angle(self, sat_lat: float, sat_lon: float, sat_alt: float,
                                 gs_lat: float, gs_lon: float) -> float:
        """計算衛星對地面站的仰角"""
        # 簡化計算 - 實際應用中需要更精確的球面幾何計算
        # 計算地面距離
        lat_diff = math.radians(sat_lat - gs_lat)
        lon_diff = math.radians(sat_lon - gs_lon)
        
        # 使用 Haversine 公式計算地面距離
        a = (math.sin(lat_diff/2)**2 + 
             math.cos(math.radians(gs_lat)) * math.cos(math.radians(sat_lat)) * 
             math.sin(lon_diff/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        ground_distance = self.earth_radius * c
        
        # 計算仰角
        if ground_distance == 0:
            return 90.0  # 直接頭頂
        
        elevation = math.degrees(math.atan(sat_alt / ground_distance))
        return max(0, elevation)
    
    def get_active_satellites(self, time_offset: float) -> List[str]:
        """獲取當前時間活躍的衛星列表"""
        active_sats = []
        for sat_id, sat_info in self.satellites.items():
            if sat_info['active']:
                active_sats.append(sat_id)
        return active_sats
    
    def add_satellite(self, satellite_id: str):
        """添加新衛星到網路"""
        if satellite_id not in self.satellites:
            # 為新衛星分配軌道參數
            num_existing = len([s for s in self.satellites.values() if s['active']])
            initial_phase = (2 * math.pi * num_existing) / (num_existing + 1)
            
            self.satellites[satellite_id] = {
                'id': satellite_id,
                'altitude': self.config['satellites']['altitude'],
                'inclination': math.radians(self.config['satellites']['inclination']),
                'orbital_period': self.config['satellites']['orbital_period'],
                'initial_phase': initial_phase,
                'active': True,
                'connected_gs': None
            }
            return True
        else:
            self.satellites[satellite_id]['active'] = True
            return True
    
    def remove_satellite(self, satellite_id: str):
        """從網路中移除衛星"""
        if satellite_id in self.satellites:
            self.satellites[satellite_id]['active'] = False
            return True
        return False


class DynamicSatelliteTopology:
    """動態衛星拓撲管理器"""
    
    def __init__(self, config_file: str = 'leo_config.yaml'):
        # 載入配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.net = None
        self.controller = None
        self.orbit_simulator = SatelliteOrbitSimulator(self.config)
        
        # 網路元件追蹤
        self.satellites = {}  # {sat_id: switch_node}
        self.ground_stations = {}  # {gs_name: host_node}
        self.active_links = {}  # {(sat_id, gs_name): link}
        
        # 模擬狀態
        self.simulation_running = False
        self.start_time = time.time()
        
        # 線程鎖保護網路操作
        self.network_lock = threading.Lock()
        
        # 創建 Mininet 網路
        self._create_network()
    
    def _create_network(self):
        """創建基礎 Mininet 網路 - 基於成功的測試配置"""
        info("*** 初始化動態衛星 SDN 網路 (基於 simple_switch_13 配置)\n")
        
        # 創建網路實例 - 使用與測試相同的配置
        self.net = Mininet(
            controller=RemoteController,
            switch=OVSKernelSwitch,  # 使用與測試相同的交換機類型
            link=TCLink,
            autoSetMacs=True
        )
        
        # 添加控制器 - 使用配置檔案中的IP
        controller_config = self.config['controller']
        self.controller = self.net.addController(
            'c0',
            controller=RemoteController,
            ip=controller_config['ip'],  # 192.168.1.101
            port=controller_config['port']  # 6653
        )
        
        info(f"*** 控制器設定: {controller_config['ip']}:{controller_config['port']}\n")
        
        # 初始化地面站
        self._setup_ground_stations()
        
        # 初始化初始衛星 (減少數量避免複雜性)
        self._setup_initial_satellites()
        
        info("*** 基礎網路拓撲創建完成\n")
    
    def _setup_ground_stations(self):
        """設置地面站 - 使用簡化的命名和IP方案"""
        locations = self.config['ground_stations']['locations']
        # 只使用前4個地面站，避免過於複雜
        for i in range(min(4, len(locations))):
            gs_config = locations[i]
            gs_name = gs_config['name']
            # 創建地面站主機，使用簡化的主機名稱
            host_name = f'h{i+1}'  # h1, h2, h3, h4
            host = self.net.addHost(
                host_name,
                ip=f'10.0.0.{i+1}/24',  # 與測試相同的IP方案
                mac=f'00:00:00:00:00:{i+1:02d}'  # 與測試相同的MAC方案
            )
            self.ground_stations[gs_name] = host
            info(f"*** 創建地面站: {gs_name} (主機名: {host_name}, IP: 10.0.0.{i+1})\n")
    
    def _setup_initial_satellites(self):
        """設置初始衛星 - 使用簡化數量"""
        # 只創建2顆衛星進行測試
        initial_sat_count = min(2, self.config['satellites']['count'])
        
        for i in range(initial_sat_count):
            sat_id = f"SAT{i+1}"
            self._add_satellite_to_network(sat_id)
        
        # 初始建立基本連接
        self._setup_initial_connections()
    
    def _setup_initial_connections(self):
        """設置初始連接 - 模擬測試成功的連接模式"""
        gs_names = list(self.ground_stations.keys())
        sat_ids = list(self.satellites.keys())
        
        # 每個衛星連接到所有地面站 (類似測試中的全連接)
        for sat_id in sat_ids:
            for gs_name in gs_names:
                self._create_link(sat_id, gs_name)
        
        # 衛星間連接 (如果有多顆衛星)
        if len(sat_ids) > 1:
            for i in range(len(sat_ids) - 1):
                self._create_satellite_link(sat_ids[i], sat_ids[i+1])
    
    def _add_satellite_to_network(self, sat_id: str):
        """將衛星添加到網路中 - 確保 OpenFlow 1.3"""
        with self.network_lock:
            if sat_id not in self.satellites:
                try:
                    # 創建衛星交換機，使用簡化的交換機名稱
                    switch_name = f's{len(self.satellites)+1}'  # s1, s2, s3...
                    switch = self.net.addSwitch(
                        switch_name,
                        protocols='OpenFlow13'  # 明確指定 OpenFlow 1.3
                    )
                    self.satellites[sat_id] = switch
                    info(f"*** 添加衛星交換機: {sat_id} (交換機名: {switch_name}, OpenFlow 1.3)\n")
                    
                    # 如果網路已啟動，需要動態連接
                    if self.net.built:
                        # 動態啟動交換機
                        switch.start([self.controller])
                        # 確保使用 OpenFlow 1.3
                        switch.cmd('ovs-vsctl set bridge %s protocols=OpenFlow13' % switch_name)
                        info(f"*** 衛星 {sat_id} 動態加入網路\n")
                except Exception as e:
                    error(f"*** 添加衛星失敗 {sat_id}: {e}\n")
                    return None
            
            return self.satellites.get(sat_id)
    
    def _create_satellite_link(self, sat1_id: str, sat2_id: str):
        """創建衛星間連接 (ISL - Inter-Satellite Link)"""
        if sat1_id in self.satellites and sat2_id in self.satellites:
            sat1_switch = self.satellites[sat1_id]
            sat2_switch = self.satellites[sat2_id]
            
            try:
                # 創建高速衛星間連接
                link = self.net.addLink(
                    sat1_switch, sat2_switch,
                    bw=100,  # 100 Mbps
                    delay='5ms'  # 低延遲
                )
                info(f"*** 建立衛星間連接: {sat1_id} <-> {sat2_id}\n")
                return link
            except Exception as e:
                error(f"*** 建立衛星間連接失敗 {sat1_id} <-> {sat2_id}: {e}\n")
                return None
    
    def _remove_satellite_from_network(self, sat_id: str):
        """從網路中移除衛星"""
        if sat_id in self.satellites:
            switch = self.satellites[sat_id]
            
            # 移除所有相關連接
            links_to_remove = []
            for link_key in self.active_links.keys():
                if link_key[0] == sat_id:
                    links_to_remove.append(link_key)
            
            for link_key in links_to_remove:
                self._remove_link(link_key)
            
            # 停止交換機
            if self.net.built:
                switch.stop()
                info(f"*** 衛星 {sat_id} 離開網路\n")
            
            # 從軌道模擬器中移除
            self.orbit_simulator.remove_satellite(sat_id)
            
            # 從本地記錄中移除
            del self.satellites[sat_id]
    
    def _create_link(self, sat_id: str, gs_name: str):
        """創建衛星-地面站連接 - 使用測試成功的參數"""
        with self.network_lock:
            link_key = (sat_id, gs_name)
            
            if link_key in self.active_links:
                return  # 連接已存在
            
            if sat_id not in self.satellites or gs_name not in self.ground_stations:
                return  # 節點不存在
            
            sat_switch = self.satellites[sat_id]
            gs_host = self.ground_stations[gs_name]
            
            try:
                # 創建連接，使用測試成功的參數
                link = self.net.addLink(
                    sat_switch, gs_host,
                    bw=10,  # 與測試相同的頻寬
                    delay='20ms'  # 與測試相同的延遲
                )
                
                self.active_links[link_key] = link
                info(f"*** 建立連接: {sat_id} <-> {gs_name}\n")
            except Exception as e:
                error(f"*** 建立連接失敗 {sat_id} <-> {gs_name}: {e}\n")
    
    def _remove_link(self, link_key: Tuple[str, str]):
        """移除衛星-地面站連接"""
        with self.network_lock:
            if link_key in self.active_links:
                link = self.active_links[link_key]
                # Mininet 中動態移除連接比較複雜，這裡標記為斷開
                del self.active_links[link_key]
                sat_id, gs_name = link_key
                info(f"*** 斷開連接: {sat_id} <-> {gs_name}\n")
    
    def start_simulation(self):
        """啟動網路和模擬 - 基於測試成功的流程"""
        info("*** 啟動動態衛星網路模擬 (基於成功測試配置)\n")
        
        # 啟動 Mininet 網路
        self.net.start()
        
        # 等待控制器初始化 (與測試相同)
        info("*** 等待控制器初始化...\n")
        time.sleep(3)
        
        # 確保所有交換機使用 OpenFlow 1.3
        info("*** 設置 OpenFlow 1.3 協議\n")
        for sat_id, switch in self.satellites.items():
            switch.cmd('ovs-vsctl set bridge %s protocols=OpenFlow13' % switch.name)
            result = switch.cmd('ovs-vsctl get bridge %s protocols' % switch.name)
            info(f"{sat_id} ({switch.name}) 協議版本: {result}")
        
        # 檢查控制器連接狀態
        info("*** 檢查控制器連接狀態\n")
        for sat_id, switch in self.satellites.items():
            result = switch.cmd('ovs-vsctl get-controller %s' % switch.name)
            info(f"{sat_id} ({switch.name}) 控制器: {result}")
        
        # 測試初始連通性
        info("*** 測試初始網路連通性\n")
        self.net.pingAll()
        
        # 顯示流表 (用於診斷)
        info("*** 顯示初始流表\n")
        for sat_id, switch in self.satellites.items():
            info(f"\n=== {sat_id} ({switch.name}) 流表 ===\n")
            result = switch.cmd('ovs-ofctl -O OpenFlow13 dump-flows %s' % switch.name)
            info(result)
        
        # 啟動動態模擬線程 (可選)
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        info("*** 動態模擬已啟動\n")
        info("*** 可用命令:\n")
        info("***   simulate - 查看當前狀態\n")
        info("***   add_satellite SAT3 - 添加新衛星\n")
        info("***   remove_satellite SAT2 - 移除衛星\n")
        info("***   pingall - 測試連通性\n")
        info("***   flows - 查看流表\n")
    
    def _simulation_loop(self):
        """模擬主循環 - 簡化版本"""
        update_interval = self.config['network']['update_interval']
        
        while self.simulation_running:
            current_time = time.time() - self.start_time
            
            # 簡化：只更新狀態信息，不修改網路拓撲
            self._update_satellite_status(current_time)
            
            time.sleep(update_interval)
    
    def _update_satellite_status(self, current_time: float):
        """更新衛星狀態 (僅用於狀態顯示)"""
        # 只更新狀態信息，避免動態網路修改導致的併發問題
        pass
    
    def add_satellite(self, sat_id: str):
        """動態添加衛星"""
        self.orbit_simulator.add_satellite(sat_id)
        switch = self._add_satellite_to_network(sat_id)
        
        if switch:
            # 連接到所有現有地面站
            for gs_name in self.ground_stations.keys():
                self._create_link(sat_id, gs_name)
            
            info(f"*** 衛星 {sat_id} 已加入網路並建立連接\n")
        else:
            error(f"*** 衛星 {sat_id} 加入失敗\n")
    
    def remove_satellite(self, sat_id: str):
        """動態移除衛星"""
        self._remove_satellite_from_network(sat_id)
        info(f"*** 衛星 {sat_id} 已離開網路\n")
    
    def get_network_status(self):
        """獲取網路狀態"""
        current_time = time.time() - self.start_time
        
        status = {
            'simulation_time': current_time,
            'active_satellites': [],
            'active_connections': [],
            'ground_stations': list(self.ground_stations.keys())
        }
        
        # 獲取活躍衛星
        for sat_id in self.satellites.keys():
            if self.orbit_simulator.satellites[sat_id]['active']:
                sat_pos = self.orbit_simulator.get_satellite_position(sat_id, current_time)
                visible_gs = self.orbit_simulator.calculate_visibility(sat_id, current_time)
                
                status['active_satellites'].append({
                    'id': sat_id,
                    'position': sat_pos,
                    'visible_stations': visible_gs
                })
        
        # 獲取活躍連接
        status['active_connections'] = list(self.active_links.keys())
        
        return status
    
    def stop_simulation(self):
        """停止模擬"""
        self.simulation_running = False
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.join()
        
        self.net.stop()
        info("*** 模擬已停止\n")


def custom_cli_commands(topology: DynamicSatelliteTopology):
    """為 CLI 添加自定義命令 - 包含測試命令"""
    def do_simulate(self, line):
        """顯示當前模擬狀態"""
        status = topology.get_network_status()
        info(f"\n=== 衛星網路狀態 (模擬時間: {status['simulation_time']:.1f}s) ===\n")
        
        info("活躍衛星:\n")
        for sat in status['active_satellites']:
            pos = sat['position']
            if pos:
                info(f"  {sat['id']}: 位置({pos[0]:.2f}°, {pos[1]:.2f}°, {pos[2]}km)\n")
                info(f"    可見地面站: {', '.join(sat['visible_stations'])}\n")
        
        info(f"\n活躍連接: {len(status['active_connections'])}\n")
        for conn in status['active_connections']:
            info(f"  {conn[0]} <-> {conn[1]}\n")
        info("\n")
    
    def do_add_satellite(self, line):
        """添加新衛星"""
        args = line.split()
        if len(args) != 1:
            info("用法: add_satellite <衛星ID>\n")
            return
        sat_id = args[0]
        topology.add_satellite(sat_id)
    
    def do_remove_satellite(self, line):
        """移除衛星"""
        args = line.split()
        if len(args) != 1:
            info("用法: remove_satellite <衛星ID>\n")
            return
        sat_id = args[0]
        topology.remove_satellite(sat_id)
    
    def do_flows(self, line):
        """顯示所有交換機的流表"""
        for sat_id, switch in topology.satellites.items():
            info(f"\n=== {sat_id} ({switch.name}) 流表 ===\n")
            result = switch.cmd('ovs-ofctl -O OpenFlow13 dump-flows %s' % switch.name)
            info(result)
    
    # 將命令綁定到 CLI 類
    CLI.do_simulate = do_simulate
    CLI.do_add_satellite = do_add_satellite
    CLI.do_remove_satellite = do_remove_satellite
    CLI.do_flows = do_flows


def main():
    """主函數"""
    setLogLevel('info')
    
    info("=== 動態衛星 SDN 網路模擬器 (基於成功測試配置) ===\n")
    
    try:
        # 創建拓撲
        topology = DynamicSatelliteTopology()
        
        # 添加自定義 CLI 命令
        custom_cli_commands(topology)
        
        # 啟動模擬
        topology.start_simulation()
        
        # 啟動 CLI
        CLI(topology.net)
        
    except KeyboardInterrupt:
        info("\n*** 收到中斷信號\n")
    finally:
        if 'topology' in locals():
            topology.stop_simulation()


if __name__ == '__main__':
    main() 