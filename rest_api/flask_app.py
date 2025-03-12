#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# SDN Controller API base URL
SDN_API_BASE = 'http://localhost:8080'

# 創建templates目錄
os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)

# 創建static目錄
os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)

# 首頁HTML模板
home_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDN Security Controller</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <style>
        body { padding-top: 20px; }
        .dashboard-container { margin-top: 20px; }
        .card { margin-bottom: 20px; }
        .alert-container { position: fixed; top: 20px; right: 20px; z-index: 9999; }
    </style>
</head>
<body>
    <div class="container">
        <header class="d-flex flex-wrap justify-content-center py-3 mb-4 border-bottom">
            <a href="/" class="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none">
                <span class="fs-4">SDN Security Controller</span>
            </a>
            <ul class="nav nav-pills">
                <li class="nav-item"><a href="/" class="nav-link active">Dashboard</a></li>
                <li class="nav-item"><a href="/switches" class="nav-link">Switches</a></li>
                <li class="nav-item"><a href="/flows" class="nav-link">Flows</a></li>
                <li class="nav-item"><a href="/firewall" class="nav-link">Firewall</a></li>
                <li class="nav-item"><a href="/anomalies" class="nav-link">Anomalies</a></li>
            </ul>
        </header>

        <div class="alert-container">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <div class="dashboard-container">
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">Network Overview</h5>
                        </div>
                        <div class="card-body">
                            <p>Connected Switches: <span id="switch-count">{{ switches|length }}</span></p>
                            <p>Active Flows: <span id="flow-count">{{ flows|default(0) }}</span></p>
                            <p>Last Update: <span id="last-update">{{ timestamp }}</span></p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5 class="card-title mb-0">Security Status</h5>
                        </div>
                        <div class="card-body">
                            <p>Firewall Rules: <span id="firewall-rules">{{ firewall_rules|default(0) }}</span></p>
                            <p>Anomalies Detected: <span id="anomalies">{{ anomalies|default(0) }}</span></p>
                            <p>IDS Alerts: <span id="ids-alerts">{{ ids_alerts|default(0) }}</span></p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5 class="card-title mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <a href="/switches" class="btn btn-outline-primary">View Switches</a>
                                <a href="/flows" class="btn btn-outline-primary">View Flows</a>
                                <a href="/anomalies/reset" class="btn btn-outline-warning">Reset Anomaly Detection</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if switches %}
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-dark text-white">
                            <h5 class="card-title mb-0">Connected Switches</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Switch ID</th>
                                            <th>Address</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for switch in switches %}
                                        <tr>
                                            <td>{{ switch.id }}</td>
                                            <td>{{ switch.address }}</td>
                                            <td>
                                                {% if switch.is_active %}
                                                <span class="badge bg-success">Active</span>
                                                {% else %}
                                                <span class="badge bg-danger">Inactive</span>
                                                {% endif %}
                                            </td>
                                            <td>
                                                <a href="/switches/{{ switch.id }}" class="btn btn-sm btn-info">Details</a>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-refresh dashboard every 30 seconds
        setTimeout(function() { location.reload(); }, 30000);
        
        // Dismiss alerts after 5 seconds
        setTimeout(function() {
            document.querySelectorAll('.alert').forEach(function(alert) {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
    </script>
</body>
</html>
'''

# 將模板寫入文件
with open(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'), 'w') as f:
    f.write(home_template)

# API輔助函數
def api_request(endpoint, method='GET', data=None):
    url = f"{SDN_API_BASE}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=5)
        else:
            return None, f"Unsupported HTTP method: {method}"
            
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Connection Error: {str(e)}"

# 路由定義
@app.route('/')
def index():
    # 獲取交換機信息
    switches_data, error = api_request('/api/v1/switches')
    switches = []
    if switches_data and 'switches' in switches_data:
        switches = switches_data['switches']
    
    # 獲取安全狀態信息
    firewall_data, _ = api_request('/api/v1/firewall/rules')
    firewall_rules = len(firewall_data.get('rules', [])) if firewall_data else 0
    
    anomaly_data, _ = api_request('/api/v1/anomaly/alerts')
    anomalies = len(anomaly_data.get('anomalies', [])) if anomaly_data else 0
    
    ids_data, _ = api_request('/api/v1/ids/alerts')
    ids_alerts = len(ids_data.get('alerts', [])) if ids_data else 0
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template('index.html', 
                          switches=switches, 
                          firewall_rules=firewall_rules,
                          anomalies=anomalies,
                          ids_alerts=ids_alerts,
                          timestamp=timestamp)

@app.route('/switches')
def switches():
    data, error = api_request('/api/v1/switches')
    if error:
        flash(f"Error fetching switches: {error}", "danger")
        return redirect(url_for('index'))
    
    return render_template('switches.html', switches=data.get('switches', []))

@app.route('/switches/<switch_id>')
def switch_detail(switch_id):
    # 獲取特定交換機的詳細資訊
    switches_data, error = api_request('/api/v1/switches')
    if error:
        flash(f"Error fetching switches: {error}", "danger")
        return redirect(url_for('switches'))
    
    # 查找目標交換機
    switches = switches_data.get('switches', [])
    switch = next((s for s in switches if s.get('id') == switch_id), None)
    
    if not switch:
        flash(f"Switch {switch_id} not found", "warning")
        return redirect(url_for('switches'))
    
    # 獲取此交換機的流量信息（如果可用）
    flows = []
    flows_data, _ = api_request(f'/api/v1/stats/flows?switch={switch_id}')
    if flows_data and 'flows' in flows_data:
        flows = flows_data['flows']
    
    return render_template('switch_detail.html', switch=switch, flows=flows)

@app.route('/switches/create', methods=['POST'])
def create_switch():
    # 獲取表單數據
    dpid = request.form.get('dpid') or None
    ports = request.form.get('ports', '4')
    
    # 準備API請求數據
    switch_data = {}
    if dpid:
        switch_data['id'] = dpid
    
    # 創建端口配置
    ports_config = {}
    num_ports = int(ports)
    for i in range(1, num_ports + 1):
        ports_config[str(i)] = {
            'hw_addr': f'00:00:00:00:{i:02x}:01',
            'name': f'eth{i}'
        }
    
    switch_data['ports'] = ports_config
    
    # 發送API請求
    data, error = api_request('/api/v1/test/switches', method='POST', data=switch_data)
    
    if error:
        flash(f"Error creating virtual switch: {error}", "danger")
    else:
        switch_id = data.get('switch', {}).get('id', 'unknown')
        flash(f"Virtual switch {switch_id} created successfully!", "success")
    
    return redirect(url_for('switches'))

@app.route('/switches/create-multiple', methods=['POST'])
def create_multiple_switches():
    count = int(request.form.get('count', '3'))
    created = 0
    
    for i in range(count):
        # 準備API請求數據 (使用默認設置)
        data, error = api_request('/api/v1/test/switches', method='POST', data={})
        if not error:
            created += 1
    
    if created > 0:
        flash(f"Successfully created {created} virtual switches!", "success")
    else:
        flash("Failed to create any virtual switches", "danger")
    
    return redirect(url_for('switches'))

@app.route('/switches/delete/<switch_id>', methods=['POST'])
def delete_switch(switch_id):
    print(f"Attempting to delete switch: {switch_id}")  # 调试信息
    
    # 嘗試刪除虛擬交換機
    # 檢查交換機是否存在
    switches_data, error = api_request('/api/v1/switches')
    
    if error:
        flash(f"Error checking switches: {error}", "danger")
        return redirect(url_for('switches'))
    
    # 檢查交換機是否存在 - 更宽松的检查
    switches = switches_data.get('switches', [])
    target_switch = next((s for s in switches if s.get('id') == switch_id), None)
    
    if not target_switch:
        flash(f"Switch {switch_id} not found", "warning")
        return redirect(url_for('switches'))
    
    # 列印交換機信息以帮助调试
    print(f"Target switch: {target_switch}")
    
    # 嘗試使用新的相容性端點刪除交換機
    try:
        # 使用相容性端點 - DELETE 方法使用查詢參數
        delete_url = f"/api/v1/test/switches/delete?switch_id={switch_id}"
        print(f"Trying to delete using compatibility URL: {delete_url}")  # 調試信息
        data, error = api_request(delete_url, method='DELETE')
        
        # 如果 DELETE 方法失敗，嘗試 POST 方法使用 JSON 請求體
        if error:
            print(f"DELETE method failed, trying POST method with JSON body")
            post_data = {'switch_id': switch_id}
            post_url = "/api/v1/test/switches/delete"
            data, error = api_request(post_url, method='POST', data=post_data)
            
            if error:
                # 再嘗試使用原始的端點
                print(f"POST method also failed, trying original endpoint")
                original_url = f"/api/v1/test/switches/{switch_id}"
                data, error = api_request(original_url, method='DELETE')
                
                if error:
                    # 最後嘗試直接的 requests 方法
                    print(f"All API methods failed, trying direct request")
                    import requests
                    alt_url = f"{SDN_API_BASE}/api/v1/test/switches/delete?switch_id={switch_id}"
                    response = requests.delete(alt_url, timeout=5)
                    
                    if response.status_code == 200:
                        flash(f"Virtual switch {switch_id} deleted successfully!", "success")
                        print(f"Direct request succeeded! Switch {switch_id} deleted")
                        return redirect(url_for('switches'))
                    else:
                        error = f"All delete attempts failed. Last error: {response.status_code} - {response.text}"
                        print(error)
        
        if error:
            # 提供完整的錯誤信息以便診斷
            full_error = f"Error deleting switch: {error}\nAPI URL tried: {delete_url}"
            flash(full_error, "danger")
            print(f"Delete error: {error}")  # 調試信息
        else:
            flash(f"Virtual switch {switch_id} deleted successfully!", "success")
            print(f"Switch {switch_id} deleted successfully")  # 調試信息
    
    except Exception as e:
        # 捕獲任何未預期的錯誤
        import traceback
        error_detail = traceback.format_exc()
        flash(f"Unexpected error deleting switch: {str(e)}", "danger")
        print(f"Exception: {str(e)}\n{error_detail}")  # 調試信息
    
    return redirect(url_for('switches'))

@app.route('/flows')
def flows():
    data, error = api_request('/api/v1/stats/flows')
    if error:
        flash(f"Error fetching flows: {error}", "danger")
        return redirect(url_for('index'))
    
    return render_template('flows.html', flows=data)

@app.route('/firewall')
def firewall():
    data, error = api_request('/api/v1/firewall/rules')
    if error:
        flash(f"Error fetching firewall rules: {error}", "danger")
        return redirect(url_for('index'))
    
    return render_template('firewall.html', rules=data.get('rules', []))

@app.route('/firewall/add', methods=['POST'])
def add_firewall_rule():
    rule_data = request.form.to_dict()
    data, error = api_request('/api/v1/firewall/rules', method='POST', data=rule_data)
    
    if error:
        flash(f"Error adding firewall rule: {error}", "danger")
    else:
        flash("Firewall rule added successfully", "success")
    
    return redirect(url_for('firewall'))

@app.route('/firewall/delete/<rule_name>', methods=['POST'])
def delete_firewall_rule(rule_name):
    data, error = api_request(f'/api/v1/firewall/rules/{rule_name}', method='DELETE')
    
    if error:
        flash(f"Error deleting firewall rule: {error}", "danger")
    else:
        flash("Firewall rule deleted successfully", "success")
    
    return redirect(url_for('firewall'))

@app.route('/anomalies')
def anomalies():
    data, error = api_request('/api/v1/anomaly/alerts')
    if error:
        flash(f"Error fetching anomalies: {error}", "danger")
        return redirect(url_for('index'))
    
    return render_template('anomalies.html', anomalies=data.get('anomalies', []))

@app.route('/anomalies/reset', methods=['GET', 'POST'])
def reset_anomaly_detection():
    if request.method == 'POST':
        data, error = api_request('/api/v1/anomaly/reset', method='POST')
        
        if error:
            flash(f"Error resetting anomaly detection: {error}", "danger")
        else:
            flash("Anomaly detection reset successfully", "success")
        
        return redirect(url_for('anomalies'))
    
    return render_template('reset_anomaly.html')

@app.route('/api/switches')
def api_switches():
    # 代理API請求到Ryu控制器
    data, error = api_request('/api/v1/switches')
    if error:
        return jsonify({'error': error}), 500
    return jsonify(data)

@app.route('/api/flows/<switch_id>', methods=['GET'])
def api_switch_flows(switch_id):
    """提供特定交換機的流量數據，用於圖表自動更新"""
    try:
        # 獲取交換機信息
        switches_data, error = api_request('/api/v1/switches')
        if error:
            return jsonify({'error': f"Error fetching switches: {error}"}), 500
            
        # 檢查交換機是否存在
        switches = switches_data.get('switches', [])
        target_switch = next((s for s in switches if s.get('id') == switch_id), None)
        
        if not target_switch:
            return jsonify({'error': f"Switch {switch_id} not found"}), 404
            
        # 獲取交換機的流量數據
        flows_endpoint = f"/api/v1/stats/flows"
        if not flows_endpoint.startswith('/'):
            flows_endpoint = '/' + flows_endpoint
            
        flows_data, error = api_request(flows_endpoint)
        
        if error:
            return jsonify({'error': f"Error fetching flows: {error}"}), 500
            
        # 提取此交換機的流量
        flows = []
        all_flows = flows_data.get('flows', [])
        
        for flow in all_flows:
            if flow.get('datapath_id') == switch_id:
                flows.append(flow)
                
        app.logger.info(f"Fetched {len(flows)} flows for switch {switch_id}")
        
        # 更新每個流的數據（模擬數據變化，實際使用時可以刪除）
        import random
        for flow in flows:
            # 隨機增加計數以模擬變化
            if 'packet_count' in flow:
                flow['packet_count'] += random.randint(0, 10)
            if 'byte_count' in flow:
                flow['byte_count'] += random.randint(100, 1000)
            
        return jsonify({
            'success': True,
            'switch_id': switch_id,
            'flows': flows,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        app.logger.error(f"Error in api_switch_flows: {e}")
        return jsonify({'error': str(e)}), 500

# 啟動Flask應用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)