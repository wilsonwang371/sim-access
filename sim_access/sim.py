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
    def setecho(cls, enable):
        if enable == False:
            return atcmd('E', False) + '0\r\n'
        else:
            return atcmd('E', False) + '1\r\n'


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
        self.__initialize()
        self.__thread = threading.Thread(target=self.__worker)
        self.__thread.start()

    def __initialize(self):
        cmds = [
            'AT+CLIP=1',
            'ATE0',
        ]
        print('Initializing SIM module...')
        for i in cmds:
            print(i)
            self.__datasource.write('{0}\r\n'.format(i).encode())
            self.__wait_ok()

    def __wait_ok(self):
        done = False
        counter = 0
        msgs = []
        while done == False and counter < 3:
            line = self.__datasource.readline()
            line = line.decode()
            msgs.append(line)
            if line == 'OK\r\n':
                done = True
            if line is None or line == '':
                counter += 1
        if not done:
            raise Exception('No OK reply')
        return msgs

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

    def __process_data(self, line):
        #print(line)
        if len(line) > 1 and line[0] == '+':
            self.__process_plus(line)
        elif len(line) > 4 and line[:3] == 'RING':
            #incoming call
            # need to use at+clcc to get phone number
            pass
        elif len(line) > 11 and line[:10] == 'MISSED_CALL':
            #missed call
            pass

    def __process_plus(self, line):
        tokens = line.split(':')
        datatype = tokens[0]
        if datatype.upper() == '+CMTI':
            sms_idx = tokens[1].split(',')[-1]
            tmp = ATCommands.readmsg(sms_idx)
            self.__datasource.write(tmp.encode())
            msgs = self.__wait_ok()
            print(msgs)

    def __worker(self):
        while True:
            try:
                line = self.__datasource.readline()
                line = line.decode()
                self.__process_data(line)
            except Exception as e:
                print(str(e))


class MySIM(SIMModuleBase):
    def on_message(self, number, text):
        pass
    
    def on_call(self, number):
        pass


if __name__ == '__main__':
    tmp = SerialDataSource()
    a = MySIM(tmp)
    time.sleep(200)
