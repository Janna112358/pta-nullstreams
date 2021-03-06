#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 14:27:40 2019

@author: jgoldstein

interpolation stuff

- target times calculation
- sinc interpolatiom
"""
import numpy as np

def round_to_p2(x):
    if x < 1:
        raise ValueError('Value must be greater or equal to 1')
    p = np.log2(x)
    return int(2 ** np.ceil(p))

def get_target_times(ti, tf, fmax=0.1):
    """
    Calculate desired target times given initial time, final time and
    maximum frequency.
    
    Time step is calculated using fmax, then the number of points is rounded up
    to get a power of two.
    
    Parameters
    ----------
    ti, tf: float
        initial and final time (days)
    fmax: float
        maximum frequency used to determine time step
        default = 0.1 (days^-1)
    """
    T = tf - ti
    # target time step is given by desired fmax
    # adjust to get a power of two for the number of samples
    Dt_try = 2 * (1/fmax)
    n = round_to_p2(T / Dt_try + 1)
    #new time step will be Dt = T / (n - 1)
    target_times = np.linspace(ti, tf, num=n, endpoint=True)
    return target_times  

def sinc_interpolation(x, x_data, y_data, TNy=1.0):
    """
    http://webee.technion.ac.il/Sites/People/YoninaEldar/Info/70.pdf
    
    Parameters
    ----------
    x: NumPy Array
        target x values
    x_data: NumPy Array
        input x values
    y_data: NumPy Array
        input y values
    TNy: float
        default = 1.0
        time scale used in the interpolation,
        frequencies above f=1/2TNy are filtered out
        
    Returns
    -------
    NumPy Array:
        interpolated y values at target x values
    """
    # todo: compare with naive interpolation: calculate fourier transform
    # directly from uneven points, then ifft
    # (compare in the fourier domain with power spectrum from sinc interp)
    n = len(x_data)
    T = (max(x_data) - min(x_data)) / (n-1)
    
    #k x n (target x samples)
    shifts = np.expand_dims(x, axis=1) - x_data
    sincs = np.sinc(shifts/TNy)
    weighted_points = y_data * sincs
    # sum over samples axis
    y_interp = (T/TNy) * np.sum(weighted_points, axis=1)
    
    return y_interp

def non_uniform_ToninaEldar(x, x_data, y_data):
    """
    eq 14 + 15(a) in Tonina & Eldar
    http://webee.technion.ac.il/Sites/People/YoninaEldar/Info/70.pdf
    """
    T = max(x_data) - min(x_data)
    
    ## equation 15a
    # shifts between all pairs of sampled times, used in bottom sin in product in 15a
    sample_shifts = np.expand_dims(x_data, axis=-1) - np.expand_dims(x_data, axis=0)
    product_bottom = np.sin(np.pi*sample_shifts/T)
    # shifts between all target and sampled times, used in top sin in product in 15a
    target_shifts = np.expand_dims(x, axis=-1) - np.expand_dims(x_data, axis=0)
    product_top = np.sin(np.pi*target_shifts/T)
    # in the product in 15a
    product = np.zeros(shape=(len(x), len(x_data)))
    for i, j in np.ndindex(product.shape):
        fraction = product_top[i] / product_bottom[j]
        # in the product, we skip the term where the shift j is equal to the shift
        # in the product_bottom (this term will be -inf), set it to 1 so it has
        # no effect on the product computation
        fraction[j] = 1
        product[i, j] = np.product(fraction)
    cosine_term = np.cos(np.pi*target_shifts/T)
    weights = cosine_term * product
    
    ## equation 14
    weighted_points = y_data * weights
    interpolated = np.sum(weighted_points, axis=-1)
    return interpolated