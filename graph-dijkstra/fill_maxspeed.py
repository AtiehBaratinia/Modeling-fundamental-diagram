import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import numpy as np

if __name__ == '__main__':
    graph = ox.load_graphml('../data/tehran-network.graphml')
    nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True)
    
    edges['maxspeed'] = edges['maxspeed'].replace({"0": np.nan})
    mx_speeds = edges.maxspeed[edges.maxspeed.notnull()]
    for i in mx_speeds.index:
        speed = mx_speeds[i]
        if isinstance(speed, list):
            mx_speeds[i] = str(max([float(s) for s in speed]))
        elif not isinstance(speed, str):
            assert(0)
    edges.maxspeed = mx_speeds.astype('float64')

    null_idx = edges.maxspeed[edges.maxspeed.isnull()].index

    highway_maxspeed = {}
    for h in edges.highway:
        if isinstance(h, list):
            for _h in h:
                highway_maxspeed[_h] = 0
        else:
            highway_maxspeed[h] = 0

    for highway in highway_maxspeed.keys():
        highway_maxspeed[highway] = edges.maxspeed[edges.highway==highway][edges.maxspeed.notnull()].median()

    tmp = np.array(list(highway_maxspeed.values()))
    tmp = tmp[tmp==tmp]
    min_speed = tmp.min()

    for highway in highway_maxspeed.keys():
        if highway_maxspeed[highway] is np.nan:
            highway_maxspeed[highway] = min_speed

    def fill_speed(idx):
        highway = edges.highway[idx]
        if isinstance(highway, list):
            max_speed = 1111
            for h in highway:
                if highway_maxspeed[h] is not np.nan:
                    max_speed = min(max_speed, highway_maxspeed[h])
            if max_speed == 0:
                max_speed = np.nan
        else:
            max_speed = highway_maxspeed[highway]
        return max_speed
        
    G = nx.MultiDiGraph(nx.read_graphml('../data/tehran-network.graphml', node_type=int))
    for idx in null_idx:
        u, v, key = edges.u[idx], edges.v[idx], edges.key[idx]
        edge_data = G.get_edge_data(u, v)[key]
        edge_data['maxspeed'] = str(fill_speed(idx))
    nx.write_graphml(G, 'tehran-network.graphml')