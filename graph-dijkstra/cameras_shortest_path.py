import pickle
import argparse
import glob
import network

def process_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--length", type=int, default=100)
    parser.add_argument("--merge", action="store_true", default=False)
    parser.add_argument("--weight", type=str, default="length", choices=['length', 'minduration'])
    args = parser.parse_args()
    return args

def compute(start, length, weight):
    with open("camera2node.pkl", "rb") as f:
        camera2node = pickle.load(f)
    codes = list(camera2node.keys())
    net = network.network('tehran-network-with-cameras.graphml')
    
    pathes = {}
    for i in range(start, min(start+length, len(codes))):
        src = camera2node[codes[i]]
        pathes[codes[i]] = {}
        for j in range(len(codes)):
            trg = camera2node[codes[j]]
            path = net.shortest_path(src, trg, weight)
            pathes[codes[i]][codes[j]] = path
            print(f'{((i-start)*len(codes)+j+1)/(length*len(codes)) * 100:.2f}% completed.\n', 
                  file=open(f'out/log-{start}-{min(start+length, len(codes))}.txt', 'w'))
            
    with open(f"out/pathes-{weight}-{start}-{min(start+length, len(codes))}.pkl", "wb") as f:
        pickle.dump(pathes, f)
    
if __name__ == '__main__':
    args = process_args()
    if args.merge:
        filenames = glob.glob(f"out/pathes-{args.weight}-*-*.pkl")
        pathes = {}
        for fn in filenames:
            with open(fn, "rb") as f:
                local = pickle.load(f)
                for key in local:
                    pathes[key] = local[key]
        with open(f"pathes-{args.weight}.pkl", "wb") as f:
            pickle.dump(pathes, f)
    else:
        compute(args.start, args.length, args.weight)