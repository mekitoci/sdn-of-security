#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SDN Network Topology Diagram Generator
Generates visual network topology diagrams based on Mininet topology parameters
"""

import argparse
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib as mpl

def generate_topology_diagram(switch_count=3, host_count=8, filename='network_topology.png'):
    """
    Generate network topology diagram and save as image file
    
    Parameters:
        switch_count: Number of switches
        host_count: Number of hosts
        filename: Output filename
    """
    # Create an empty undirected graph
    G = nx.Graph()
    
    # Define node types and colors
    CONTROLLER_COLOR = '#FF6B6B'  # Red
    SWITCH_COLOR = '#4ECDC4'      # Cyan
    HOST_COLOR = '#F9F7F7'        # White
    LINK_COLOR = '#555555'        # Dark gray
    
    # Add controller node
    G.add_node('c0', type='controller')
    
    # Add switch nodes
    switches = [f's{i+1}' for i in range(switch_count)]
    for switch in switches:
        G.add_node(switch, type='switch')
    
    # Add host nodes
    hosts = [f'h{i+1}' for i in range(host_count)]
    for host in hosts:
        G.add_node(host, type='host')
    
    # Connect controller to all switches
    for switch in switches:
        G.add_edge('c0', switch, color=LINK_COLOR, style='dashed')
    
    # Connect switches in a linear topology
    for i in range(len(switches) - 1):
        G.add_edge(switches[i], switches[i+1], color=LINK_COLOR, style='solid')
    
    # Connect hosts evenly to switches
    for i, host in enumerate(hosts):
        switch_index = i % switch_count
        G.add_edge(host, switches[switch_index], color=LINK_COLOR, style='solid')
    
    # Set node colors
    node_colors = []
    for node in G.nodes():
        if node.startswith('c'):
            node_colors.append(CONTROLLER_COLOR)
        elif node.startswith('s'):
            node_colors.append(SWITCH_COLOR)
        else:  # host
            node_colors.append(HOST_COLOR)  
    # Set node sizes
    node_sizes = []
    for node in G.nodes():
        if node.startswith('c'):
            node_sizes.append(700)  # Controller nodes larger
        elif node.startswith('s'):
            node_sizes.append(500)  # Switch nodes medium size
        else:  # host
            node_sizes.append(300)  # Host nodes smaller
    
    # Set node shapes
    node_shapes = []
    for node in G.nodes():
        if node.startswith('c'):
            node_shapes.append('s')  # Controller as square
        elif node.startswith('s'):
            node_shapes.append('o')  # Switch as circle
        else:  # host
            node_shapes.append('o')  # Host also as circle
    
    # Set edge styles
    edge_colors = [G[u][v]['color'] for u, v in G.edges()]
    edge_styles = [G[u][v]['style'] for u, v in G.edges()]
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Set font support for English
    try:
        plt.rcParams['font.sans-serif'] = ['Arial']  # For displaying English labels
        plt.rcParams['axes.unicode_minus'] = False    # For displaying minus sign correctly
    except:
        print("Cannot set font, using default font")
    
    # Set layout
    pos = nx.spring_layout(G, seed=42)  # Use spring layout with fixed random seed for consistency
    
    # Draw nodes and edges
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    
    # Process node labels
    nx.draw_networkx_labels(G, pos, font_color='black', font_weight='bold')
    
    # Process edges, draw separately based on style attribute
    solid_edges = [(u, v) for u, v in G.edges() if G[u][v]['style'] == 'solid']
    dashed_edges = [(u, v) for u, v in G.edges() if G[u][v]['style'] == 'dashed']
    
    nx.draw_networkx_edges(G, pos, edgelist=solid_edges, width=1.5, edge_color=LINK_COLOR)
    nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, width=1.5, edge_color=LINK_COLOR, style='dashed')
    
    # Add legend
    controller_patch = mpl.patches.Patch(color=CONTROLLER_COLOR, label='Controller')
    switch_patch = mpl.patches.Patch(color=SWITCH_COLOR, label='Switch')
    host_patch = mpl.patches.Patch(color=HOST_COLOR, label='Host')
    solid_line = mpl.lines.Line2D([], [], color=LINK_COLOR, label='Data Link')
    dashed_line = mpl.lines.Line2D([], [], color=LINK_COLOR, linestyle='dashed', label='Control Link')
    
    plt.legend(handles=[controller_patch, switch_patch, host_patch, solid_line, dashed_line], 
               loc='lower right', fontsize=10)
    
    # Add title and description
    plt.title(f'SDN Network Topology ({switch_count} switches, {host_count} hosts)', fontsize=16)
    plt.text(0.5, -0.1, 
             f'Linear Topology: {" → ".join(switches)}\nHosts evenly distributed across switches', 
             horizontalalignment='center', 
             verticalalignment='center',
             transform=plt.gca().transAxes,
             fontsize=10)
    
    # Save figure and display
    plt.axis('off')  # Turn off coordinate axes
    plt.tight_layout()
    
    # Only save if filename is provided
    if filename is not None:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f'Topology diagram saved as: {filename}')
    
    return G

def generate_attack_diagram(switch_count=3, host_count=8, 
                           target_host='h8', attack_hosts=['h1', 'h2', 'h3'], 
                           attack_type='syn', filename='attack_topology.png'):
    """
    Generate attack scenario topology diagram and save as image file
    
    Parameters:
        switch_count: Number of switches
        host_count: Number of hosts
        target_host: Target host of the attack
        attack_hosts: List of hosts initiating the attack
        attack_type: Type of attack
        filename: Output filename
    """
    # First generate basic topology
    G = generate_topology_diagram(switch_count, host_count, filename=None)
    
    # Define attack-related colors
    TARGET_COLOR = '#FF0000'  # Red (attack target)
    ATTACKER_COLOR = '#FF9500'  # Orange (attacker)
    ATTACK_LINK_COLOR = '#FF5500'  # Orange-red (attack traffic)
    
    # Set node colors
    node_colors = []
    for node in G.nodes():
        if node == target_host:
            node_colors.append(TARGET_COLOR)
        elif node in attack_hosts:
            node_colors.append(ATTACKER_COLOR)
        elif node.startswith('c'):
            node_colors.append('#FF6B6B')  # Controller
        elif node.startswith('s'):
            node_colors.append('#4ECDC4')  # Switch
        else:  # Other hosts
            node_colors.append('#F9F7F7')  # White
    
    # Set node sizes
    node_sizes = []
    for node in G.nodes():
        if node == target_host or node in attack_hosts:
            node_sizes.append(600)  # Attack-related nodes larger
        elif node.startswith('c'):
            node_sizes.append(700)  # Controller nodes larger
        elif node.startswith('s'):
            node_sizes.append(500)  # Switch nodes medium size
        else:  # Other hosts
            node_sizes.append(300)  # Host nodes smaller
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Set font support for English
    try:
        plt.rcParams['font.sans-serif'] = ['Arial']  # For displaying English labels
        plt.rcParams['axes.unicode_minus'] = False    # For displaying minus sign correctly
    except:
        print("Cannot set font, using default font")
    
    # Set layout
    pos = nx.spring_layout(G, seed=42)  # Use spring layout with fixed random seed for consistency
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    
    # Process node labels
    nx.draw_networkx_labels(G, pos, font_color='black', font_weight='bold')
    
    # Process edges, first identify attack paths
    attack_edges = []
    all_edges = list(G.edges())
    
    # Find paths from attack hosts to target host
    for attack_host in attack_hosts:
        # Find the switch connected to the attack host
        for u, v in all_edges:
            if (u == attack_host and v.startswith('s')) or (v == attack_host and u.startswith('s')):
                switch = v if v.startswith('s') else u
                attack_edges.append((attack_host, switch))
                
                # Find the switch connected to the target host
                target_switch = None
                for u2, v2 in all_edges:
                    if (u2 == target_host and v2.startswith('s')) or (v2 == target_host and u2.startswith('s')):
                        target_switch = v2 if v2.startswith('s') else u2
                        
                # If attack host and target host are connected to the same switch
                if switch == target_switch:
                    attack_edges.append((switch, target_host))
                else:
                    # Find path from attack host's switch to target host's switch
                    try:
                        path = nx.shortest_path(G, switch, target_switch)
                        for i in range(len(path) - 1):
                            attack_edges.append((path[i], path[i+1]))
                        attack_edges.append((target_switch, target_host))
                    except:
                        pass
    
    # Remove duplicate edges
    attack_edges = list(set(attack_edges))
    
    # Other edges (non-attack paths)
    other_edges = [(u, v) for u, v in all_edges if (u, v) not in attack_edges and (v, u) not in attack_edges]
    control_edges = [(u, v) for u, v in other_edges if 'c0' in (u, v)]
    data_edges = [(u, v) for u, v in other_edges if 'c0' not in (u, v)]
    
    # Draw non-attack path edges
    nx.draw_networkx_edges(G, pos, edgelist=data_edges, width=1.0, edge_color='#555555')
    nx.draw_networkx_edges(G, pos, edgelist=control_edges, width=1.0, edge_color='#555555', style='dashed')
    
    # Draw attack path edges with different color and width
    nx.draw_networkx_edges(G, pos, edgelist=attack_edges, width=2.5, edge_color=ATTACK_LINK_COLOR, 
                           arrows=True, arrowsize=15, arrowstyle='->')
    
    # Add legend
    controller_patch = mpl.patches.Patch(color='#FF6B6B', label='Controller')
    switch_patch = mpl.patches.Patch(color='#4ECDC4', label='Switch')
    host_patch = mpl.patches.Patch(color='#F9F7F7', label='Normal Host')
    attacker_patch = mpl.patches.Patch(color=ATTACKER_COLOR, label='Attacker')
    target_patch = mpl.patches.Patch(color=TARGET_COLOR, label='Target')
    attack_line = mpl.lines.Line2D([], [], color=ATTACK_LINK_COLOR, linewidth=2.5, label='Attack Traffic')
    solid_line = mpl.lines.Line2D([], [], color='#555555', label='Data Link')
    dashed_line = mpl.lines.Line2D([], [], color='#555555', linestyle='dashed', label='Control Link')
    
    plt.legend(handles=[controller_patch, switch_patch, host_patch, attacker_patch, target_patch, 
                        attack_line, solid_line, dashed_line], 
               loc='lower right', fontsize=10)
    
    # Add title and description
    plt.title(f'SDN Network Attack Scenario - {attack_type.upper()} Attack Simulation', fontsize=16)
    plt.text(0.5, -0.1, 
             f'Target: {target_host}\nAttackers: {", ".join(attack_hosts)}', 
             horizontalalignment='center', 
             verticalalignment='center',
             transform=plt.gca().transAxes,
             fontsize=12)
    
    # Save figure and display
    plt.axis('off')  # Turn off coordinate axes
    plt.tight_layout()
    
    # Only save if filename is provided
    if filename is not None:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f'Attack scenario topology diagram saved as: {filename}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate SDN Network Topology Diagram')
    parser.add_argument('-s', '--switches', type=int, default=3, help='Number of switches')
    parser.add_argument('-n', '--hosts', type=int, default=8, help='Number of hosts')
    parser.add_argument('-o', '--output', type=str, default='network_topology.png', help='Output filename')
    parser.add_argument('--attack', action='store_true', help='Generate attack scenario topology diagram')
    parser.add_argument('--target', type=str, default='h8', help='Target host being attacked')
    parser.add_argument('--attackers', type=str, default='h1,h2,h3', help='Attacking hosts, separated by commas')
    parser.add_argument('--attack-type', type=str, default='syn', help='Attack type')
    
    args = parser.parse_args()
    
    if args.attack:
        attack_hosts = args.attackers.split(',')
        generate_attack_diagram(
            switch_count=args.switches,
            host_count=args.hosts,
            target_host=args.target,
            attack_hosts=attack_hosts,
            attack_type=args.attack_type,
            filename=args.output
        )
    else:
        generate_topology_diagram(
            switch_count=args.switches,
            host_count=args.hosts,
            filename=args.output
        )
