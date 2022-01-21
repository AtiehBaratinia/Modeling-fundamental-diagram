import pickle
import network
import pandas as pd
import sys

if __name__ == '__main__':
    camera2node = {}
    tehran_network = network.network('tehran-network.graphml')
    cameras_df = pd.read_csv('../cameras/cameras.csv')
    for i in range(cameras_df.shape[0]):
        code = cameras_df.iloc[i].code
        lat = cameras_df.iloc[i].lat
        lon = cameras_df.iloc[i].lon
        u = tehran_network.add_point((lat, lon))
        camera2node[code] = u
        sys.stdout.write(f"\r{i+1} camera(s) from {cameras_df.shape[0]}, added.")
        sys.stdout.flush()
        
    tehran_network.save("tehran-network-with-cameras")
    print("\nnew graph saved to /graph/tehran-network-with-cameras.graphml")

    with open("camera2node.pkl", "wb") as f:
        pickle.dump(camera2node, f)
    print("camera2node map saved to /graph/camera2node.pkl")