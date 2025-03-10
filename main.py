import collections
if not hasattr(collections, 'MutableMapping'):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, tcp, udp, icmp
from ryu.lib import hub
from ryu.app.wsgi import WSGIApplication

# Import the REST API component
from rest_api import RestAPI

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    # Add REST API and WSGI as required applications
    _CONTEXTS = {
        'wsgi': WSGIApplication,
        'rest_api': RestAPI
    }

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = {}  # 初始化MAC地址表
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Connect REST API to the main application
        wsgi = kwargs['wsgi']
        self.rest_api = kwargs.get('rest_api')
        if self.rest_api:
            self.rest_api.set_main_app(self)
            print("Main application connected to REST API")
            self.logger.info("Main application connected to REST API")

    def _monitor(self):
        while True:
            try:
                for dp in list(self.datapaths.values()):
                    if dp.is_active:
                        self._request_stats(dp)
                hub.sleep(10)
            except Exception as e:
                self.logger.error("Monitor thread error: %s", e)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('Switch joined: datapath-%016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == 'disconnect':
            if datapath.id in self.datapaths:
                self.logger.warning('Switch left: datapath-%016x', datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, MAIN_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # 安裝ARP處理規則（優先級2）
        arp_match = parser.OFPMatch(eth_type=0x0806)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 2, arp_match, actions)

        # 安裝IPv4處理規則（優先級1）
        ip_match = parser.OFPMatch(eth_type=0x0800)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 1, ip_match, actions)

        # 預設規則（優先級0）
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        
        eth = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        arp_pkt = pkt.get_protocol(arp.arp)
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        udp_pkt = pkt.get_protocol(udp.udp)
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        in_port = msg.match['in_port']

        self.logger.info("\n=== 收到封包 ===")
        self.logger.info("MAC: %s -> %s", eth.src, eth.dst)
        
        # MAC地址學習
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][eth.src] = in_port

        if arp_pkt:
            # 學習來源端MAC地址
            self.mac_to_port[datapath.id][arp_pkt.src_mac] = in_port
            
            if arp_pkt.opcode == arp.ARP_REQUEST:
                self.logger.info("ARP Request: %s -> %s", arp_pkt.src_ip, arp_pkt.dst_ip)
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                
                # 安裝雙向轉發規則
                match = parser.OFPMatch(
                    eth_type=0x0806,
                    arp_spa=arp_pkt.src_ip,
                    arp_tpa=arp_pkt.dst_ip
                )
                self.add_flow(datapath, 5, match, actions)
                
                # 發送封包
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=actions,
                    data=msg.data
                )
                datapath.send_msg(out)
                return
            else:
                # 處理ARP回應
                if arp_pkt.dst_mac in self.mac_to_port[datapath.id]:
                    out_port = self.mac_to_port[datapath.id][arp_pkt.dst_mac]
                    actions = [parser.OFPActionOutput(out_port)]
                    
                    # 安裝雙向轉發規則
                    match = parser.OFPMatch(
                        eth_type=0x0806,
                        arp_spa=arp_pkt.src_ip,
                        arp_tpa=arp_pkt.dst_ip
                    )
                    self.add_flow(datapath, 5, match, actions)
                    
                    # 轉發ARP回應
                    out = parser.OFPPacketOut(
                        datapath=datapath,
                        buffer_id=ofproto.OFP_NO_BUFFER,
                        in_port=in_port,
                        actions=actions,
                        data=msg.data
                    )
                    datapath.send_msg(out)
                    return
        elif ip_pkt:
            # 根據學習的MAC地址轉發
            if eth.dst in self.mac_to_port[datapath.id]:
                out_port = self.mac_to_port[datapath.id][eth.dst]
            else:
                out_port = ofproto.OFPP_FLOOD
                
            actions = [parser.OFPActionOutput(out_port)]
            
            # 安裝IP轉發規則
            match = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_src=ip_pkt.src,
                ipv4_dst=ip_pkt.dst,
                ip_proto=ip_pkt.proto
            )
            self.add_flow(datapath, 10, match, actions)

            # 立即轉發封包
            data = None if msg.buffer_id == ofproto.OFP_NO_BUFFER else msg.data
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data
            )
            datapath.send_msg(out)

            proto_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
            proto = proto_map.get(ip_pkt.proto, 'Unknown')
            self.logger.info("IP: %s -> %s 協定: %s", ip_pkt.src, ip_pkt.dst, proto)
            
            if tcp_pkt:
                self.logger.info("TCP 端口: %d -> %d", tcp_pkt.src_port, tcp_pkt.dst_port)
            elif udp_pkt:
                self.logger.info("UDP 端口: %d -> %d", udp_pkt.src_port, udp_pkt.dst_port)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(
            datapath=datapath,
            table_id=0,
            out_port=datapath.ofproto.OFPP_ANY,
            out_group=datapath.ofproto.OFPG_ANY,
            match=parser.OFPMatch(),
            flags=0
        )
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        if not ev.msg.body:
            return

        self.logger.info("\n=== 流量統計 (%d 筆記錄) ===", len(ev.msg.body))
        for stat in sorted(ev.msg.body, key=lambda x: x.packet_count, reverse=True):
            if stat.packet_count == 0:
                continue

            match_info = {
                'eth_src': stat.match.get('eth_src', 'N/A'),
                'eth_dst': stat.match.get('eth_dst', 'N/A'),
                'ip_src': stat.match.get('ipv4_src', stat.match.get('arp_spa', 'N/A')),
                'ip_dst': stat.match.get('ipv4_dst', stat.match.get('arp_tpa', 'N/A')),
                'proto': self._get_protocol_info(stat.match)
            }

            self.logger.info(
                "[%s] %s(%s) -> %s(%s)\n封包數: %-6d 位元組: %-6d",
                match_info['proto'],
                match_info['ip_src'], match_info['eth_src'],
                match_info['ip_dst'], match_info['eth_dst'],
                stat.packet_count,
                stat.byte_count
            )

    def _get_protocol_info(self, match):
        if match.get('eth_type') == 0x0806:
            return 'ARP'
        elif match.get('icmpv4_type'):
            return 'ICMP'
        elif match.get('tcp_src'):
            return f"TCP/{match.get('tcp_src')}-{match.get('tcp_dst')}"
        elif match.get('udp_src'):
            return f"UDP/{match.get('udp_src')}-{match.get('udp_dst')}"
        elif match.get('eth_type') == 0x0800:
            return 'IPv4'
        return 'Unknown'

