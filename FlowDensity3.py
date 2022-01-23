#!/usr/bin/env python
# coding: utf-8

# In[4]:


def flow_speed_plots(cameras, data, code, seg_id, cod):
    one_cam = cameras[cameras['code']==code]
    one_cam = one_cam.sort_values(by ='day_minute')
    timef = np.array(one_cam['day_minute'])
    flow = 4* np.array(one_cam['flow'])
    plt.figure()
    plt.grid(True)
    plt.scatter(timef, flow, color ='red')
    one_seg = data[data['segment_id']==seg_id]
    one_seg = one_seg.sort_values(by ='day_minute')
    timeS = np.array(one_seg['day_minute'])
    speed = np.array(one_seg['speed'])
    plt.scatter(timeS, speed, color='blue')
    
    Density = []
    Flow = []
    T = []
    for t in timef:
        if t in timeS:
            T.append(t)
    plt.show()
    for t in T:
        t1 = list(timef).index(t)
        t2 = list(timeS).index(t)
        Density.append(flow[t1]/speed[t2])
        Flow.append(flow[t1])
    
    
    
    fig, ax = plt.subplots(2, figsize = (18,8))
    fig.suptitle('Camera Code ' + str(code))
    ax[0].grid(True)
    
    ax[0].scatter(Density, Flow, color = 'red' , label = 'flow-density points from real data(Navigator) ')
    mymodel = np.poly1d(np.polyfit(Density, Flow, 2))
    Density = sorted(Density)
    ax[0].plot(Density, mymodel(Density), color = "red", label = 'interpolation of flow_density points from real data')
    
    ax[0].scatter(cod['scatter_X'], cod['scatter_Y'] , color = 'black',                  label = "flow-density points from estimated data(Cameras)" )
    ax[0].plot(cod['line_X'], cod['line_Y'], color = "black",               label = "interpolation of flow-density points from estimated data")
    ax[0].set_xlabel("Density(#cars/Km)", fontsize = 15)
    ax[0].set_ylabel("flow(#cars/hour)", fontsize = 15)
    ax[0].legend(fontsize = 12)
    
    
    
    
    
    Najafi = pd.DataFrame({'flow':cod['scatter_Y']  , 'velocity':cod['scatter_Y']/cod['scatter_X']})

    
    speedNeshan = []
    speedNajafi = []
    Flow = []
    for t in T:
        t1 = list(timef).index(t)
        t2 = list(timeS).index(t)
        
        speedNeshan.append(speed[t2])
        Flow.append(flow[t1])
        s_n = Najafi[Najafi.flow == flow[t1]]
        if len(s_n) !=0:
            speedNajafi.append(s_n['velocity'].values[0])
        else:
            speedNajafi.append(-1)
    
    
    estimation_err = 0
    neshan_mean = 0 
    counter = 0
    for i in range(len(T)):
        if speedNajafi[i]!=-1:
            counter+=1
            neshan_mean += speedNeshan[i]
            estimation_err += abs(speedNajafi[i] - speedNeshan[i])
    estimation_err /= counter
    neshan_mean /=counter
    estimation_err /= neshan_mean
    
    
    
    ax[1].grid(True)
    ax[1].plot(T, speedNeshan, color = 'red', label = "real speed from real data(Navigator)")
    ax[1].scatter(T, speedNajafi, color = 'black', label = "estimated speed(Cameras)")
    
    for i in range(len(T)):
        if speedNajafi[i]==-1:
            ax[1].scatter(T[i], speedNajafi[i], color = 'white', linewidths= 5)
    ax[1].set_xlabel("time", fontsize = 15)
    ax[1].set_ylabel("speed(Km/h)", fontsize = 15)
    ax[1].legend(fontsize = 12)
    ax[1].text(1,1,"estimation error is: " + str(round(estimation_err,3)), fontsize = 15)
    plt.savefig(str(code)+'.png')
    plt.show()
    
    return  



import csv 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


##### Reading data:
neshan_camera = pd.read_csv('neshan_camera.csv' )
data_cameras3 = pd.read_csv('data_cameras3.csv')
data_neshan3 = pd.read_csv('data_neshan3.csv')

### the list of selected camera codes: 
code_list = list(set(neshan_camera['code']))

# the length of code_list is 29, so, 
# choose a number from 0 to 28 to see different plots:
code = code_list[14]
najafiData = pd.read_csv(str(code) + '.csv')
seg_id = neshan_camera[neshan_camera['code'] == code]['segment_id'].values
seg_id = seg_id[0]


# visualization
flow_speed_plots(cameras=data_cameras3 , data =data_neshan3                      , code= code, seg_id= seg_id, cod = najafiData)


# In[ ]:




