#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 16:40:29 2019

@author: robert
"""

""" Based on the arrayqueue package. """
  
from multiprocessing import Queue, Array
import numpy as np
from queue import Empty, Full


class ArrayView:
    def __init__(self, array, max_bytes, dtype, el_shape, i_item=0):
        self.dtype = dtype
        self.el_shape = el_shape
        self.nbytes_el = self.dtype.itemsize * np.product(self.el_shape)
        self.n_items = int(np.floor(max_bytes / self.nbytes_el))
        self.total_shape = (self.n_items,) + self.el_shape
        self.i_item = i_item
        self.view = np.frombuffer(array, dtype, np.product(self.total_shape)).reshape(self.total_shape)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(self, other.__class__):
            return self.el_shape == other.el_shape and self.dtype == other.dtype
        return False

    def push(self, element):
        self.view[self.i_item, ...] = element
        i_inserted = self.i_item
        self.i_item = (self.i_item + 1) % self.n_items
        return self.dtype, self.el_shape, i_inserted # a tuple is returned to maximise performance

    def pop(self, i_item):
        return self.view[i_item, ...]

    def fits(self, item):
        if isinstance(item, np.ndarray):
            return item.dtype == self.dtype and item.shape == self.el_shape
        return (item[0] == self.dtype and
                item[1] == self.el_shape and
                item[2] < self.n_items)


class ArrayQueue:
    """ A drop-in replacement for the multiprocessing queue, usable
     only for numpy arrays, which removes the need for pickling and
     should provide higher speeds and lower memory usage
    """
    def __init__(self, max_mbytes=10):
        self.maxbytes = int(max_mbytes*1000000)
        self.array = Array('c', self.maxbytes)
        self.view = None
        self.queue = Queue()
        self.read_queue = Queue()
        self.last_item = 0

    def check_full(self):
        while True:
            try:
                self.last_item = self.read_queue.get(timeout=0.00001)
            except Empty:
                break
        if self.view.i_item == self.last_item:
            raise Full("Queue of length {} full when trying to insert {},"
                       " last item read was {}".format(self.view.n_items,
                                                       self.view.i_item, self.last_item))

    def put(self, element):
        if self.view is None or not self.view.fits(element):
            self.view = ArrayView(self.array.get_obj(), self.maxbytes,
                                  element.dtype, element.shape)
            self.last_item = 0
        else:
            self.check_full()
        qitem = self.view.push(element)

        self.queue.put(qitem)

    def get(self, **kwargs):
        aritem = self.queue.get(**kwargs)
        if self.view is None or not self.view.fits(aritem):
            self.view = ArrayView(self.array.get_obj(), self.maxbytes,
                                  *aritem)
        self.read_queue.put(aritem[2])
        return self.view.pop(aritem[2])

    def clear(self):
        """ Empties the queue without the need to read all the existing
        elements
        :return: nothing
        """
        self.view = None
        while True:
            try:
                it = self.queue.get_nowait()
            except Empty:
                break
        while True:
            try:
                it = self.read_queue.get_nowait()
            except Empty:
                break

        self.last_item = 0

    def empty(self):
        return self.queue.empty()
    
    def qsize(self):
        return self.queue.qsize()


class RspQueue(ArrayQueue):
    """ An extension of the queue class that supports sending response objects. """
    def put(self, rsp):
        element = rsp.data
        if self.view is None or not self.view.fits(element):
            self.view = ArrayView(self.array.get_obj(), self.maxbytes,
                                  element.dtype, element.shape)
        else:
            self.check_full()
        qitem = self.view.push(element)
        rsp.data = qitem
        
        self.queue.put(rsp)
        
    def get(self, **kwargs):
        rsp = self.queue.get(**kwargs)
        aritem = rsp.data
        if self.view is None or not self.view.fits(aritem):
            self.view = ArrayView(self.array.get_obj(), self.maxbytes,
                                  *aritem)
        self.read_queue.put(aritem[2])
        rsp.data = self.view.pop(aritem[2])
        return rsp
