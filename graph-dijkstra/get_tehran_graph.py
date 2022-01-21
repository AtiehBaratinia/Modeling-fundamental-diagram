import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

if __name__ == '__main__':

    cameras_df = pd.read_csv('../cameras/cameras.csv')
    lat_mn, lat_mx = cameras_df.lat.min()-0.02, cameras_df.lat.max()+0.02
    lon_mn, lon_mx = cameras_df.lon.min()-0.02, cameras_df.lon.max()+0.02

    graph = ox.graph_from_bbox(lat_mx, lat_mn, lon_mx, lon_mn, network_type='drive')
    print("Graph downloaded.")

    graph_proj = ox.project_graph(graph)
    ox.save_graphml(graph_proj, filepath='../data/tehran-network.graphml')
    print("Projected graph saved.")