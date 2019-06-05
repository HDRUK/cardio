# -*- coding: utf-8 -*-

import numpy as np
from scipy.interpolate import interp1d


def find_first_index_for_maximum_in_zero_crossing(sdppg, zero_crossing):
  """
  Find the first index in the zero_crossing array that corresponds to the
  leftmost end of a zero crossing interval for a local maximum.

  Parameters
  ----
  sdppg: 1D array-like of float; the sdppg signal
  zero_crossing: 1D array-like of float; the zero crossing found for sdppg through its second derivative

  Returns
  ----
  start: int; leftmost end of the interval containing a local maximum
  """
  if len(zero_crossing) == 0:
    return 0
  start = 0
  # compute max and min values
  max_value = np.max(sdppg[zero_crossing[start]:zero_crossing[start+1]])
  min_value = np.min(sdppg[zero_crossing[start]:zero_crossing[start+1]])
  # get the relative amplitude of the peak/trough
  max_value = np.max([max_value - sdppg[zero_crossing[start]],
                      max_value - sdppg[zero_crossing[start+1]]])
  min_value = np.max([sdppg[zero_crossing[start]] - min_value,
                      sdppg[zero_crossing[start+1]] - min_value])
  if min_value > max_value:
    start += 1
  return start


def find_next_a(sdppg, zero_crossing, start):
  """
  Find the next a peak in the SDPPG signal.

  Parameters
  ----
  sdppg: 1D array-like of float; the (normalised) sdppg signal
  zero_crossing: 1D array-like of float; the zero crossing found from the fourth derivative of the PPG
  start: int, starting position from which the zero_crossing array will be read

  Returns
  ----
  a: float; the feature
  k: int; the first position in the zero-crossing array after a

  Notes: if there is no next a, a is set to np.nan and k to len(zero_crossing)
  For further information:
      https://ieeexplore.ieee.org/document/5412099
  """
  k = start

  def compute_max(x, z, n):  # TODO maybe out?
    return np.max(x[z[n]:z[n+1]])
  z_len = len(zero_crossing)
  if k + 3 >= z_len:
    return np.nan, z_len
  max1 = compute_max(sdppg, zero_crossing, k)
  max2 = compute_max(sdppg, zero_crossing, k+2)  # k+1 refers to the next min
  while max2 > max1:
    k += 2
    max1 = max2
    if k + 3 >= z_len:
      return np.nan, z_len
    max2 = compute_max(sdppg, zero_crossing, k+2)
  # now max1 is a
  k += 1
  return max1, k


def sdppg_agi(a, b, c, d, e):
  """
  Compute the ageing index (AGI) from the features (a, b, c, d, e) extracted
  from the SDPPG approach. The formula is (b-c-d-e)/a. The feature can be obtained through
  features_from_sdppg.

  Parameters
  ----
  a: float; array-like of float; feature 'a' extracted from the sdppg approach.
  b: float; array-like of float; feature 'b' extracted from the sdppg approach.
  c: float; array-like of float; feature 'c' extracted from the sdppg approach.
  d: float; array-like of float; feature 'd' extracted from the sdppg approach.
  e: float; array-like of float; feature 'e' extracted from the sdppg approach.
  Returns
  ----
  AGI: numpy array of floats; the ageing index computed for each element.

  For further reading:
      https://www.hindawi.com/journals/tswj/2013/169035/abs/
      https://ieeexplore.ieee.org/document/5412099
  """
  a_ = np.asarray(a, dtype=float)
  b_ = np.asarray(b, dtype=float)
  c_ = np.asarray(c, dtype=float)
  d_ = np.asarray(d, dtype=float)
  e_ = np.asarray(e, dtype=float)
  AGI = (b_-c_-d_-e_)/a_
  return AGI


