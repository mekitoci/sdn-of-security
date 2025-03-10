#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from webob import Response
import json
import logging
import datetime
import random
import time
import os
from collections import defaultdict, deque

# REST API 應用名稱 - 確保正確的 URL 路徑前綴
rest_app_name = 'api'
root_app_name = 'root'

class RestAPI(app_manager.RyuApp):
    """REST API 應用：為 SDN 功能提供 Web API 接口
    
    此應用實現了REST API，允許外部系統與SDN控制器交互，
    包括查詢統計信息、管理防火牆規則、處理IDS警報等。
    """
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}
    
    def __init__(self, *args, **kwargs):
        super(RestAPI, self).__init__(*args, **kwargs)
        self.logger.info("Initializing REST API application")
        
        # Get WSGI application
        self.wsgi = kwargs.get('wsgi')
        
        # Main application reference (will be set in the main application)
        self.main_app = None
        self.datapaths = {}
        
        # 用於存儲流量統計數據
        self.flow_stats = {}
        # 防止頻繁請求的時間戳記錄
        self.last_stats_request = {}
        
        # 只有當 wsgi 存在時才註冊 API 路由
        if self.wsgi:
            # Register API routes - 使用正確的名稱和 URL 前綴
            self.wsgi.register(RestAPIController, {
                rest_app_name: self,
                root_app_name: self
            })
            
            # Also register controller as a handler for the root URL
            self.wsgi.register(RootController, {root_app_name: self})
        
        self.logger.info(f"REST API endpoints registered with prefix: {RestAPIController.URL_PREFIX}")
    
    def is_real_datapath(self, dp):
        """檢查是否為真實的 Ryu Datapath 對象"""
        return hasattr(dp, 'ofproto_parser')
    
    def set_main_app(self, app):
        """設置主應用引用"""
        self.main_app = app
        self.logger.info("REST API connected to main application")
    
    def request_flow_stats(self, datapath_id=None):
        """請求指定交換機或所有交換機的流量統計信息"""
        now = time.time()
        target_datapaths = {}
        
        # 確定目標交換機
        if datapath_id and str(datapath_id) in self.datapaths:
            dp_id = str(datapath_id)
            target_datapaths[dp_id] = self.datapaths[dp_id]
        elif datapath_id is None:
            target_datapaths = self.datapaths
        else:
            self.logger.warning(f'交換機 {datapath_id} 不存在')
            return
        
        # 發送統計請求
        for dp_id, dp in target_datapaths.items():
            # 限制請求頻率 (每2秒最多請求一次)
            if now - self.last_stats_request.get(dp_id, 0) < 2:
                continue
                
            # 檢查是否為真實 Ryu Datapath，若不是則跳過請求
            if not self.is_real_datapath(dp):
                self.logger.debug(f'跳過模擬交換機 {dp_id} 的流量統計請求')
                continue
            
            self.logger.debug(f'正在向交換機 {dp_id} 請求流量統計')
            parser = dp.ofproto_parser
            req = parser.OFPFlowStatsRequest(dp, 0, dp.ofproto.OFPTT_ALL,
                                             dp.ofproto.OFPP_ANY, dp.ofproto.OFPG_ANY)
            dp.send_msg(req)
            self.last_stats_request[dp_id] = now
    
    @set_ev_cls(ofp_event.EventOFPStateChange, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def _state_change_handler(self, ev):
        """處理交換機連接和斷開事件"""
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info(f'註冊交換機: {datapath.id}')
                self.datapaths[datapath.id] = datapath
                # 初始化統計信息請求時間戳
                self.last_stats_request[datapath.id] = 0
        elif ev.state == CONFIG_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info(f'取消註冊交換機: {datapath.id}')
                del self.datapaths[datapath.id]
                if datapath.id in self.last_stats_request:
                    del self.last_stats_request[datapath.id]
                if datapath.id in self.flow_stats:
                    del self.flow_stats[datapath.id]
    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        """處理流量統計回覆"""
        body = ev.msg.body
        datapath = ev.msg.datapath
        dpid = datapath.id
        
        # 將統計數據轉換為更易於使用的格式
        flows = []
        for stat in body:
            flow = {
                'dpid': dpid,
                'table_id': stat.table_id,
                'duration_sec': stat.duration_sec,
                'duration_nsec': stat.duration_nsec,
                'priority': stat.priority,
                'idle_timeout': stat.idle_timeout,
                'hard_timeout': stat.hard_timeout,
                'cookie': stat.cookie,
                'packet_count': stat.packet_count,
                'byte_count': stat.byte_count,
                'match': {}
            }
            
            # 處理匹配字段
            for field in stat.match.fields:
                if field.header == stat.match.OXM_OF_IN_PORT:
                    flow['match']['in_port'] = field.value
                elif field.header == stat.match.OXM_OF_ETH_SRC:
                    flow['match']['eth_src'] = field.value
                elif field.header == stat.match.OXM_OF_ETH_DST:
                    flow['match']['eth_dst'] = field.value
                elif field.header == stat.match.OXM_OF_ETH_TYPE:
                    flow['match']['eth_type'] = field.value
                elif field.header == stat.match.OXM_OF_IPV4_SRC:
                    flow['match']['ipv4_src'] = field.value
                elif field.header == stat.match.OXM_OF_IPV4_DST:
                    flow['match']['ipv4_dst'] = field.value
                elif field.header == stat.match.OXM_OF_IP_PROTO:
                    flow['match']['ip_proto'] = field.value
                elif field.header == stat.match.OXM_OF_TCP_SRC:
                    flow['match']['tcp_src'] = field.value
                elif field.header == stat.match.OXM_OF_TCP_DST:
                    flow['match']['tcp_dst'] = field.value
                elif field.header == stat.match.OXM_OF_UDP_SRC:
                    flow['match']['udp_src'] = field.value
                elif field.header == stat.match.OXM_OF_UDP_DST:
                    flow['match']['udp_dst'] = field.value
                # 可以根據需要添加更多字段
            
            # 處理動作
            actions = []
            for instruction in stat.instructions:
                if instruction.type == datapath.ofproto.OFPIT_APPLY_ACTIONS:
                    for action in instruction.actions:
                        if action.type == datapath.ofproto.OFPAT_OUTPUT:
                            actions.append(f'OUTPUT:{action.port}')
                        elif action.type == datapath.ofproto.OFPAT_DROP:
                            actions.append('DROP')
                        # 其他動作類型...
            
            flow['actions'] = actions
            flows.append(flow)
        
        # 保存統計信息
        self.flow_stats[dpid] = flows
        self.logger.info(f'已更新交換機 {dpid} 的流量統計 ({len(flows)} 個流)')
    
    def get_flow_stats(self, switch_id=None):
        """獲取流量統計數據 - 供其他應用調用"""
        # 嘗試獲取最新的流量統計
        if switch_id:
            try:
                # 將switch_id轉換為數字格式
                dpid = int(switch_id) if isinstance(switch_id, str) else switch_id
                
                # 請求最新統計數據
                if str(dpid) in self.datapaths:
                    self.request_flow_stats(dpid)
                    
                # 檢查是否有現有數據
                if dpid in self.flow_stats:
                    return self.flow_stats[dpid]
            except (ValueError, KeyError) as e:
                self.logger.error(f'獲取流量統計時發生錯誤: {e}')
        else:
            # 如果沒有指定交換機，請求所有交換機的統計數據
            self.request_flow_stats()
            # 合併所有交換機的數據
            all_flows = []
            for flows in self.flow_stats.values():
                all_flows.extend(flows)
            return all_flows
        
        return []  # 如果沒有數據，返回空列表


class RootController(ControllerBase):
    """Root controller for handling the homepage"""
    
    def __init__(self, req, link, data, **config):
        super(RootController, self).__init__(req, link, data, **config)
        self.rest_app = data[root_app_name]
    
    @route(root_app_name, '/switch_manager.html', methods=['GET'])
    def get_switch_manager(self, req, **kwargs):
        """虛擬交換機管理界面"""
        import os
        html_path = os.path.join(os.path.dirname(__file__), 'switch_manager.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return Response(content_type='text/html', body=html_content)
        except Exception as e:
            self.rest_app.logger.error(f"Error serving switch_manager.html: {e}")
            return Response(status=404, body=f"File not found: {html_path}")
            
    @route(root_app_name, '/history_view.html', methods=['GET'])
    def get_history_view(self, req, **kwargs):
        """封包歷史記錄查看頁面"""
        html_path = os.path.join(os.path.dirname(__file__), 'templates', 'history_view.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return Response(content_type='text/html', body=html_content)
        except Exception as e:
            self.rest_app.logger.error(f"Error serving history_view.html: {e}")
            return Response(status=404, body=f"File not found: {html_path}")
    
    @route(root_app_name, '/', methods=['GET'])
    def get_home(self, req, **kwargs):
        """Homepage for SDN Controller"""
        html = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SDN Security Controller</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2 {
                    color: #2c3e50;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                }
                .endpoint {
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-left: 4px solid #3498db;
                    margin-bottom: 10px;
                }
                .method {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    font-size: 0.8em;
                    margin-right: 10px;
                }
                .get {
                    background-color: #2ecc71;
                }
                .post {
                    background-color: #3498db;
                }
                .delete {
                    background-color: #e74c3c;
                }
            </style>
        </head>
        <body>
            <h1>SDN Security Controller</h1>
            <p>Welcome to the SDN Security Controller Web Interface. Use the following API endpoints to interact with the controller:</p>
            
            <h2>Available API Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/system/info" target="_blank" class="api-link">
                    <strong>/api/v1/system/info</strong>
                </a>
                <p>Get system information including version and connected switches.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/switches" target="_blank" class="api-link">
                    <strong>/api/v1/switches</strong>
                </a>
                <p>Get information about all connected switches.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> 
                <a href="http://localhost:8080/api/v1/test/switches" target="_blank" class="api-link">
                    <strong>/api/v1/test/switches</strong>
                </a>
                <p>Create a virtual switch for testing.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/stats/flows" target="_blank" class="api-link">
                    <strong>/api/v1/stats/flows</strong>
                </a>
                <p>Get flow statistics from all switches.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/firewall/rules" target="_blank" class="api-link">
                    <strong>/api/v1/firewall/rules</strong>
                </a>
                <p>Get all firewall rules.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> 
                <a href="http://localhost:8080/api/v1/firewall/rules" target="_blank" class="api-link">
                    <strong>/api/v1/firewall/rules</strong>
                </a>
                <p>Add a new firewall rule.</p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> 
                <a href="javascript:void(0)" class="api-link">
                    <strong>/api/v1/firewall/rules/{rule_id}</strong>
                </a>
                <p>Delete a specific firewall rule.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/ids/alerts" target="_blank" class="api-link">
                    <strong>/api/v1/ids/alerts</strong>
                </a>
                <p>Get IDS alerts.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/anomaly/alerts" target="_blank" class="api-link">
                    <strong>/api/v1/anomaly/alerts</strong>
                </a>
                <p>Get anomaly detection alerts.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> 
                <a href="http://localhost:8080/api/v1/anomaly/reset" target="_blank" class="api-link">
                    <strong>/api/v1/anomaly/reset</strong>
                </a>
                <p>Reset anomaly learning.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> 
                <a href="http://localhost:8080/api/v1/slices" target="_blank" class="api-link">
                    <strong>/api/v1/slices</strong>
                </a>
                <p>Get network slices.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> 
                <a href="http://localhost:8080/api/v1/slices" target="_blank" class="api-link">
                    <strong>/api/v1/slices</strong>
                </a>
                <p>Create a new network slice.</p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> 
                <a href="javascript:void(0)" class="api-link">
                    <strong>/api/v1/slices/{slice_id}</strong>
                </a>
                <p>Delete a specific network slice.</p>
            </div>
        </body>
        </html>
        '''
        return Response(content_type='text/html; charset=utf-8', body=html)


class RestAPIController(ControllerBase):
    URL_PREFIX = '/api/v1'
    
    # Test switch counter for auto-generating IDs
    test_switch_counter = 1
    # 存儲封包歷史記錄
    packet_history = defaultdict(lambda: deque(maxlen=100))  # 每個交換機存儲最近100個封包記錄
    flow_history = defaultdict(lambda: deque(maxlen=50))    # 每個交換機存儲最近50個流量數據點
    """REST API 控制器：處理 HTTP 請求並與主應用交互"""
    
    def __init__(self, req, link, data, **config):
        super(RestAPIController, self).__init__(req, link, data, **config)
        self.rest_app = data[rest_app_name]
    

    #
    # 系統信息 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/system/info', methods=['GET'])
    def get_system_info(self, req, **kwargs):
        """獲取系統信息"""
        # 檢查主應用連接
        if self.rest_app.main_app:
            main_app = self.rest_app.main_app
            
            # 收集系統信息
            info = {
                'version': '1.0.0',
                'switches': len(main_app.datapaths),
                'switch_ids': list(main_app.datapaths.keys()),
                'modules': [
                    'firewall', 'ids', 'anomaly_detection', 'network_slice'
                ]
            }
        else:
            # 返回樣本數據用於測試
            info = {
                'version': '1.0.0',
                'switches': 0,
                'switch_ids': [],
                'modules': [
                    'firewall', 'ids', 'anomaly_detection', 'network_slice'
                ],
                'status': 'test_mode'
            }
        
        return self._json_response(info)
    
    #
    # 交換機 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/switches', methods=['GET'])
    def get_switches(self, req, **kwargs):
        """獲取所有交換機信息"""
        try:
            # 直接使用 rest_app 的 datapaths 或 main_app 的 datapaths
            if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'datapaths'):
                main_app = self.rest_app.main_app
                self.rest_app.logger.info(f"Using main_app's datapaths with {len(main_app.datapaths)} entries")
                datapaths = main_app.datapaths
            else:
                self.rest_app.logger.info(f"Using rest_app's datapaths with {len(self.rest_app.datapaths)} entries")
                datapaths = self.rest_app.datapaths
            
            switches = []
            for dpid, dp in datapaths.items():
                # 嘗試獲取交換機的 IP 地址
                if hasattr(dp, 'socket') and dp.socket:
                    socket_address = dp.socket.getpeername() if hasattr(dp.socket, 'getpeername') else None
                    address = socket_address[0] if socket_address else getattr(dp, 'address', None)
                else:
                    address = getattr(dp, 'address', None)
                
                # 如果找不到地址，檢查其他可能的屬性
                if not address and hasattr(dp, 'id'):
                    # 嘗試根據 DataPath ID 格式化地址
                    if isinstance(dp.id, int) and dp.id > 0:
                        # 從 DPID 構造假 IP 地址（僅用於顯示）
                        last_octet = dp.id & 0xFF
                        address = f"192.168.0.{last_octet}"
                
                switch_info = {
                    'id': dpid,
                    'address': address if address else 'unknown',
                    'is_active': getattr(dp, 'is_active', True),
                    'ports': getattr(dp, 'ports', {}),
                    'virtual': getattr(dp, 'virtual', False),
                    'dpid': getattr(dp, 'id', None)
                }
                switches.append(switch_info)
            
            self.rest_app.logger.info(f"Returning info for {len(switches)} switches")
            return self._json_response({'switches': switches})
        except Exception as e:
            self.rest_app.logger.error(f"Error in get_switches: {e}")
            return self._error_response(500, f"Internal Server Error: {str(e)}")
            
    @route(rest_app_name, f'{URL_PREFIX}/test/switches', methods=['POST'])
    def create_test_switch(self, req, **kwargs):
        """創建測試模擬交換機"""
        try:
            # 確保 datapaths 字典存在
            if not hasattr(self.rest_app, 'datapaths'):
                self.rest_app.datapaths = {}
            
            # 解析請求主體 (如果存在)
            switch_data = {}
            if req.body:
                try:
                    switch_data = json.loads(req.body.decode('utf-8'))
                except json.JSONDecodeError:
                    # 使用默認值
                    pass
                    
            # 生成唯一開關 ID
            switch_id = switch_data.get('id', f"s{RestAPIController.test_switch_counter}")
            RestAPIController.test_switch_counter += 1
            
            # 創建虛擬交換機
            import time
            mock_switch = {
                'address': switch_data.get('address', '127.0.0.1'),
                'is_active': True,
                'ports': switch_data.get('ports', {
                    '1': {'hw_addr': '00:00:00:00:00:01', 'name': 'eth1'},
                    '2': {'hw_addr': '00:00:00:00:00:02', 'name': 'eth2'}
                }),
                'virtual': True,
                'added_at': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            # 添加到 datapaths 集合中
            self.rest_app.datapaths[switch_id] = mock_switch
            self.rest_app.logger.info(f"Created mock switch with ID: {switch_id}")
            
            return self._json_response({
                'success': True,
                'message': f"Mock switch created with ID: {switch_id}",
                'switch': {
                    'id': switch_id,
                    **mock_switch
                },
                'total_switches': len(self.rest_app.datapaths)
            })
            
        except Exception as e:
            self.rest_app.logger.error(f"Error creating mock switch: {e}")
            return self._error_response(500, f"Failed to create mock switch: {str(e)}")
    
    @route(rest_app_name, f'{URL_PREFIX}/test/switches/{{switch_id}}', methods=['DELETE'])
    def delete_test_switch(self, req, **kwargs):
        """刪除測試模擬交換機"""
        try:
            # 獲取交換機ID
            switch_id = kwargs.get('switch_id')
            if not switch_id:
                return self._error_response(400, "Missing switch_id parameter")
            
            # 診斷信息
            self.rest_app.logger.info(f"Received DELETE request for switch: {switch_id}")
            self.rest_app.logger.info(f"All kwargs: {kwargs}")

            # 確保 datapaths 字典存在
            if not hasattr(self.rest_app, 'datapaths'):
                self.rest_app.logger.error(f"datapaths dictionary not found")
                return self._error_response(404, f"Switch {switch_id} not found")
            
            # 檢查交換機是否存在
            self.rest_app.logger.info(f"Available switches: {list(self.rest_app.datapaths.keys())}")
            if switch_id not in self.rest_app.datapaths:
                self.rest_app.logger.error(f"Switch {switch_id} not found in datapaths")
                return self._error_response(404, f"Switch {switch_id} not found")
            
            # 寬魅化檢查 - 允許刪除任何存在的交換機
            switch = self.rest_app.datapaths[switch_id]
            
            # 刪除交換機
            removed_switch = self.rest_app.datapaths.pop(switch_id)
            self.rest_app.logger.info(f"Deleted mock switch with ID: {switch_id}")
            
            return self._json_response({
                'success': True,
                'message': f"Mock switch {switch_id} deleted successfully",
                'deleted_switch': {
                    'id': switch_id,
                    **removed_switch
                },
                'remaining_switches': len(self.rest_app.datapaths)
            })
        except Exception as e:
            self.rest_app.logger.error(f"Error deleting mock switch: {e}")
            return self._error_response(500, f"Failed to delete mock switch: {str(e)}")
    
    # 創建相容性DELETE端點依對接口參數
    @route(rest_app_name, f'{URL_PREFIX}/test/switches/delete', methods=['POST', 'DELETE'])
    def delete_test_switch_compat(self, req, **kwargs):
        """相容性對接點允許不同形式的刪除請求"""
        try:
            # 如果是POST請求，嘗試獲取JSON陳述的switch_id
            if req.method == 'POST' and req.body:
                try:
                    data = json.loads(req.body.decode('utf-8'))
                    switch_id = data.get('switch_id')
                except json.JSONDecodeError:
                    switch_id = None
            else:
                # 偵測查詢參數
                switch_id = req.GET.get('switch_id')
            
            if not switch_id:
                return self._error_response(400, "Missing switch_id parameter")
            
            self.rest_app.logger.info(f"Compat endpoint: deleting switch {switch_id}")
            
            # 確保 datapaths 字典存在
            if not hasattr(self.rest_app, 'datapaths'):
                self.rest_app.logger.error(f"datapaths dictionary not found")
                return self._error_response(404, f"Switch {switch_id} not found")
                
            # 檢查交換機是否存在
            if switch_id not in self.rest_app.datapaths:
                self.rest_app.logger.error(f"Switch {switch_id} not found in datapaths")
                return self._error_response(404, f"Switch {switch_id} not found")
                
            # 刪除交換機
            removed_switch = self.rest_app.datapaths.pop(switch_id)
            self.rest_app.logger.info(f"Deleted mock switch with ID: {switch_id} (compat endpoint)")
            
            return self._json_response({
                'success': True,
                'message': f"Mock switch {switch_id} deleted successfully",
                'deleted_switch': {
                    'id': switch_id,
                    **removed_switch
                },
                'remaining_switches': len(self.rest_app.datapaths)
            })
        except Exception as e:
            self.rest_app.logger.error(f"Error in compat delete endpoint: {e}")
            return self._error_response(500, f"Failed to delete mock switch: {str(e)}")

    #
    # 流量統計 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/stats/flows', methods=['GET'])
    def get_flow_stats(self, req, **kwargs):
        """獲取流量統計信息"""
        # 獲取請求參數
        switch_id = req.GET.get('switch') if hasattr(req, 'GET') else None
        force_sample = req.GET.get('sample', '').lower() == 'true' if hasattr(req, 'GET') else False
        self.rest_app.logger.info(f"Get flow stats request for switch: {switch_id}, force_sample: {force_sample}")
        
        # 優先嘗試獲取真實的流量統計數據（除非明確要求使用樣本數據）
        real_stats = []
        if not force_sample:
            # 直接從 RestAPI 實例獲取真實統計數據
            try:
                # 請求獲取最新的流量統計
                self.rest_app.request_flow_stats(switch_id)
                
                # 等待短暫時間讓統計數據更新（最多等待0.5秒）
                time.sleep(0.5)
                
                # 從流量統計緩存中獲取數據
                if switch_id:
                    try:
                        dpid = int(switch_id) if isinstance(switch_id, str) else switch_id
                        
                        # 檢查是否為真實 Ryu Datapath，若不是則跳過請求
                        if switch_id in self.rest_app.datapaths and not self.rest_app.is_real_datapath(self.rest_app.datapaths[switch_id]):
                            self.rest_app.logger.debug(f'跳過模擬交換機 {switch_id} 的流量統計請求')
                            return self._json_response({
                                'success': True,
                                'message': f"Mock switch {switch_id} does not support real flow stats",
                                'switch_id': switch_id,
                                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'is_real_data': False
                            })
                        
                        if dpid in self.rest_app.flow_stats:
                            real_stats = self.rest_app.flow_stats[dpid]
                    except (ValueError, KeyError) as e:
                        self.rest_app.logger.warning(f"無法獲取交換機 {switch_id} 的統計數據: {e}")
                else:
                    # 如果沒有指定交換機，合併所有統計數據
                    for flows in self.rest_app.flow_stats.values():
                        real_stats.extend(flows)
                
                if real_stats and len(real_stats) > 0:
                    self.rest_app.logger.info(f"返回 {len(real_stats)} 條真實流量統計記錄")
                    
                    # 保存流量統計歷史記錄
                    now = datetime.datetime.now()
                    if switch_id and len(real_stats) > 0:
                        # 計算總封包數和位元組數
                        total_packets = sum(flow.get('packet_count', 0) for flow in real_stats)
                        total_bytes = sum(flow.get('byte_count', 0) for flow in real_stats)
                        
                        history_entry = {
                            'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
                            'total_packets': total_packets,
                            'total_bytes': total_bytes,
                            'active_flows': len(real_stats)
                        }
                        
                        # 記錄當前統計數據
                        stats_info = f"\n==== 真實流量統計資料 ({now.strftime('%H:%M:%S')}) ====\n" \
                                    f"Switch ID: {switch_id}\n" \
                                    f"Total packets: {total_packets:,}\n" \
                                    f"Total bytes: {total_bytes:,}\n" \
                                    f"Active flows: {len(real_stats)}"
                        
                        print(stats_info)
                        self.rest_app.logger.info(f"真實流量統計: 交換機 {switch_id}, {len(real_stats)} 個流, {total_packets:,} 個封包, {total_bytes:,} 位元組")
                        
                        # 計算變化量
                        if switch_id in RestAPIController.flow_history and RestAPIController.flow_history[switch_id]:
                            last_history = RestAPIController.flow_history[switch_id][-1]
                            last_packets = last_history.get('total_packets', 0)
                            last_bytes = last_history.get('total_bytes', 0)
                            last_time = datetime.datetime.strptime(last_history.get('timestamp'), "%Y-%m-%d %H:%M:%S")
                            time_diff = (now - last_time).total_seconds()
                            
                            # 計算變化量
                            delta_packets = total_packets - last_packets
                            delta_bytes = total_bytes - last_bytes
                            
                            # 計算速率並儲存到歷史記錄中
                            if time_diff > 0:
                                packets_per_second = delta_packets / time_diff
                                bytes_per_second = delta_bytes / time_diff
                                
                                # 將速率數據添加到歷史記錄中
                                history_entry['packets_per_second'] = packets_per_second
                                history_entry['bytes_per_second'] = bytes_per_second
                                
                                change_info = f"\n==== 變化量計算 ====\n" \
                                            f"Time difference: {time_diff:.2f} seconds\n" \
                                            f"Packet count change: {delta_packets:,} ({packets_per_second:.2f} pps)\n" \
                                            f"Byte count change: {delta_bytes:,} ({bytes_per_second:.2f} Bps)\n" \
                                            f"===================="
                                
                                print(change_info)
                                self.rest_app.logger.info(f"流量變化率: 交換機 {switch_id}, {packets_per_second:.2f} pps, {bytes_per_second:.2f} Bps")
                        
                        # 儲存歷史記錄
                        RestAPIController.flow_history[switch_id].append(history_entry)
                    
                    # 返回真實數據
                    return self._json_response({
                        'flows': real_stats, 
                        'success': True, 
                        'switch_id': switch_id,
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'has_history': bool(RestAPIController.flow_history.get(switch_id)) if switch_id else False,
                        'is_real_data': True
                    })
            except Exception as e:
                self.rest_app.logger.error(f"獲取真實流量統計時發生錯誤: {str(e)}")
                # 如果出錯，繼續獲取模擬數據
            
            # 備用策略：嘗試通過主應用獲取流量統計（舊方法，保留兼容性）
            if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'get_flow_stats'):
                try:
                    real_stats = self.rest_app.main_app.get_flow_stats(switch_id)
                    if real_stats and len(real_stats) > 0:
                        # 如果有真實數據就直接返回
                        self.rest_app.logger.info(f"從主應用返回 {len(real_stats)} 條真實流量統計記錄")
                        return self._json_response({
                            'flows': real_stats, 
                            'success': True, 
                            'switch_id': switch_id,
                            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'is_real_data': True
                        })
                except Exception as e:
                    self.rest_app.logger.error(f"從主應用獲取流量統計時發生錯誤: {str(e)}")
        
        # 測試模式或無真實數據時 - 返回模擬流量統計
        # 找到指定的交換機或所有交換機
        datapaths = getattr(self.rest_app, 'datapaths', {})
        if switch_id and switch_id in datapaths:
            datapaths = {switch_id: datapaths[switch_id]}
        
        flows = []
        protocol_types = [
            {'eth_type': 0x0800, 'name': 'IPv4'},
            {'eth_type': 0x0806, 'name': 'ARP'},
            {'eth_type': 0x86DD, 'name': 'IPv6'},
            {'eth_type': 0x8100, 'name': 'VLAN'}
        ]
        
        # 常見協議端口
        tcp_ports = [80, 443, 22, 3389, 8080, 8443, 25, 53, 5432, 3306]
        udp_ports = [53, 67, 68, 123, 161, 162, 514, 1900, 5353]
        
        # 網絡前綴
        networks = ['10.0.0', '192.168.1', '172.16.0', '10.10.0']
        
        for dpid, dp in datapaths.items():
            # 獲取交換機的端口數量
            port_count = len(getattr(dp, 'ports', {}))
            if port_count == 0:
                port_count = 4  # 默認端口數
                
            # 生成8-15個不同的流規則
            flow_count = random.randint(8, 15) if not switch_id else random.randint(10, 20)
            for i in range(1, flow_count + 1):
                # 隨機選擇協議類型
                protocol = random.choice(protocol_types)
                
                # 基本流規則
                flow = {
                    'dpid': dpid,
                    'table_id': random.randint(0, 2),
                    'priority': random.randint(0, 65535),
                    'idle_timeout': random.choice([0, 30, 60, 300, 600]),
                    'hard_timeout': random.choice([0, 1800, 3600, 7200]),
                    'packet_count': random.randint(100, 500000),
                    'byte_count': random.randint(10000, 50000000),
                    'duration_sec': random.randint(60, 86400),  # 1分鐘到1天
                    'actions': []
                }
                
                # 決定流向 - 進入或離開
                flow_direction = random.choice(['ingress', 'egress'])
                
                # 創建真實的動作
                if flow_direction == 'egress':
                    output_port = random.randint(1, port_count)
                    flow['actions'] = [f'OUTPUT:{output_port}']
                else:
                    # 其他可能的動作
                    actions = [
                        'DROP',
                        f'SET_QUEUE:{random.randint(1, 3)}',
                        f'SET_VLAN_VID:{random.randint(100, 999)}',
                        'NORMAL'
                    ]
                    flow['actions'] = [random.choice(actions)]
                
                # 創建匹配條件
                match = {
                    'in_port': random.randint(1, port_count),
                    'eth_type': protocol['eth_type']
                }
                
                # 添加特定協議的匹配條件
                if protocol['name'] == 'IPv4':
                    src_net = random.choice(networks)
                    dst_net = random.choice(networks)
                    while dst_net == src_net:  # 確保源和目的不同
                        dst_net = random.choice(networks)
                    
                    match['ipv4_src'] = f'{src_net}.{random.randint(1, 254)}'
                    match['ipv4_dst'] = f'{dst_net}.{random.randint(1, 254)}'
                    
                    # 添加TCP/UDP特定匹配
                    if random.random() < 0.7:  # 70%的概率添加傳輸層協議
                        if random.random() < 0.6:  # 60%概率使用TCP
                            match['ip_proto'] = 6  # TCP
                            match['tcp_src'] = random.choice(tcp_ports)
                            match['tcp_dst'] = random.choice(tcp_ports)
                        else:
                            match['ip_proto'] = 17  # UDP
                            match['udp_src'] = random.choice(udp_ports)
                            match['udp_dst'] = random.choice(udp_ports)
                
                elif protocol['name'] == 'ARP':
                    # ARP特定匹配
                    match['arp_op'] = random.choice([1, 2])  # 1=請求, 2=回應
                    match['arp_spa'] = f'{random.choice(networks)}.{random.randint(1, 254)}'
                    match['arp_tpa'] = f'{random.choice(networks)}.{random.randint(1, 254)}'
                
                elif protocol['name'] == 'IPv6':
                    # 簡化的IPv6地址
                    ipv6_prefixes = ['2001:db8::', 'fe80::', 'fd00::']
                    match['ipv6_src'] = f'{random.choice(ipv6_prefixes)}{random.randint(1, 9999)}'
                    match['ipv6_dst'] = f'{random.choice(ipv6_prefixes)}{random.randint(1, 9999)}'
                
                elif protocol['name'] == 'VLAN':
                    # VLAN特定匹配
                    match['vlan_vid'] = random.randint(1, 4094)
                
                # 添加MAC地址匹配 (50%概率)
                if random.random() < 0.5:
                    octets = [format(random.randint(0, 255), '02x') for _ in range(6)]
                    match['eth_src'] = ':'.join(octets)
                if random.random() < 0.5:
                    octets = [format(random.randint(0, 255), '02x') for _ in range(6)]
                    match['eth_dst'] = ':'.join(octets)
                
                flow['match'] = match
                flows.append(flow)
        
        # 保存流量統計歷史記錄
        now = datetime.datetime.now()
        if switch_id and len(flows) > 0:
            # 計算總封包數和位元組數
            total_packets = sum(flow.get('packet_count', 0) for flow in flows)
            total_bytes = sum(flow.get('byte_count', 0) for flow in flows)
            
            history_entry = {
                'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'active_flows': len(flows)
            }
            
            # 使用日誌系統記錄當前統計數據，同時保留控制台輸出以便調試
            stats_info = f"\n==== 流量統計資料 ({now.strftime('%H:%M:%S')}) ====\n" \
                        f"Switch ID: {switch_id}\n" \
                        f"Total packets: {total_packets:,}\n" \
                        f"Total bytes: {total_bytes:,}\n" \
                        f"Active flows: {len(flows)}"
            
            print(stats_info)
            self.rest_app.logger.info(f"Flow stats for switch {switch_id}: {len(flows)} flows, {total_packets:,} packets, {total_bytes:,} bytes")
            
            # 計算變化量
            if switch_id in RestAPIController.flow_history and RestAPIController.flow_history[switch_id]:
                last_history = RestAPIController.flow_history[switch_id][-1]
                last_packets = last_history.get('total_packets', 0)
                last_bytes = last_history.get('total_bytes', 0)
                last_time = datetime.datetime.strptime(last_history.get('timestamp'), "%Y-%m-%d %H:%M:%S")
                time_diff = (now - last_time).total_seconds()
                
                # 計算變化量
                delta_packets = total_packets - last_packets
                delta_bytes = total_bytes - last_bytes
                
                # 計算速率並儲存到歷史記錄中，便於前端使用
                if time_diff > 0:
                    packets_per_second = delta_packets / time_diff
                    bytes_per_second = delta_bytes / time_diff
                    
                    # 將速率數據添加到歷史記錄中
                    history_entry['packets_per_second'] = packets_per_second
                    history_entry['bytes_per_second'] = bytes_per_second
                    
                    change_info = f"\n==== 變化量計算 ====\n" \
                                f"Time difference: {time_diff:.2f} seconds\n" \
                                f"Packet count change: {delta_packets:,} ({packets_per_second:.2f} pps)\n" \
                                f"Byte count change: {delta_bytes:,} ({bytes_per_second:.2f} Bps)\n" \
                                f"===================="
                    
                    print(change_info)
                    self.rest_app.logger.info(f"Flow rate for switch {switch_id}: {packets_per_second:.2f} pps, {bytes_per_second:.2f} Bps")
            
            # 使用 RestAPIController 中的靜態變數存儲歷史記錄
            RestAPIController.flow_history[switch_id].append(history_entry)
        
        # 添加額外的響應信息
        response_data = {
            'flows': flows,
            'success': True,
            'switch_id': switch_id,
            'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
            'has_history': bool(RestAPIController.flow_history.get(switch_id)) if switch_id else False
        }
        
        self.rest_app.logger.info(f"Returning {len(flows)} sample flow statistics")
        return self._json_response(response_data)
    
    #
    # 防火牆 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/firewall/rules', methods=['GET'])
    def get_firewall_rules(self, req, **kwargs):
        """獲取防火牆規則列表"""
        # 如果主應用已連接且防火牆模塊已啟用，獲取實際規則
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'firewall') and self.rest_app.main_app.firewall:
            return self._json_response({'rules': self.rest_app.main_app.firewall.rules})
        
        # 返回樣本防火牆規則用於測試
        sample_rules = [
            {
                'id': 1,
                'name': 'block_malicious',
                'priority': 100,
                'action': 'drop',
                'dl_type': 0x0800,  # IPv4
                'nw_src': '192.168.1.100',
                'active': True,
                'description': '阻止悡意來源的流量'
            },
            {
                'id': 2,
                'name': 'allow_web',
                'priority': 90,
                'action': 'allow',
                'dl_type': 0x0800,  # IPv4
                'nw_dst': '10.0.0.80',
                'tp_dst': 80,
                'active': True,
                'description': '允許到Web服務器的流量'
            },
            {
                'id': 3,
                'name': 'limit_ssh',
                'priority': 95,
                'action': 'allow',
                'dl_type': 0x0800,  # IPv4
                'nw_dst': '10.0.0.100',
                'tp_dst': 22,
                'active': True,
                'description': '只允許對管理伺服器的SSH連接'
            }
        ]
        
        self.rest_app.logger.info("Returning sample firewall rules for testing")
        return self._json_response({'rules': sample_rules})
    
    @route(rest_app_name, f'{URL_PREFIX}/firewall/rules', methods=['POST'])
    def add_firewall_rule(self, req, **kwargs):
        """添加防火牆規則"""
        if not self.rest_app.main_app:
            return self._error_response(503, "Main application not connected")
        
        main_app = self.rest_app.main_app
        if not hasattr(main_app, 'firewall') or not main_app.firewall:
            return self._error_response(404, "Firewall module not enabled")
        
        try:
            rule = json.loads(req.body)
            
            # 驗證規則格式
            if 'name' not in rule or 'action' not in rule:
                return self._error_response(400, "Rule missing required fields")
            
            # 添加規則
            if main_app.firewall.add_rule(rule):
                # 安裝規則到所有交換機
                for dp in main_app.datapaths.values():
                    if dp.is_active:
                        main_app.firewall.install_rules(dp)
                
                # 保存規則
                main_app.firewall.save_rules()
                
                return self._json_response({'message': 'Rule added successfully', 'rule': rule})
            else:
                return self._error_response(400, "Failed to add rule")
            
        except json.JSONDecodeError:
            return self._error_response(400, "Invalid JSON format")
        except Exception as e:
            return self._error_response(500, str(e))
    
    @route(rest_app_name, f'{URL_PREFIX}/firewall/rules/{{rule_name}}', methods=['DELETE'])
    def delete_firewall_rule(self, req, **kwargs):
        """刪除防火牆規則"""
        if not self.rest_app.main_app:
            return self._error_response(503, "Main application not connected")
        
        main_app = self.rest_app.main_app
        if not hasattr(main_app, 'firewall') or not main_app.firewall:
            return self._error_response(404, "Firewall module not enabled")
        
        rule_name = kwargs.get('rule_name')
        if not rule_name:
            return self._error_response(400, "Rule name not specified")
        
        # 刪除規則
        if main_app.firewall.remove_rule(rule_name):
            # 重新安裝規則到所有交換機
            for dp in main_app.datapaths.values():
                if dp.is_active:
                    main_app.firewall.install_rules(dp)
            
            # 保存規則
            main_app.firewall.save_rules()
            
            return self._json_response({'message': f'Rule {rule_name} deleted successfully'})
        else:
            return self._error_response(404, f"Rule {rule_name} does not exist")
    
    #
    # IDS API
    #
    @route(rest_app_name, f'{URL_PREFIX}/ids/alerts', methods=['GET'])
    def get_ids_alerts(self, req, **kwargs):
        """獲取IDS警報列表"""
        # 獲取查詢參數
        count = int(req.GET.get('count', 10))
        
        # 如果主應用已連接且IDS模塊已啟用，獲取實際警報
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'ids') and self.rest_app.main_app.ids:
            main_app = self.rest_app.main_app
            return self._json_response({'alerts': main_app.ids.get_alerts(count)})
        
        # 返回樣本IDS警報用於測試
        import datetime
        import random
        
        sample_alerts = []
        current_time = datetime.datetime.now()
        
        # 警報類型
        alert_types = [
            'Port Scan', 'SYN Flood', 'Malicious IP Access', 
            'DNS Tunneling', 'ARP Spoofing', 'SSH Brute Force'
        ]
        
        # 生成隨機警報
        for i in range(min(count, 10)):
            time_offset = datetime.timedelta(minutes=random.randint(1, 120))
            alert_time = (current_time - time_offset).strftime('%Y-%m-%dT%H:%M:%S')
            severity = random.choice(['Low', 'Medium', 'High', 'Critical'])
            alert_type = random.choice(alert_types)
            src_ip = f"192.168.1.{random.randint(2, 254)}"
            dst_ip = f"10.0.0.{random.randint(2, 254)}"
            
            sample_alerts.append({
                'id': f"test-{i+1}",
                'timestamp': alert_time,
                'type': alert_type,
                'severity': severity,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'details': f"Sample {alert_type} alert for testing",
                'test_mode': True
            })
        
        # 按时间排序
        sample_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        self.rest_app.logger.info(f"Returning {len(sample_alerts)} sample IDS alerts for testing")
        return self._json_response({'alerts': sample_alerts})
    
    #
    # 異常檢測 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/anomaly/alerts', methods=['GET'])
    def get_anomaly_alerts(self, req, **kwargs):
        """獲取異常檢測警報列表"""
        # 獲取查詢參數
        count = int(req.GET.get('count', 10))
        
        # 如果主應用已連接且異常檢測模塊已啟用，獲取實際警報
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'anomaly_detector') and self.rest_app.main_app.anomaly_detector:
            main_app = self.rest_app.main_app
            return self._json_response({'anomalies': main_app.anomaly_detector.get_anomalies(count)})
        
        # 返回樣本異常檢測警報用於測試
        import datetime
        import random
        
        sample_anomalies = []
        current_time = datetime.datetime.now()
        
        # 異常類型
        anomaly_types = [
            'Traffic Spike', 'Unusual Connection Pattern', 'New Host Activity', 
            'Bandwidth Anomaly', 'Protocol Violation', 'Suspicious Scanning'
        ]
        
        # 生成隨機異常警報
        for i in range(min(count, 10)):
            time_offset = datetime.timedelta(minutes=random.randint(1, 180))
            anomaly_time = (current_time - time_offset).strftime('%Y-%m-%dT%H:%M:%S')
            confidence = random.randint(70, 99)
            anomaly_type = random.choice(anomaly_types)
            mac_addr = f"00:{random.randint(10, 99)}:{random.randint(10, 99)}:{random.randint(10, 99)}:{random.randint(10, 99)}:{random.randint(10, 99)}"
            duration = random.randint(5, 300)
            
            sample_anomalies.append({
                'id': f"anomaly-{i+1}",
                'timestamp': anomaly_time,
                'type': anomaly_type,
                'confidence': confidence,
                'host': mac_addr,
                'duration': duration,
                'description': f"Sample {anomaly_type} detected for host {mac_addr}",
                'test_mode': True
            })
        
        # 按时间排序
        sample_anomalies.sort(key=lambda x: x['timestamp'], reverse=True)
        self.rest_app.logger.info(f"Returning {len(sample_anomalies)} sample anomaly alerts for testing")
        return self._json_response({'anomalies': sample_anomalies})
    
    @route(rest_app_name, f'{URL_PREFIX}/anomaly/reset', methods=['POST'])
    def reset_anomaly_learning(self, req, **kwargs):
        """重置異常檢測學習狀態"""
        # 如果主應用已連接且異常檢測模塊已啟用，重置實際學習狀態
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'anomaly_detector') and self.rest_app.main_app.anomaly_detector:
            main_app = self.rest_app.main_app
            main_app.anomaly_detector.reset_learning()
            return self._json_response({'message': 'Anomaly detection learning state reset successfully'})
        
        # 測試模式回應
        self.rest_app.logger.info("Reset anomaly detection learning state in test mode")
        return self._json_response({
            'message': 'Anomaly detection learning state reset successfully (TEST MODE)',
            'test_mode': True
        })
    
    #
    # 網絡切片 API
    #
    @route(rest_app_name, f'{URL_PREFIX}/slices', methods=['GET'])
    def get_network_slices(self, req, **kwargs):
        """獲取網絡切片列表"""
        # 如果主應用已連接且切片管理器已啟用，獲取實際切片列表
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'slice_manager') and self.rest_app.main_app.slice_manager:
            main_app = self.rest_app.main_app
            
            slices = []
            for slice_id, network_slice in main_app.slice_manager.slices.items():
                slice_info = {
                    'id': slice_id,
                    'priority': network_slice.priority,
                    'vlans': network_slice.vlans,
                    'hosts': [str(h) for h in network_slice.hosts],
                    'bandwidth': network_slice.bandwidth
                }
                slices.append(slice_info)
            
            return self._json_response({'slices': slices})
        
        # 返回樣本切片數據用於測試
        sample_slices = [
            {
                'id': 'premium',
                'priority': 100,
                'vlans': [10, 20],
                'hosts': ['00:00:00:00:00:01', '00:00:00:00:00:02'],
                'bandwidth': 100  # Mbps
            },
            {
                'id': 'normal',
                'priority': 50,
                'vlans': [30, 40],
                'hosts': ['00:00:00:00:00:03', '00:00:00:00:00:04'],
                'bandwidth': 50  # Mbps
            },
            {
                'id': 'economy',
                'priority': 10,
                'vlans': [50],
                'hosts': ['00:00:00:00:00:05'],
                'bandwidth': 10  # Mbps
            }
        ]
        
        self.rest_app.logger.info("Returning sample network slices for testing")
        return self._json_response({'slices': sample_slices})
    
    @route(rest_app_name, f'{URL_PREFIX}/slices', methods=['POST'])
    def create_network_slice(self, req, **kwargs):
        """創建網絡切片"""
        try:
            # 解析請求內容
            try:
                body_str = req.body.decode('utf-8') if hasattr(req.body, 'decode') else req.body
                slice_config = json.loads(body_str)
            except json.JSONDecodeError:
                return self._error_response(400, "Invalid JSON format")
            
            # 驗證配置格式
            if 'id' not in slice_config:
                return self._error_response(400, "Missing slice ID")
            
            slice_id = slice_config.get('id')
            priority = slice_config.get('priority', 10)
            vlans = slice_config.get('vlans', [])
            hosts = slice_config.get('hosts', [])
            bandwidth = slice_config.get('bandwidth', 0)
            
            # 如果主應用已連接且切片管理器已啟用，創建實際切片
            if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'slice_manager') and self.rest_app.main_app.slice_manager:
                main_app = self.rest_app.main_app
                
                # 創建切片
                if main_app.slice_manager.create_slice(slice_id, priority, vlans, hosts):
                    # 設置帶寬
                    if 'bandwidth' in slice_config:
                        main_app.slice_manager.slices[slice_id].set_bandwidth(bandwidth)
                    
                    # 保存配置
                    main_app.slice_manager.save_slices()
                    
                    return self._json_response({'message': f'Slice {slice_id} created successfully'})
                else:
                    return self._error_response(400, f"Slice {slice_id} already exists")
            
            # 測試模式 - 創建虛擬切片
            # 確保 test_slices 字典存在
            if not hasattr(self.rest_app, 'test_slices'):
                self.rest_app.test_slices = {}
                
            # 檢查是否已存在
            if slice_id in self.rest_app.test_slices:
                return self._error_response(400, f"Slice {slice_id} already exists")
                
            # 創建測試切片
            import time
            test_slice = {
                'id': slice_id,
                'priority': priority,
                'vlans': vlans,
                'hosts': hosts,
                'bandwidth': bandwidth,
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            # 保存到測試切片集合
            self.rest_app.test_slices[slice_id] = test_slice
            self.rest_app.logger.info(f"Created test network slice with ID: {slice_id}")
            
            return self._json_response({
                'success': True,
                'message': f'Test slice {slice_id} created successfully (TEST MODE)',
                'slice': test_slice
            })
                
        except Exception as e:
            self.rest_app.logger.error(f"Error creating network slice: {e}")
            return self._error_response(500, str(e))
    
    @route(rest_app_name, f'{URL_PREFIX}/slices/{{slice_id}}', methods=['DELETE'])
    def delete_network_slice(self, req, **kwargs):
        """刪除網絡切片"""
        slice_id = kwargs.get('slice_id')
        if not slice_id:
            return self._error_response(400, "Slice ID not specified")
        
        # 如果主應用已連接且切片管理器已啟用，刪除實際切片
        if self.rest_app.main_app and hasattr(self.rest_app.main_app, 'slice_manager') and self.rest_app.main_app.slice_manager:
            main_app = self.rest_app.main_app
            
            # 刪除切片
            if main_app.slice_manager.delete_slice(slice_id):
                # 保存配置
                main_app.slice_manager.save_slices()
                
                return self._json_response({'message': f'Slice {slice_id} deleted successfully'})
        
        # 測試模式 - 如果存在虛擬切片，刪除它
        if hasattr(self.rest_app, 'test_slices') and slice_id in self.rest_app.test_slices:
            # 刪除測試切片
            deleted_slice = self.rest_app.test_slices.pop(slice_id)
            self.rest_app.logger.info(f"Deleted test network slice with ID: {slice_id}")
            
            return self._json_response({
                'success': True,
                'message': f'Test slice {slice_id} deleted successfully (TEST MODE)'
            })
        
        # 如果在實際或測試模式中都沒有找到切片
        return self._error_response(404, f"Slice {slice_id} does not exist")
    
    #
    # 輔助方法
    #
    def _json_response(self, data):
        """返回JSON響應"""
        try:
            body = json.dumps(data, ensure_ascii=True)
            self.rest_app.logger.info(f"Sending JSON response: {body[:100]}...")
            response = Response(content_type='application/json; charset=utf-8', body=body)
            # 設置CORS頭，允許前端訪問
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response
        except Exception as e:
            self.rest_app.logger.error(f"Error creating JSON response: {e}")
            return self._error_response(500, f"Error creating JSON response: {str(e)}")
    
    def _error_response(self, status_code, message):
        """返回錯誤響應"""
        try:
            body = json.dumps({'error': message}, ensure_ascii=True)
            self.rest_app.logger.error(f"Sending error response: {message} (status: {status_code})")
            response = Response(
                content_type='application/json; charset=utf-8',
                body=body,
                status=status_code
            )
            # 設置CORS頭，允許前端訪問
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response
        except Exception as e:
            # 如果連 JSON 序列化都失敗，返回純文本錯誤
            self.rest_app.logger.error(f"Error creating error response: {e}")
            return Response(
                content_type='text/plain',
                body=f"Internal Server Error: {str(e)}",
                status=500
            )
