#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests backpropagation algorithm
"""
from __future__ import division, print_function

import numpy as np
import os
from os.path import abspath, basename, dirname, join, split, exists
import sys
import warnings
import zipfile

# Add parent directory to beginning of path variable
DIR = dirname(abspath(__file__))
sys.path = [split(DIR)[0]] + sys.path


def create_test_sino_2d(A=9, N=22, max_phase=5.0,
                        ampl_range=(1.0, 1.0)):
    """
    Creates 2D test sinogram for optical diffraction tomography.
    The sinogram is generated from a Gaussian that is shifted
    according to the rotational position of a non-centered
    object.
    
    Parameters
    ----------
    A : int
        Number of angles of the sinogram.
    N : int
        Size of one acquisition.
    max_phase : float
        Phase normalization. If this is greater than
        2PI, then it also tests the unwrapping
        capabilities of the reconstruction algorithm.
    ampl_range : tuple of floats
        Determines the min/max range of the amplitude values.
        Equal values means constant amplitude.
    """
    # initiate array
    resar = np.zeros((A, N), dtype=np.complex128)
    # 2pi coverage
    angles = np.linspace(0, 2*np.pi, A, endpoint=False)
    # x-values of Gaussain
    x = np.linspace(-N/2, N/2, N, endpoint=True)
    # SD of Gaussian
    dev = np.sqrt(N/2)
    # Off-centered rotation:
    off = N/7
    for ii in range(A):
        # Gaussian distribution sinogram
        x0 = np.cos(angles[ii])*off
        phase = np.exp(-(x-x0)**2/dev**2)
        phase = normalize(phase, vmax=max_phase)
        if ampl_range[0] == ampl_range[1]:
            # constant amplitude
            ampl = ampl_range[0]
        else:
            # ring
            ampldev = dev/5
            amploff = off*.3
            ampl1 = np.exp(-(x-x0-amploff)**2/ampldev**2)
            ampl2 = np.exp(-(x-x0+amploff)**2/ampldev**2)
            ampl = ampl1+ampl2
            ampl = normalize(ampl, vmin=ampl_range[0], vmax=ampl_range[1])
        resar[ii] = ampl*np.exp(1j*phase)
    return resar, angles


def create_test_sino_3d(A=9, Nx=22, Ny=22, max_phase=5.0,
                        ampl_range=(1.0,1.0)):
    """
    Creates 3D test sinogram for optical diffraction tomography.
    The sinogram is generated from a Gaussian that is shifted
    according to the rotational position of a non-centered
    object. The simulated rotation is about the second (y)/[1]
    axis.
    
    Parameters
    ----------
    A : int
        Number of angles of the sinogram.
    Nx : int
        Size of the first axis.
    Ny : int
        Size of the second axis.
    max_phase : float
        Phase normalization. If this is greater than
        2PI, then it also tests the unwrapping
        capabilities of the reconstruction algorithm.
    ampl_range : tuple of floats
        Determines the min/max range of the amplitude values.
        Equal values means constant amplitude.
    
    Returns
    """
    # initiate array
    resar = np.zeros((A, Ny, Nx), dtype=np.complex128)
    # 2pi coverage
    angles = np.linspace(0, 2*np.pi, A, endpoint=False)
    # x-values of Gaussain
    x = np.linspace(-Nx/2, Nx/2, Nx, endpoint=True).reshape(1,-1)
    y = np.linspace(-Ny/2, Ny/2, Ny, endpoint=True).reshape(-1,1)
    # SD of Gaussian
    dev = min(np.sqrt(Nx/2), np.sqrt(Ny/2))
    # Off-centered rotation  about second axis:
    off = Nx/7
    for ii in range(A):
        # Gaussian distribution sinogram
        x0 = np.cos(angles[ii])*off
        phase = np.exp(-(x-x0)**2/dev**2) * np.exp(-(y)**2/dev**2)
        phase = normalize(phase, vmax=max_phase)
        if ampl_range[0] == ampl_range[1]:
            # constant amplitude
            ampl = ampl_range[0]
        else:
            # ring
            ampldev = dev/5
            amploff = off*.3
            ampl1 = np.exp(-(x-x0-amploff)**2/ampldev**2)
            ampl2 = np.exp(-(x-x0+amploff)**2/ampldev**2)
            ampl = ampl1+ampl2
            ampl = normalize(ampl, vmin=ampl_range[0], vmax=ampl_range[1])
        resar[ii] = ampl*np.exp(1j*phase)
    return resar, angles


def cutout(a):
    """ cut out circle/sphere from 2D/3D square/cubic array
    """
    x = np.arange(a.shape[0])
    c = a.shape[0] / 2
    
    if len(a.shape) == 2:
        x = x.reshape(-1,1)
        y = x.reshape(1,-1)
        zero = ((x-c)**2 + (y-c)**2) < c**2
    elif len(a.shape) == 3:
        x = x.reshape(-1,1,1)
        y = x.reshape(1,-1,1)
        z = x.reshape(1,-1,1)
        zero = ((x-c)**2 + (y-c)**2 + (z-c)**2) < c**2
    else:
        raise ValueError("Cutout array must have dimension 2 or 3!")
    a *= zero
    #tool.arr2im(a, scale=True).save("test.png")
    return a

def get_test_parameter_set(set_number=1):
    res = 2.1
    lD = 0
    nm = 1.333
    parameters = []
    for i in range(set_number):
        parameters.append({"res" : res,
                           "lD" : lD,
                           "nm" : nm})
        res += .1
        lD += np.pi
        nm *= 1.01
    return parameters

def normalize(av, vmin=0, vmax=1):
    """
    normalize an array to the range vmin/vmax
    """
    if vmin == vmax:
        return np.ones_like(av)*vmin
    elif vmax < vmin:
        warnings.warn("swapping vmin and vmax, because vmax < vmin.")
        vmin, vmax = vmax, vmin
    
    norm_one = (av - np.min(av))/(np.max(av)-np.min(av))
    return norm_one * (vmax-vmin) + vmin


def get_results(frame):
    """ Get the results from the frame of a method """
    filen = frame.f_globals["__file__"]
    funcname = frame.f_code.co_name
    identifier = "{}__{}".format(filen.split("test_", 1)[1][:-3],
                                 funcname)
    wdir = join(dirname(abspath(__file__)), "data")
    text = join(wdir, identifier+".txt")
    zipf = join(wdir, identifier+".zip")
    if exists(text):
        pass
    elif exists(zipf):
        with zipfile.ZipFile(zipf) as arc:
            arc.extract(basename(text), wdir)
    else:
        raise ValueError("No results found for: {}".format(text))
    
    data = np.loadtxt(text)
    return data

def write_results(frame, r):
    """
    Used for writing the results to zip-files in the current directory.
    If put in the directory "data", these files will be used for tests.
    """
    data = np.array(r).flatten().view(float)
    filen = frame.f_globals["__file__"]
    funcname = frame.f_code.co_name
    identifier = "{}__{}".format(filen.split("test_", 1)[1][:-3],
                                 funcname)
    text = identifier+".txt"
    zipf = identifier+".zip"
    # remove existing files
    if exists(text):
        os.remove(text)
    if exists(zipf):
        os.remove(zipf)
    # save text
    np.savetxt(text, data, fmt="%.10f")
    # make zip
    with zipfile.ZipFile(zipf, "w", compression=zipfile.ZIP_DEFLATED) as arc:
        arc.write(text)
    os.remove(text)