def features_from_sdppg(t, signal, normalise=True, flip=True,
                        spline=True, f=100):
  """
  Find the a, b, c, d, e parameters (features, "waves") for a PPG signal
  through its normalised second derivative.

  Parameters
  ----
  t: 1D array-like of float; the time points at which the signal has been measured
  signal: 1D array-like of float; the measured PPG signal
  normalise: bool(default=True); if True, normalise SDPPG and its second derivative
  flip: bool (default=True); should the signal be flipped?
  spline: bool (default=True); use the cubic spline interpolation of signal instead of signal. BEWARE of splines: they can change the maxima and minima value and position!
  f: int (default=100); factor used to compute the new number of points if spline==True : the length of the splined signal will be len(t)*f

  NOTES: t and signal must have the same length; t must be monotonic and positive

  Returns
  ----
  sdppg: the sdppg computed from the PPG signal provided. It is the result of the spline if spline=True
  features: dictionary containing 10 numpy array: a, b, c, d, e (each of them is a np array of the respective "wave" fount in the SDPPG), the AGI index (AGI) computed for each element of the array, and the time differences between the "waves" a and b, b and c, c and d, and d and e (t_ab, t_bc, t_cd, t_de).

  NOTES:
    a is the initial positive wave
    b is early negative wave (we suppose b < 0)
    c is the re-upsloping wave
    d is the re-downloping wave
    e is the diastolic positive wave

  For further information, please read:
      https://www.hindawi.com/journals/tswj/2013/169035/abs/
      https://ieeexplore.ieee.org/document/5412099
  """
  sdppg = np.gradient(np.gradient(signal, t), t)
  fdppg = np.gradient(np.gradient(sdppg, t), t)
  # spline
  if spline:
    spline_sdppg = interp1d(t, sdppg, kind='cubic')
    spline_fdppg = interp1d(t, fdppg, kind='cubic')
    newt = np.linspace(t[0], t[-1], len(t)*f)
    spline_sdppg = spline_sdppg(newt)
    spline_fdppg = spline_fdppg(newt)
    sdppg = spline_sdppg
    fdppg = spline_fdppg
  else:
    newt = np.asarray(t)
  # normalisation
  if normalise:
    sdppg /= np.max(np.abs(sdppg))
    fdppg /= np.max(np.abs(fdppg))
  # flip
  if flip:
    sdppg = np.flip(sdppg)
    fdppg = np.flip(fdppg)
    newt = np.flip(newt)

  # find the zero crossings
  intermediate_step = fdppg[0:-1]*fdppg[1:]
  zero_crossing = np.where(intermediate_step < 0.)[0]
  # find starting position
  i = find_first_index_for_maximum_in_zero_crossing(sdppg, zero_crossing)
  a, b, c, d, e = [], [], [], [], []
  t_a, t_b, t_c, t_d, t_e = [], [], [], [], []
  z_len = len(zero_crossing)
  while i < z_len:
    next_a, i = find_next_a(sdppg, zero_crossing, i)
    if i >= z_len:  # to be certain i is not out of bounds. See find_next_a
      break
    next_t_a = np.argmax(sdppg[zero_crossing[i-1]:zero_crossing[i]]) + zero_crossing[i-1]
    next_b = 1.
    while next_b > 0:
      if i + 1 >= z_len:  # to be certain we have enough elements in the array
        break
      next_b = np.min(sdppg[zero_crossing[i]:zero_crossing[i+1]])
      next_t_b = np.argmin(sdppg[zero_crossing[i]:zero_crossing[i+1]]) + zero_crossing[i]
      if next_b > 0:
        i += 2

    if i + 4 >= z_len: # to be certain we have enough elements to find the other waves
      break
    # next_b = np.min(sdppg[zero_crossing[i]:zero_crossing[i+1]])
    next_c = np.max(sdppg[zero_crossing[i+1]:zero_crossing[i+2]])
    next_t_c = np.argmax(sdppg[zero_crossing[i+1]:zero_crossing[i+2]]) + zero_crossing[i+1]
    next_d = np.min(sdppg[zero_crossing[i+2]:zero_crossing[i+3]])
    next_t_d = np.argmin(sdppg[zero_crossing[i+2]:zero_crossing[i+3]]) + zero_crossing[i+2]
    next_e = np.max(sdppg[zero_crossing[i+3]:zero_crossing[i+4]])
    next_t_e = np.argmax(sdppg[zero_crossing[i+3]:zero_crossing[i+4]]) + zero_crossing[i+3]
    # No need to check c: it's the next maximum after a; always < a
    if next_e >= next_a:
      i += 3  # Find the next 'a' after the bad region due to false e
    else:
      a.append(next_a)
      b.append(next_b)
      c.append(next_c)
      d.append(next_d)
      e.append(next_e)
      t_a.append(next_t_a)
      t_b.append(next_t_b)
      t_c.append(next_t_c)
      t_d.append(next_t_d)
      t_e.append(next_t_e)
      i += 5  # sdppg[zero_crossing[i+4]: zero_crossing[i+5]] should be a minimum

  # convert to numpy array
  a = np.asarray(a)
  b = np.asarray(b)
  c = np.asarray(c)
  d = np.asarray(d)
  e = np.asarray(e)
  t_a = newt[t_a]
  t_b = newt[t_b]
  t_c = newt[t_c]
  t_d = newt[t_d]
  t_e = newt[t_e]
  t_ab = np.abs(t_a-t_b)
  t_bc = np.abs(t_b-t_c)
  t_cd = np.abs(t_c-t_d)
  t_de = np.abs(t_d-t_e)
  agi = sdppg_agi(a, b, c, d, e)
  features = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'AGI': agi,
              't_ab': t_ab, 't_bc': t_bc, 't_cd': t_cd, 't_de': t_de}
  return sdppg, features  # return sdppg and a dictionary
