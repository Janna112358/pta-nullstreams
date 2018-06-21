#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 14:38:17 2018

@author: jgoldstein
"""

# some musings on the null stream matrix calculation using enterrpise things

import numpy as np
from enterprise.signals.utils import create_gw_antenna_pattern

def calculate_nullstream_matrix(source, pulsar_locations):
    n = len(pulsar_locations)
    if n < 3:
        raise ValueError('Can not calculate null streams for fewer than 3 pulsars')
        
    # not sure what the input format of pulsar_locations is going to be
    # for now, assuming (theta, phi) angles
    # convert this to unit vectors pointing to the locations
    
    theta, phi = pulsar_locations.T
    pulsar_vectors = np.array([np.sin(theta) * np.cos(phi), 
             np.sin(theta) * np.sin(phi), np.cos(theta)])
    
    
    # Get response functions Fplus, Fcross for each pulsar form enterprise
    # the rest is just linear algebra
    
    Fplus, Fcross, _ = create_gw_antenna_pattern(pulsar_vectors, *source)
    
    # put response functions into a matrix R (nx2), n = number of pulsars
    # R_i1 = Fplus for pulsar i, R_i2 = Fcross for pulsar i
    
    response_matrix = np.vstack((Fplus, Fcross)).T
    
    # projection matrix for the null space S (nxn)
    # S = I(nx) - R_ij R_MPinv_jk
    # where R_MPinv is the Moore-Penrose/pseudo inverse of R, which is 2xn
    
    response_mpinv = np.linalg.pinv(response_matrix)
    null_space_proj = np.eye(n) - np.einsum('ij, jk', response_matrix, 
                              response_mpinv)
    
    # Reduce S to (n-2)xn using the QR-decomposition (you can probably do this differently if you want)
    # because there's only n-2 null streams, so S is of rank n-2
    # The QR-decomposition gives S = QR, then the first n-2 columns of Q form an
    # orthonormal basis for the column vectors of S
    # Then we take this basis as the 2nd through nth row of our final matrix (so they are transposed here)
    
    q, r = np.linalg.qr(null_space_proj)
    null_stream_matrix = np.zeros((n, n))
    null_stream_matrix[2:] = q[:, :-2].T
    
    # The first two rows of M get you the reconstructed hplus and hcross
    # fill them with R_MPinv (which has two rows)
    
    null_stream_matrix[:2] = response_mpinv
    return null_stream_matrix

