import pickle
import network
from shapely import wkt
from shapely.geometry import LineString
from pyproj import Transformer
from clickhouse_driver import Client
import sys

HOST = '31.24.233.25'
USER = 'sharif'
PASSWORD = 'other13bedar'
PORT = '9000'
DB_NAME = 'visualization'
TABLE_NAME = 'cameras_path'

weight = 'length'

if __name__ == '__main__':
    print("loading pathes...")
    with open(f"pathes-{weight}.pkl", "rb") as f:
        pathes = pickle.load(f)
    print("loading camera2node...")
    with open(f"camera2node.pkl", "rb") as f:
        camera2node = pickle.load(f)
    print("initializing network...")
    net = network.network('tehran-network-with-cameras.graphml')
    codes = list(pathes.keys())
    proj = Transformer.from_crs("EPSG:32639", "EPSG:4326", always_xy=True)
    
    client = Client(HOST, port=PORT, user=USER, password=PASSWORD)
    print("creating db if not exists...")
    client.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"
    )
    print("droping table if exists...")
    client.execute(
        f"drop table if exists {DB_NAME}.{TABLE_NAME}"
    )
    print("creating table if not exists...")
    client.execute(
                   f"CREATE TABLE IF NOT EXISTS {DB_NAME}.{TABLE_NAME}" + \
                   "("                                                  + \
                   "code_source  UInt64,"                               + \
                   "code_target  UInt64,"                               + \
                   "min_duration Float32,"                              + \
                   "length       Float32,"                              + \
                   "wkt          String"                                + \
                   ") ENGINE = MergeTree()"                             + \
                   "PARTITION BY tuple()"                               + \
                   "ORDER BY (code_source, code_target)"
    )
    print("inserting values...")
    for i in range(len(codes)):
        for j in range(len(codes)):
            route = pathes[codes[i]][codes[j]]['route']
            min_duration = pathes[codes[i]][codes[j]]['min_duration']
            length = pathes[codes[i]][codes[j]]['length']
            if len(route) != 0:
                cur = 0
                line_coords = []
                while(cur+1 < len(route)):
                    u = route[cur]
                    v = route[cur+1]
                    edge_data = net.g.get_edge_data(u, v)
                    key = list(edge_data.keys())[0]
                    mn = edge_data[key][weight]
                    for _key in edge_data:
                        if edge_data[_key][weight] < mn:
                            mn = edge_data[_key][weight]
                            key = _key
                    coords = wkt.loads(edge_data[key]['geometry']).coords
                    if cur+1 == len(route)-1:
                        line_coords += coords
                    else:
                        line_coords += coords[:-1]
                    cur += 1
                line_coords_ll = []
                for (x, y) in line_coords:
                    lon, lat = proj.transform(x, y)
                    line_coords_ll.append((lat, lon))
                route_wkt = LineString(line_coords_ll).wkt
                if route_wkt == "GEOMETRYCOLLECTION EMPTY":
                    route_wkt = "LINESTRING EMPTY"
            else:
                xi, yi = net.g.nodes[camera2node[codes[i]]]['x'], net.g.nodes[camera2node[codes[i]]]['y']
                xj, yj = net.g.nodes[camera2node[codes[j]]]['x'], net.g.nodes[camera2node[codes[j]]]['y']
                loni, lati = proj.transform(xi, yi)
                lonj, latj = proj.transform(xj, yj)
                route_wkt = LineString([(lati, loni), (latj, lonj)]).wkt
            client.execute(
                f"INSERT INTO {DB_NAME}.{TABLE_NAME} (code_source, code_target, min_duration, length, wkt) VALUES",
                [{'code_source'  : int(codes[i]), 
                  'code_target'  : int(codes[j]), 
                  'min_duration' : min_duration,
                  'length'       : length,
                  'wkt'          : route_wkt
                 }]
            )
            
            sys.stdout.write(f"\r{(i*len(codes)+j+1)/(len(codes)**2)*100:.3f}% inserted.")
            sys.stdout.flush()
    print("")

    
    