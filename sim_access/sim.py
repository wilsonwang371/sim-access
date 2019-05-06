from sim_access.datasource import DataSource, SerialDataSource
import six
from abc import abstractmethod, ABCMeta
import threading
import time
import sys


def atcmd(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}'.format(cmd.upper())
    else:
        cmd = 'AT{0}'.format(cmd.upper())
    return cmd

def atread(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}?'.format(cmd.upper())
    else:
        cmd = 'AT{0}?'.format(cmd.upper())
    return cmd

def atset(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}='.format(cmd.upper())
    else:
        cmd = 'AT{0}='.format(cmd.upper())
    return cmd


class ATCommands(object):

    @classmethod
    def dial(cls, number):
        assert isinstance(number, str)
        return atcmd('D', False) + '{0};\r\n'.format(number)

    @classmethod
    def hungup(cls):
        return atcmd('CHUP', True) + '\r\n'

    @classmethod
    def regstatus(cls):
        return atread('COPS', True) + '\r\n'

    @classmethod
    def readmsg(cls, index):
        return atset('CMGR', True) + '{0}\r\n'.format(index)
    
    @classmethod
    def readnewmsgs(cls):
        return atset('CMGL', True) + '"REC UNREAD"\r\n'

    @classmethod
    def sendmsg(cls, number, text):
        return [atset('CMGS', True) + '"{0}"\r'.format(number),
                '{0}\x1a\n'.format(text)]


@six.add_metaclass(ABCMeta)
class SIMModuleBase(object):

    def __init__(self, datasource):
        assert isinstance(datasource, DataSource)
        self.__datasource = datasource
        self.__thread = threading.Thread(target=self.__worker)
        self.__thread.start()

    @abstractmethod
    def on_message(self, number, text):
        raise NotImplementedError()

    @abstractmethod
    def on_call(self, number):
        raise NotImplementedError()

    def send_message(self, number, text):
        cmd = ATCommands.sendmsg(number, text)
        for i in cmd:
            self.__datasource.write(i.encode())
            time.sleep(1)
    
    def __worker(self):
        while True:
            try:
                line = self.__datasource.readline()
                sys.stdout.write(line.decode())
                sys.stdout.flush()
            except Exception as e:
                print(str(e))


class MySIM(SIMModuleBase):
    def on_message(self, number, text):
        pass
    
    def on_call(self, number):
        pass


if __name__ == '__main__':
    '''print(ATCommands.dial('6073484940'))
    print(ATCommands.hungup())
    print(ATCommands.regstatus())
    print(ATCommands.readmsg(1))
    print(ATCommands.readnewmsgs())'''
    tmp = SerialDataSource()
    a = MySIM(tmp)
    a.send_message('6073484940', 'test')
    time.sleep(10)
