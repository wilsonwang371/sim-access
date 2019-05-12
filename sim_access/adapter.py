import logging
import sys
import time
from abc import ABCMeta, abstractmethod

import serial
import six


logger = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class AdapterBase(object):

    @abstractmethod
    def read(self, size=0):
        raise NotImplementedError()

    @abstractmethod
    def readline(self):
        raise NotImplementedError()

    @abstractmethod
    def write(self, data):
        raise NotImplementedError()

    @abstractmethod
    def available(self):
        raise NotImplementedError()



class SerialAdapter(AdapterBase):

    def __init__(self, devfile='/dev/tty.usbserial-00000000', baud=115200):
        self.__port = serial.Serial(devfile, baudrate=baud, timeout=3.0)

    def read(self, size=0):
        if size == 0:
            data = self.__port.read_all()
        else:
            data = self.__port.read(size)
        return data
    
    def readline(self):
        data = self.__port.readline()
        logger.debug('<' + data.decode())
        return data

    def write(self, data):
        assert isinstance(data, bytes)
        logger.debug('>' + data.decode())
        self.__port.write(data)

    def available(self):
        return self.__port.in_waiting
