# LEO卫星移动模拟系统使用指南

## 系统概述

本系统使用Ryu SDN控制器和Mininet网络仿真器来模拟低轨道(LEO)卫星的移动进出过程。通过动态网络拓扑变化，真实反映卫星网络的特点。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Configuration │    │   Orbit Data    │    │   Performance   │
│   leo_config.   │    │   satellite_    │    │   Monitoring    │
│   yaml          │    │   orbit_data.   │    │                 │
└─────────────────┘    │   json          │    └─────────────────┘
         │              └─────────────────┘              │
         │                        │                      │
         v                        v                      v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ryu SDN       │◄──►│   Mininet       │◄──►│   Real-time     │
│   Controller    │    │   Network       │    │   Statistics    │
│   leo_ryu_      │    │   Simulation    │    │                 │
│   controller.py │    │   leo_satellite_│    └─────────────────┘
└─────────────────┘    │   simulation.py │
         │              └─────────────────┘
         │                        │
         v                        v
┌─────────────────┐    ┌─────────────────┐
│   Flow Table    │    │   Dynamic       │
│   Management    │    │   Topology      │
│                 │    │   Updates       │
└─────────────────┘    └─────────────────┘
```

## 系统组件

### 1. 核心组件

- **Ryu控制器** (`leo_ryu_controller.py`): SDN控制器，管理网络流表和路由
- **Mininet拓扑** (`leo_satellite_simulation.py`): 网络仿真环境  
- **配置文件** (`leo_config.yaml`): 系统参数配置
- **轨道数据** (`satellite_orbit_data.json`): 真实的卫星轨道运行数据

### 2. 功能模块

- **轨道计算模块**: 计算卫星实时位置
- **连接性管理**: 判断卫星可见性和链路状态
- **路由优化**: 动态调整路由策略
- **性能监控**: 收集网络性能指标

## 快速开始

### 环境准备

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y python3-pip mininet openvswitch-switch

# 安装Python依赖
pip3 install ryu pyyaml

# 克隆项目
git clone <your-repo>
cd satellite/
```

### 基本使用

#### 1. 启动Ryu控制器

```bash
# 在第一个终端窗口中启动控制器
cd satellite/
ryu-manager leo_ryu_controller.py --verbose

# 控制器将在端口6653上监听OpenFlow连接
```

#### 2. 运行Mininet仿真

```bash
# 在第二个终端窗口中启动仿真
cd satellite/
sudo python3 leo_satellite_simulation.py

# 或者使用参数启动
sudo python3 leo_satellite_simulation.py --duration 600 --interval 10
```

#### 3. 监控系统状态

在Mininet CLI中可以使用以下命令：

```bash
# 查看网络拓扑
mininet> net

# 测试连通性
mininet> pingall

# 查看交换机状态
mininet> sh ovs-vsctl show

# 查看流表
mininet> sh ovs-ofctl dump-flows s1

# 启动实时监控
mininet> py net.simulation_running = True
```

## 配置说明

### leo_config.yaml 主要参数

```yaml
# 网络基本参数
network:
  simulation_duration: 3600  # 模拟持续时间（秒）
  update_interval: 5         # 更新间隔（秒）
  real_time_factor: 10       # 时间加速倍数

# 卫星参数
satellites:
  count: 12                  # 卫星数量
  altitude: 550              # 轨道高度（km）
  inclination: 53            # 轨道倾角（度）
  orbital_period: 5760       # 轨道周期（秒）

# 路由算法参数
routing:
  algorithm: "shortest_path"  # 路由算法选择
  weight_factors:
    distance: 0.4            # 距离权重
    congestion: 0.3          # 拥塞权重
    stability: 0.3           # 稳定性权重
```

## 高级功能

### 1. 性能监控

```bash
# 启用实时统计
python3 -c "
from leo_satellite_simulation import SatelliteTopology
topo = SatelliteTopology()
net = topo.create_initial_topology()
net.start()
topo.simulate_mobility(duration=300, update_interval=10)
"
```

### 2. 自定义流量测试

```bash
# 在Mininet CLI中生成测试流量
mininet> gs1 ping -c 10 gs2
mininet> iperf gs1 gs3
```

### 3. 网络切换演示

系统会自动模拟以下场景：
- 卫星进入覆盖范围（仰角 > 45°）
- 卫星离开覆盖范围（仰角 < 45°）
- 动态路由重新计算
- 流量切换和负载均衡

## 监控指标

系统自动收集以下性能指标：

1. **吞吐量** (throughput): 网络数据传输速率
2. **延迟** (latency): 端到端传输延迟
3. **丢包率** (packet_loss): 数据包丢失百分比
4. **切换频率** (handover_frequency): 卫星切换次数
5. **链路利用率** (link_utilization): 网络链路使用率

## 故障排除

### 常见问题

1. **控制器连接失败**
   ```bash
   # 检查端口是否被占用
   sudo netstat -tlnp | grep 6653
   
   # 重启控制器
   sudo pkill -f ryu-manager
   ryu-manager leo_ryu_controller.py --verbose
   ```

2. **Mininet启动失败**
   ```bash
   # 清理Mininet残留
   sudo mn -c
   
   # 重启OpenVSwitch
   sudo service openvswitch-switch restart
   ```

3. **交换机连接问题**
   ```bash
   # 检查OpenFlow版本
   sudo ovs-vsctl set bridge s1 protocols=OpenFlow13
   
   # 查看控制器连接
   sudo ovs-vsctl get-controller s1
   ```

### 日志分析

```bash
# 查看Ryu控制器日志
tail -f leo_sim.log

# 查看Mininet系统日志
dmesg | grep -i mininet

# 查看OpenVSwitch日志
sudo tail -f /var/log/openvswitch/ovs-vswitchd.log
```

## 系统扩展

### 添加新的路由算法

1. 在 `leo_ryu_controller.py` 中的 `_optimize_routing()` 方法添加新算法
2. 在 `leo_config.yaml` 中配置算法参数
3. 重启控制器应用新配置

### 增加卫星数量

1. 修改 `leo_config.yaml` 中的 `satellites.count` 参数
2. 更新 `leo_satellite_simulation.py` 中的拓扑创建逻辑
3. 调整轨道数据文件 `satellite_orbit_data.json`

### 自定义性能指标

1. 在控制器中实现新的统计收集方法
2. 修改 `leo_config.yaml` 中的监控配置
3. 添加相应的数据展示逻辑

## 技术支持

如果遇到问题，请检查：

1. Python版本 (推荐 Python 3.8+)
2. Ryu版本兼容性
3. Mininet安装完整性
4. OpenVSwitch服务状态
5. 系统防火墙设置

## 示例输出

正常运行时，您将看到类似输出：

```
INFO:LEOSatelliteController:LEO卫星网络控制器已启动
INFO:LEOSatelliteController:交换机 1 已连接
INFO:LEOSatelliteController:卫星 sat_1 已注册
创建LEO卫星网络拓扑...
添加地面站: gs1
添加地面站: gs2
添加地面站: gs3
添加卫星: s1
添加卫星: s2
时间: 0s - 更新卫星连接状态
卫星 s1 进入覆盖范围 (仰角: 67.1°)
活跃卫星: ['s1', 's3', 's5'] (3/5)
```

## 相关文档

- [Ryu SDN Framework Documentation](https://ryu.readthedocs.io/)
- [Mininet Walkthrough](http://mininet.org/walkthrough/)
- [OpenFlow 1.3 Specification](https://opennetworking.org/sdn-resources/openflow/) 