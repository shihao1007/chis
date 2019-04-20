# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 20:56:19 2019

Mie Scattering module for Chemical Holographic Imaging System (CHIS) library

@author: Shihao Ran
         STIM Laboratory
"""

# import packages
import numpy as np
import scipy as sp
import scipy.special
import math

def get_order(a=1, lambDa=1):
    """
    Calculate the order of the integration based on radius of the sphere
    and the wavelength of the incident field

    Parameters
    ----------
        a: radius of the sphere, float
        lambDa: wavelength of the incident field, float

    Returns
    -------
        l: order of the field, 1-D array int
    """

    # calculate the maximal order based on the Bessel function decaying
    l_max = math.ceil(2*np.pi*a/lambDa + 4*(2*np.pi*a/lambDa)**(1/3) + 2)

    # create a order vector from the maxiaml order
    l = np.arange(0, l_max+1, 1)

    return l


def coeff_b(l, k, n=1, a=1):

    """
    Calculate the B vector with respect to the sphere properties

    Note that B vector is independent to scatter matrix and only
    relys on n and a

    Parameters
    ----------
        l: order vector of the simulation, 1-D array, int
        k: wavenumber of the incident field, float
        n: refractive index (and attenuation coeff.) of the sphere, complex
        a: radius of the sphere, float

    Returns
    -------
        B: B coefficient vector, 1-D array, complex
    """

    # calculate everything related to spherical Bessel function of the 1st kind
    jka = sp.special.spherical_jn(l, k * a)
    jka_p = sp.special.spherical_jn(l, k * a, derivative=True)
    jkna = sp.special.spherical_jn(l, k * n * a)
    jkna_p = sp.special.spherical_jn(l, k * n * a, derivative=True)

    # calculate everything related to spherical Bessel funtion of the 2nd kind
    yka = sp.special.spherical_yn(l, k * a)
    yka_p = sp.special.spherical_yn(l, k * a, derivative=True)

    # calculate spherical Hankel function of the 1st kind and its derivative
    hka = jka + yka * 1j
    hka_p = jka_p + yka_p * 1j

    # calculate different terms of B
    bi = jka * jkna_p * n
    ci = jkna * jka_p
    di = jkna * hka_p
    ei = hka * jkna_p * n

    # calculate B
    B = (bi - ci) / (di - ei)

    return B

def horizontal_canvas(res, fov, z, dimention=2):
    """
    get a horizontal render space (meshgrid) for the simulation
    x, y coordinates of the grid is specified by the resolution and FOV
    and the z coordinate is specified by the z parameter

    NOTE: by defualt, the sphere being simulated should be positioned
    at the origin. If not, do not use this function

    For 1-D canvas, the length of the line is half the resolution

    Parameters
    ----------
        res: the resolution of the simulation, int
        fov: the physical field of view of the simulation, int
        z: z coordinate along the axial axis, float
        dimention: the dimention of the simulation, 1 or 2

    Returns
    -------
        rMag: the magnitude of the position vector
              corresponds to each pixel, 2-D array (res, res), float
              or 1-D array (res/2, 1), float

    """

    # get the maxiaml value of the grid (centering with 0)
    halfgrid = np.ceil(fov/2)

    if dimention == 2:
        # get x,y,z components of the position vector r
        gx = np.linspace(-halfgrid, halfgrid, res)
        gy = gx
        [x, y] = np.meshgrid(gx, gy)
        z = np.zeros((res, res)) + z

        # initialize r vectors
        rVecs = np.zeros((res, res, 3))
        # assign x,y,z components
        rVecs[...,0] = x
        rVecs[...,1] = y
        rVecs[...,2] = z

        # calculate the magnitude map of the whole plane
        rMag = np.sqrt(np.sum(rVecs**2, 2))

    elif dimention == 1:
        # locate the center pixel
        center = int(np.ceil(res/2))

        # range of x, y
        gx = np.linspace(-halfgrid, +halfgrid, res)[:center+1]
        gy = gx[0]

        # calculate the distance matrix
        rMag = np.sqrt(gx**2+gy**2+z**2)

    else:
        raise ValueError('The dimention of the canvas is invalid!')

    return rMag

def pad(res, fov, padding=0):
    """
    Pad the rendering plane to make the simulation bigger
    The padded image is 2*padding+1 times larger than the original image

    Parameters
    ----------
        res: resolution of the original image, int
        fov: physical field of view of the original image, int
        padding: padding coefficient, int

    Returns
    -------
        simRes: simulation resolution, int
        simFov: simulation field of view, int
    """

    return int(res*(padding*2+1)), int(fov*(padding*2+1))

def asymptotic_hankel(x, l):
    """
    Calculate the asymptotic form of the Hankel function for all orders in
    order vector l

    Parameters
    ----------
        x: array like input data, 2-D array, float
        l: order vector, 1-D array, int

    Returns
    -------
        hl_sym: asymptotic form of the hankel values 3-D array
                (x.shape, l.shape)
    """
    if np.isscalar(l):
        raise ValueError('Please set l as an order vector, not scalar!')
    
    # initialize the return
    if x.ndim == 1:
        hl_asym = np.zeros((x.shape[0], l.shape[0]),
                           dtype = np.complex128)

    elif x.ndim == 2:
        hl_asym = np.zeros((x.shape[0], x.shape[1], l.shape[0]),
                           dtype = np.complex128)

    # calculate the values for each order
    for i in l:
        hl_asym[..., i] = np.exp(1j*(x-i*math.pi/2))/(1j * x)

    return hl_asym

def asymptotic_legendre(res, fov, l, dimention=2):
    """
    Calculate the asymptotic form of the Legendre Polynomial

    Parameters
    ----------
        res: resolution of the simulation, int
        fov: physical field of view, int
        l: order vector, 1-D array, int
        dimention: dimention of the simulation, 1 or 2

    Returns
    -------
        pl_cos_theta: 3-D array, float, (res, res, len(l))
    """
    # get the frequency components
    if dimention == 2:
        fx = np.fft.fftfreq(res, fov/res)
        fy = fx

        # create a meshgrid in the Fourier Domain
        [kx, ky] = np.meshgrid(fx, fy)
        # calculate the sum of kx ky components so we can calculate
        # cos_theta in the Fourier Domain later
        kxky = kx**2 + ky**2

    elif dimention == 1:
        fx = np.fft.fftfreq(res, fov/res)[:int(res/2)+1]
        fy = fx[0]

        kxky = fx**2 + fy**2
    else:
        raise ValueError('The dimention of the simulation is invalid!')


    # create a mask where the sum of kx^2 + ky^2 is
    # bigger than 1 (where kz is not defined)
    mask = kxky > 1
    # mask out the sum
    kxky[mask] = 0
    # calculate cos theta in Fourier domain
    cos_theta = np.sqrt(1 - kxky)
    cos_theta[mask] = 0
    # calculate the Legendre Polynomial term
    pl_cos_theta = sp.special.eval_legendre(l, cos_theta[..., None])
    # mask out the light that is propagating outside of the objective
    pl_cos_theta[mask] = 0

    return pl_cos_theta

def near_filed_legendre(res, fov, z, k_dir, l, dimention=2):
    """
    calculate the legendre polynomial for near field simulation
    
    FIXME: this has only 2-D case
    
    """
    halfgrid = np.ceil(fov/2)
    # range of x, y
    gx = np.linspace(-halfgrid, +halfgrid, res)
    gy = gx
    [x, y] = np.meshgrid(gx, gy)     
    # make it a plane at z = 0 on the Z axis
    z = np.zeros((res, res,)) + z
    
    # initialize r vectors in the space
    rVecs = np.zeros((res, res, 3))
    # make x, y, z components
    rVecs[:,:,0] = x
    rVecs[:,:,1] = y
    rVecs[:,:,2] = z
    # compute the rvector relative to the sphere
    rVecs_ps = rVecs
    
    # calculate the distance matrix
    rMag = np.sqrt(np.sum(rVecs_ps ** 2, 2))
    
    # normalize the r vectors    
    rNorm = rVecs_ps / rMag[...,None]
    
    # compute cos(theta)
    cos_theta = np.dot(rNorm, k_dir)
    
    # compute the legendre polynomial
    plcos = sp.special.eval_legendre(l, cos_theta[..., None])
    
    return plcos


def scatter_matrix(res, fov, z, a, lambDa, dimention=2,
                   option='far', k_dir=None):
    """
    calculate the scatter matrix

    Parameters
    ----------
        res:    resolution of the simulation, int
        fov:    physical field of view of the simulation, int
        z:      z coordinate of the rendering plane, assuming
                this is a horizontal simulation
                
        k_dir:  propagation direction of the incident planewave
        a:      radius of the sphere
        lambDa: wavelength of the incident field
        dimention: dimention of the simulation, 1 or 2
        option: for near field or far field simulation, near or far

    Returns
    -------
        scatter_matrix: 3-D array, complex, (res, res, len(l))
    """

    # the maximal order
    l = get_order(a, lambDa)

    # construct the evaluate plane
    rMag = horizontal_canvas(res, fov, z, dimention)
    kMag = 2 * np.pi / lambDa

    # calculate k dot r
    kr = kMag * rMag

    # if for far field simulation
    if option == 'far':
        # calculate the Legendre polynomial in frequency domain
        pl_cos_theta = asymptotic_legendre(res, fov, l, dimention)
        # calculate the asymptotic form of hankel funtions
        hlkr = asymptotic_hankel(kr, l)
    
    # if for near field simulation
    elif option == 'near':
        # calculate them normaly
        pl_cos_theta = near_filed_legendre(res, fov, z, k_dir, l, dimention)
        jkr = sp.special.spherical_jn(l, kr[..., None])
        ykr = sp.special.spherical_yn(l, kr[..., None])
        hlkr = jkr + ykr * 1j
    else:
        raise ValueError('Please specify far field or near field!')
    
    # calculate the prefix alpha term
    alpha = (2*l + 1) * 1j ** l
    # calculate the matrix besides B vector
    scatter = hlkr * pl_cos_theta * alpha

    return scatter

def near_field(res, fov, a, n, lambDa, z, k_dir):
    """
    Calculate the 2-D near field image

    Parameters
    ----------
        res:    resolution of the simulation
        fov:    physical field of the view of the simulation
        z:      z coordinate of the rendering plane, assuming
                this is a horizontal simulation
        a:      radius of the sphere
        n:      material property of the sphere
        lambDa: wavelength of the incident field
        k_dir:  propagation direction

    Returns:
        E_near:  2-D array, complex
    """
    l = get_order(a, lambDa)
    
    k = 2*np.pi/lambDa
    
    B = coeff_b(l, k, n, a)
    
    scatter_near = scatter_matrix(res, fov, z, a, lambDa, 2, 'near', k_dir)
    
    E_near = np.sum(scatter_near * B, axis=-1)
    
    return E_near



def far_field(res, fov, z, a, n, lambDa, scale, dimention=2):
    """
    Calculate the far field image

    Parameters
    ----------
        res:    resolution of the simulation
        fov:    physical field of the view of the simulation
        z:      z coordinate of the rendering plane, assuming
                this is a horizontal simulation
        a:      radius of the sphere
        n:      material property of the sphere
        lambDa: wavelength of the incident field
        scale:  scale factor to scale up the simulated intensity
        dimention: dimention of the simulation, 1 or 2

    Returns:
        E_far:  2-D or 1-D array, complex
    """

    # the maximal order
    l = get_order(a, lambDa)

    # the wavenumber
    k = 2*np.pi/lambDa

    # calculate B coefficient
    B = coeff_b(l, k, n, a)

    # calculate the matrix besides B vector
    scatter = scatter_matrix(res, fov, z, a, lambDa, dimention)

    # calculate every order of the integration
    Sum = scatter * B
    # integrate through all the orders to get 
    # the farfield in the Fourier Domain
    E_far_shifted = np.sum(Sum, axis = -1) * scale

    if dimention == 2:
        # shift the Forier transform of 
        # the scatttering field for visualization
        E_far = np.fft.ifftshift(E_far_shifted)
    elif dimention == 1:
        E_far = E_far_shifted

    return E_far

def far2near(far_field):
    """
    Calculate the near field simulation from the far field image

    Parameters
    ----------
        far_field: the far field simulation, 2-D array, complex

    Returns
    -------
        near_field: the near field image, 2-D array, complex
    """

    near_field = np.fft.ifftshift(np.fft.ifft2(np.fft.fftshift(far_field)))

    return near_field

def bandpass_filter(res, fov, NA_in, NA_out, dimention=2):
    """
    Create a bandpass filter in the Fourier domain based on the
    back numberical aperture (NA) of the objective

    A bandpass filter in the Foureir domain is essentially a
    cocentric circle with inner and outer radius specified
    by center obscuration and back aperture
    Anything blocked by the objective will be masked as zeros

    Parameters
    ----------
        res:    resolution of the simulation
        fov:    physical field of view
        NA_in:  center obscuration of the objective
        NA_out: back aperture of the objective
        dimention: dimention of the simulation

    Returns
    -------
        bpf:    bandpass filter, 2-D or 1-D array, int (1/0)
    """

    # create a meshgrid in the Fourier domain
    fx = np.fft.fftfreq(res, fov/res)
    [kx, ky] = np.meshgrid(fx, fx)
    kxky = np.sqrt(kx**2 + ky**2)

    # initialize the filter
    bpf = np.zeros((res, res))

    # compute the mask
    mask_out = kxky <= NA_out
    mask_in = kxky >= NA_in

    # combine the masks
    mask = np.logical_and(mask_out, mask_in)

    # mask the filter
    bpf[mask] = 1

    # return according to the dimention
    if dimention == 2:
        bpf_return = bpf
    elif dimention == 1:
        bpf_return = bpf[0, :int(res/2)+1]
    else:
        raise ValueError('The dimention of the simulation is invalid!')

    return bpf_return

def idhf(res, fov, y):
    """
    Inverse Discrete Hankel Transform of an 1D array

    Parameters
    ----------
        res: resolution of the simulation
        fov: field of view
        y: 1-D array to be transformed

    Returns
    -------
        F: 1-D array after transformation
        F_x: sample index
    """

    X = int(fov/2)
    n_s = int(res/2)

    # order of the bessel function
    order = 0
    # root of the bessel function
    jv_root = sp.special.jn_zeros(order, n_s)
    jv_M = jv_root[-1]
    jv_m = jv_root[:-1]
#    jv_mX = jv_m/X

#    F_term = np.interp(jv_mX, x, y)
    F_term = y[1:]
    # inverse DHT
    F = np.zeros(n_s, dtype=np.complex128)
    jv_k = jv_root[None,...]

    prefix = 2/(X**2)

    Jjj = jv_m[...,None]*jv_k/jv_M
    numerator = sp.special.jv(order, Jjj)
    denominator = sp.special.jv(order+1, jv_m[...,None])**2

    summation = np.sum(numerator / denominator * F_term[:-1][...,None], axis=0)

    F = prefix * summation

    F_x = jv_root*X/jv_M

    return F, F_x

def apply_filter(res, fov, E, filter):
    """
    Apply the filter to the field
    the field in the real domain is transformed into Fourier domain
    then multiplied by the filter in the Fourier domain so that
    the frequency components that are outside of the filter are filtered out
    Then the filtered field is transformed back into the real domain

    Parameters
    ----------
        E:      input field, 2-D array, compelx or real
        filter: filter to be applied, 2-D array, int (1/0)

    Returns
    -------
        E_filtered: filtered field in the real domain
    """

    if E.ndim == 2:
        # apply Fourier transform to the input field
        E_fft = np.fft.fft2(E)

        # apply the filter
        E_fft_filtered = E_fft * filter

        # convert the field back
        E_filtered = np.fft.ifft2(E_fft_filtered)

        return E_filtered

    elif E.ndim == 1:
        # apply the filter to the 1-D simulation
        E_dht_filtered = E * filter

        # apply inverse hankel transform
        E_filtered, E_x = idhf(res, fov, E_dht_filtered)

        return E_filtered, E_x

def crop_field(res, E):
    """
    Crop the field into the specified resolution and field of view

    Parameters
    ----------
        res: the resolution be crop the field to
        E: input field, 2-D array, complex or real

    Returns
    -------
        E_crop: cropped field, 2-D array, (res, res)
    """

    # get the size before and after cropping
    imsize = E.shape[0]
    cropsize = res

    # compute the starting and ending index of the axis
    startIdx = int(np.fix(imsize /2) - np.floor(cropsize/2))
    endIdx = int(startIdx + cropsize - 1)

    # crop the field
    E_crop = E[startIdx:endIdx+1, startIdx:endIdx+1]

    return E_crop

def get_phase_shift(res, fov, k, d):
    """
    calculate a 2-D phase shift mask with distance d
    
    Parameters
    ----------
        res: resolution of the simulation
        fov: field of view
        k: wavenumber
        d: propagation distance
        
    Returns
    -------
        phase: phase shift map, 2D complex array
    """
    # calculate the fourier frequencies
    fx = np.fft.fftfreq(res, fov/res)
    fy = np.fft.fftfreq(res, fov/res)
    
    # calculate kz
    kx, ky = np.meshgrid(fx, fy)
    kxky = kx ** 2 + ky ** 2
    mask = kxky > k**2
    kxky[mask] = 0
    kz = np.sqrt(k**2 - kxky)
    kz[mask] = 0
    
    # calculate phase term
    phase = np.exp(1j * kz * d)
    
    return phase