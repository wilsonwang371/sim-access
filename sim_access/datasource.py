from abc import ABCMeta, abstractmethod
import six
import serial
import time
import sys


@six.add_metaclass(ABCMeta)
class DataSource(object):

    @abstractmethod
    def read(self, size=1):
        raise NotImplementedError()

    @abstractmethod
    def write(self, data):
        raise NotImplementedError()

    @abstractmethod
    def available(self):
        raise NotImplementedError()



class SerialDataSource(DataSource):

    def __init__(self, devfile='/dev/tty.usbserial-00000000', baud=115200):
        self.__port = serial.Serial(devfile, baudrate=baud, timeout=3.0)

    def read(self, size=1):
        data = self.__port.read(size)
        return data

    def write(self, data):
        assert isinstance(data, bytes)
        self.__port.write(data)

    def available(self):
        return self.__port.in_waiting


if __name__ == '__main__':
    tmp = SerialDataSource()
    tmp.write('AT\r\n'.encode())
    time.sleep(3)
    while tmp.available():
        sys.stdout.write(tmp.read().decode())