if __name__ == '__main__':
    from ryu import cfg
    cfg.CONF(args=['--ofp-tcp-listen-port', '6653'], default_config_files=[])
    app_manager.main()
        elif match.get('tcp_src'):
            return f"TCP/{match.get('tcp_src')}-{match.get('tcp_dst')}"
        elif match.get('udp_src'):
            return f"UDP/{match.get('udp_src')}-{match.get('udp_dst')}"
        elif match.get('eth_type') == 0x0800:
            return 'IPv4'
        return 'Unknown'

if __name__ == '__main__':
    from ryu import cfg
    cfg.CONF(args=['--ofp-tcp-listen-port', '6653'], default_config_files=[])
    app_manager.main()
            self.logger.info(
                "[%s] %s(%s) -> %s(%s)\n封包數: %-6d 位元組: %-6d",
                match_info['proto'],
                match_info['ip_src'], match_info['eth_src'],
                match_info['ip_dst'], match_info['eth_dst'],
                stat.packet_count,
                stat.byte_count
            )

    def _get_protocol_info(self, match):
        if match.get('eth_type') == 0x0806:
            return 'ARP'
        elif match.get('icmpv4_type'):
            return 'ICMP'
        elif match.get('tcp_src'):
            return f"TCP/{match.get('tcp_src')}-{match.get('tcp_dst')}"
        elif match.get('udp_src'):
            return f"UDP/{match.get('udp_src')}-{match.get('udp_dst')}"
        elif match.get('eth_type') == 0x0800:
            return 'IPv4'
        return 'Unknown'

if __name__ == '__main__':
    from ryu import cfg
    cfg.CONF(args=['--ofp-tcp-listen-port', '6653'], default_config_files=[])
    app_manager.main()
    app_manager.main()