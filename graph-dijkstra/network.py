import networkx as nx
import pandas as pd
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import Point, LineString, GeometryCollection
import numpy as np
import folium
import random
from rtree import index

class network:
    def __init__(self, path):
        self.g = nx.MultiDiGraph(nx.read_graphml(path, node_type=int))
        self._rtree = None
        
        for u, d in self.g.nodes(data=True):
            d['x'] = float(d['x'])
            d['y'] = float(d['y'])
            
        for u, v, d in self.g.edges(data=True):
            d['length'] = float(d['length'])
            if 'geometry' not in d:
                point_u = Point((self.g.nodes[u]['x'], self.g.nodes[u]['y']))
                point_v = Point((self.g.nodes[v]['x'], self.g.nodes[v]['y']))
                d['geometry'] = LineString([point_u, point_v]).wkt            
    
    def shortest_path(self, src, trg, weight):
        def h(u, v):
            xu, yu = self.g.nodes[u]['x'], self.g.nodes[u]['y']
            xv, yv = self.g.nodes[v]['x'], self.g.nodes[v]['y']
            return ((xu-xv)**2 + (yu-yv)**2)**0.5
        
        try:
            path = nx.astar_path(G=self.g, source=src, target=trg, heuristic=h, weight=weight)
        except:
            path = []
        if src == trg:
            min_duration = 0
            length = 0
        elif len(path) == 0:
            min_duration = np.nan
            length = np.nan
        else:
            min_duration = 0
            length = 0
            cur = 0
            while(cur+1 < len(path)):
                u = path[cur]
                v = path[cur+1]
                edge_data = self.g.get_edge_data(u, v)
                key = list(edge_data.keys())[0]
                mn = edge_data[key][weight]
                for _key in edge_data:
                    if edge_data[_key][weight] < mn:
                        mn = edge_data[_key][weight]
                        key = _key
                min_duration += edge_data[key]['minduration']
                length += edge_data[key]['length']
                if v == trg:
                    break
                cur += 1
        path_stat = {}
        path_stat['route'] = path
        path_stat['min_duration'] = min_duration
        path_stat['length'] = length
        return path_stat
        
    def nearset_edge(self, point):
        # point -> (x, y)
        
        if self._rtree is None:
            self._build_rtree()
        
        point_box = (point.x-100, point.y-100, point.x+100, point.y+100)
        close_edges_idx = self._rtree.intersection(point_box)
        edges_list = []
        for idx in close_edges_idx:
            u, v, key = self._idx2edge[idx]
            edge_data = self.g.get_edge_data(u, v, key=key)
            edge_line = wkt.loads(edge_data['geometry'])
            edges_list.append([edge_line, u, v, key])

        edges_with_distances = [
            (
                edge,
                point.distance(edge[0])
            )
            for edge in edges_list
        ]
        _, u, v, key = min(edges_with_distances, key=lambda x: x[1])[0]
        return u, v, key

    def add_point(self, loc):
        # loc -> (lat, lon)
        # return node id of inserted loc
        
        point = Point(_ll2xy(loc[0], loc[1]))        
        u, v, key = self.nearset_edge(point)
        edge_data = self.g.get_edge_data(u, v, key=key)
        
        edge_line = wkt.loads(edge_data['geometry'])
        pt_on_line = edge_line.interpolate(edge_line.project(point))
        coords = list(edge_line.coords)
        head = Point(coords[0])
        tail = Point(coords[-1])
        if (head.distance(pt_on_line) <= 1e-12):
            return u
        if  (tail.distance(pt_on_line) <= 1e-12):
            return v
        uiv_line = _split(edge_line, pt_on_line)
        ui_line, iv_line = uiv_line[0], uiv_line[1]
        i = random.randint(0, 1e7)
        while i in self.g.nodes():
            i = random.randint(0, 1e7)
            
        attr = {}
        attr['x'] = pt_on_line.x
        attr['y'] = pt_on_line.y
        
        self.g.add_node(i, **attr)
        
        ui_edge_data, iv_edge_data = {}, {}
        for key_data in edge_data:
            ui_edge_data[key_data] = edge_data[key_data]
            iv_edge_data[key_data] = edge_data[key_data]
        ui_edge_data['osmid'] = np.nan
        ui_edge_data['length'] = ui_line.length
        ui_edge_data['geometry'] = ui_line.wkt
        iv_edge_data['osmid'] = np.nan
        iv_edge_data['length'] = iv_line.length
        iv_edge_data['geometry'] = iv_line.wkt
        
        self._add_edge(u, i, 0, ui_edge_data)
        self._add_edge(i, v, 0, iv_edge_data)
        
        self._remove_edge(u, v, key)
        return i
    
    def save(self, name):
        nx.write_graphml(self.g, f'{name}.graphml')
        
    def load(self, path):
        self.g = nx.MultiDiGraph(nx.read_graphml(path, node_type=int))
    
    def _build_rtree(self):
        self._edge2idx = {}
        self._idx2edge = {}
        self._idx = 0
        self._rtree = index.Index()
        for (u, v, key, data) in self.g.edges(data=True, keys=True):
            self._edge2idx[(u, v, key)] = self._idx
            self._idx2edge[self._idx] = (u, v, key)
            self._rtree.insert(self._idx, wkt.loads(data['geometry']).bounds)
            self._idx += 1
    
    def _add_edge(self, u, v, key, data):
        self.g.add_edge(u, v, key=key, **data)
        self._edge2idx[(u, v, key)] = self._idx
        self._idx2edge[self._idx] = (u, v, key)
        self._rtree.insert(self._idx, wkt.loads(data['geometry']).bounds)
        self._idx += 1
        
    def _remove_edge(self, u, v, key):
        idx = self._edge2idx[(u, v, key)]
        data = self.g.get_edge_data(u, v, key=key)
        self._rtree.delete(idx, wkt.loads(data['geometry']).bounds)
        self._idx2edge.pop(idx)
        self._edge2idx.pop((u, v, key))
        self.g.remove_edge(u, v, key=key)
    
    def visualize_path(self, path, **args):
        route = path['route']
        length = path['length']
        min_duration = path['min_duration']
        src = route[0]
        trg = route[-1]
        
        src_color = args.pop("src_color", 'green')
        trg_color = args.pop("trg_color", 'red')
        node_color = args.pop("node_color", 'black')
        edge_color = args.pop("edge_color", 'blue')

        lines = []
        pts = []
        cur = 0
        
        if len(route) != 0:
            while(cur+1 < len(route)):
                u = route[cur]
                v = route[cur+1]
                edge_data = self.g.get_edge_data(u, v)
                edge_line = wkt.loads(edge_data[0]['geometry'])
                coords = list(edge_line.coords)
                for x, y in coords:
                    lat, lon = _xy2ll(x, y)
                    lines.append((lat, lon))
                x, y = self.g.nodes[u]['x'], self.g.nodes[u]['y']
                lat, lon = _xy2ll(x, y)
                pts.append((lat, lon))
                if v == trg:
                    x, y = self.g.nodes[v]['x'], self.g.nodes[v]['y']
                    lat, lon = _xy2ll(x, y)
                    pts.append((lat, lon))
                    break
                cur += 1
        x, y = self.g.nodes[u]['x'], self.g.nodes[u]['y']
        lat, lon = _xy2ll(x, y)
        
        m = folium.Map(location=(lat, lon), zoom_start=15)

        folium.PolyLine(lines, color=edge_color, weight=3, opacity=1, popup=f"length: {length:.2f}m, min_duration: {min_duration:.2f}s").add_to(m)

        folium.CircleMarker(location=pts[0], color=src_color, radius=3, fill=True, fill_opacity=1, popup="source").add_to(m)
        for i in range(1, len(pts)-1):
            folium.CircleMarker(location=pts[i], color=node_color, radius=1, fill=True, fill_opacity=1).add_to(m)
        folium.CircleMarker(location=pts[-1], color=trg_color, radius=3, fill=True, fill_opacity=1, popup="target").add_to(m)
        
        display(m)
        
        
def _xy2ll(x, y):
    proj = Transformer.from_crs("EPSG:32639", "EPSG:4326", always_xy=True)
    tmp = proj.transform(x, y)
    return tmp[1], tmp[0]

def _ll2xy(lat, lon):
    proj = Transformer.from_crs("EPSG:4326", "EPSG:32639", always_xy=True)
    return proj.transform(lon, lat)

def _split(line, splitter):
    distance_on_line = line.project(splitter)
    coords = list(line.coords)
    current_position = 0.0
    for i in range(len(coords)-1):
        point1 = coords[i]
        point2 = coords[i+1]
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        segment_length = (dx ** 2 + dy ** 2) ** 0.5
        current_position += segment_length
        if distance_on_line == current_position:
            # splitter is exactly on a vertex
            return GeometryCollection([
                LineString(coords[:i+2]),
                LineString(coords[i+1:])
            ])
        elif distance_on_line < current_position:
            # splitter is between two vertices
            return GeometryCollection([
                LineString(coords[:i+1] + [splitter.coords[0]]),
                LineString([splitter.coords[0]] + coords[i+1:])
            ])
    return GeometryCollection([line])