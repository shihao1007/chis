# -*- coding: utf-8 -*-
"""
Created on Mon May  6 18:35:26 2019

Convert a sequence of images into a mp4 file

Editor:
    Shihao Ran
    STIM Laboratory
"""

import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np

def anime(image, FPS, data_dir, fname, option = 'Real', autoscale = False):
    
    """
    convert a dataset into a animation and save as a mp4 file
    
    Parameters
    ----------
        image: array_like
            The input image matrix, at least has 3 dimensions
            The last dimension has to be 1 or 2
            1 stands for the image only has 1 channel, real
            2 stands for the image has 2 channel, real and imaginary
        FPS: int,
            frame per second
        data_dir: string
            the directory to save the mp4 file
        fname: string
            the name of the mp4 file
        option: "Real" or "Imaginary"
            the type of channel to plot
        autoscale: bool
            set the range of the colormap to the maximal and minimal of all
            images in the data if set to True
            otherwise the range is different for each frame
    
    Returns
    -------
        None
    """
    
    img = []
    fig = plt.figure()
    
    if image.shape[-1] == 1:
        _min, _max = np.amin(image[...,0]), np.amax(image[...,0])  
        for i in range(image.shape[0]):
            if autoscale:
                img.append([plt.imshow(image[i,:,:,0], vmin = _min, vmax = _max)])
            else:
                img.append([plt.imshow(image[i,:,:,0])])
    else:
        if option == 'Real':
            _min, _max = np.amin(image[...,0]), np.amax(image[...,0])
            for i in range(image.shape[0]):
                if autoscale:
                    img.append([plt.imshow(image[i,:,:,0], vmin = _min, vmax = _max)])
                else:
                    img.append([plt.imshow(image[i,:,:,0])])
            
        elif option == 'Imaginary':
            _min, _max = np.amin(image[...,1]), np.amax(image[...,1])
            for i in range(image.shape[0]):
                if autoscale:
                    img.append([plt.imshow(image[i,:,:,1], vmin = _min, vmax = _max)])
                else:
                    img.append([plt.imshow(image[i,:,:,1])])
            
        else:
            raise ValueError("Invalid channel type!")
    
    ani = animation.ArtistAnimation(fig,img,interval=int(1000/FPS))
    writer = animation.writers['ffmpeg'](fps=FPS)
    
    ani.save(data_dir + '\\' + fname + '.mp4',writer=writer)