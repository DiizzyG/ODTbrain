#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mie sphere
The *in silico* data set was created with the Mie calculation software
`GMM-field`_. The data consist of a two-dimensional projection of a
sphere with radius :math:`R=14\lambda`,
refractive index :math:`n_\mathrm{sph}=1.006`,
embedded in a medium of refractive index :math:`n_\mathrm{med}=1.0`
onto a detector which is :math:`l_\mathrm{D} = 20\lambda` away from the
center of the sphere.

The package :mod:`nrefocus` allows a better reconstruction
by numerically focusing the detected field prior to the
refractive index reconstruction and then setting :math:`l_\mathrm{D}=0`
for the reconstruction with :func:`odtbrain.backpropagate_3d`.

The figure 3D reconstruction from Mie simulations of a perfect sphere
using 200 projections. Missing angle artifacts are visible along the
:math:`y`-axis due to the :math:`2\pi`-only coverage in 3D Fourier
space.

.. _`GMM-field`: https://code.google.com/p/scatterlib/wiki/Nearfield
"""
from __future__ import division, print_function

import zipfile

import matplotlib.pylab as plt
import nrefocus
import numpy as np

import odtbrain as odt

from example_helper import get_file

datazip = get_file("mie_3d_sphere_field.zip")
# Get simulation data
arc = zipfile.ZipFile(datazip)

Ex_real = np.loadtxt(arc.open("mie_sphere_real.txt"))
Ex_imag = np.loadtxt(arc.open("mie_sphere_imag.txt"))
Ex = Ex_real + 1j * Ex_imag
# get nm, lD, res
with arc.open("mie_info.txt") as info:
    cfg = {}
    for l in info.readlines():
        l = l.decode()
        if l.count("=") == 1:
            key, val = l.split("=")
            cfg[key.strip()] = float(val.strip())

# Manually set number of angles:
A = 200

print("Example: Backpropagation from 3d Mie scattering")
print("Refractive index of medium:", cfg["nm"])
print("Measurement position from object center:", cfg["lD"])
print("Wavelength sampling:", cfg["res"])
print("Number of angles for reconstruction:", A)
print("Performing backpropagation.")

# Reconstruction angles
angles = np.linspace(0, 2 * np.pi, A, endpoint=False)

# Perform focusing
Ex, d = nrefocus.refocus(Ex,
                         d=cfg["lD"]*cfg["res"],
                         nm=cfg["nm"],
                         res=cfg["res"],
                         )

# Create sinogram
u_sin = np.tile(Ex.flat, A).reshape(A, int(cfg["size"]), int(cfg["size"]))

# Apply the Rytov approximation
u_sinR = odt.sinogram_as_rytov(u_sin)

# Backpropagation
fR = odt.backpropagate_3d(uSin=u_sinR,
                          angles=angles,
                          res=cfg["res"],
                          nm=cfg["nm"],
                          lD=0,
                          padfac=2.1)

# RI computation
nR = odt.odt_to_ri(fR, cfg["res"], cfg["nm"])

# Plotting
fig, axes = plt.subplots(2, 3, figsize=(8, 4))
axes = np.array(axes).flatten()
# field
axes[0].set_title("Mie field phase")
axes[0].set_xlabel("xD")
axes[0].set_ylabel("yD")
axes[0].imshow(np.angle(Ex), cmap=plt.cm.coolwarm)  # @UndefinedVariable
axes[1].set_title("Mie field amplitude")
axes[1].set_xlabel("xD")
axes[1].set_ylabel("yD")
axes[1].imshow(np.abs(Ex), cmap=plt.cm.gray)  # @UndefinedVariable

# line plot
axes[2].set_title("RI reconstruction, line plots")
axes[2].set_xlabel("distance [px]")
axes[2].set_ylabel("real refractive index")
center = int(cfg["size"] / 2)
x = np.arange(cfg["size"]) - center
axes[2].plot(x, nR[:, center, center].real, label="along x")
axes[2].plot(x, nR[center, center, :].real, label="along z")
axes[2].plot(x, nR[center, :, center].real, label="along y")
axes[2].legend(loc=2)
axes[2].set_xlim((-center, center))
dn = abs(cfg["nsph"] - cfg["nm"])
axes[2].set_ylim((cfg["nm"] - dn / 10, cfg["nsph"] + dn))
axes[2].ticklabel_format(useOffset=False)

# cross sections
axes[3].set_title("RI reconstruction, section at x=0")
axes[3].set_xlabel("z")
axes[3].set_ylabel("y")
axes[3].imshow(nR[center, :, :].real)

axes[4].set_title("RI reconstruction, section at y=0")
axes[4].set_xlabel("x")
axes[4].set_ylabel("z")
axes[4].imshow(nR[:, center, :].real)

axes[5].set_title("RI reconstruction, section at z=0")
axes[5].set_xlabel("y")
axes[5].set_ylabel("x")
axes[5].imshow(nR[:, :, center].real)

plt.tight_layout()
plt.show()
