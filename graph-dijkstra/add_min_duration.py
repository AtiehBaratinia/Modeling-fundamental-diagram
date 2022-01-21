import networkx as nx
import ast

if __name__ == "__main__":
    G = nx.MultiDiGraph(nx.read_graphml('tehran-network.graphml', node_type=int))
    for u, v in G.edges():
        edge_data = G.get_edge_data(u, v)
        for key in edge_data:
            mx_speed = ast.literal_eval(edge_data[key]['maxspeed'])
            if isinstance(mx_speed, list):   
                edge_data[key]['minduration'] = float(edge_data[key]['length']) /  max([float(s) for s in mx_speed])
            else:
                edge_data[key]['minduration'] = float(edge_data[key]['length']) / float(mx_speed)
    nx.write_graphml(G, 'tehran-network.graphml')
        