from sim_access.datasource import DataSource, SerialDataSource
import six
from abc import abstractmethod, ABCMeta
import threading
import time
import sys
import binascii


def ucs2encode(text):
    if text is None or text == '':
        return ''
    return text.encode('utf-16-be').hex().upper()

def ucs2decode(text):
    if text is None or text == '':
        return ''
    return binascii.unhexlify(text).decode('utf-16-be')

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
        return [atset('CMGS', True) + '"{0}"\r'.format(ucs2encode(number)),
                '{0}\x1a\n'.format(ucs2encode(text))]

    @classmethod
    def delallmsgs(cls):
        return atset('CMGD', True) + '1,4\r\n'
    
    @classmethod
    def callerinfo(cls):
        return atread('CLCC', True) + '\r\n'


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
            'AT',
            'AT+CMGF=1',
            'AT+CSMP=17,167,0,8',
            'AT+CLIP=1',
            'ATE0',
            'AT+CSCS="UCS2"',
        ]
        print('Initializing SIM module...')
        for i in cmds:
            #print(i)
            self.__datasource.write('{0}\r\n'.format(i).encode())
            self.__wait_ok()

    def __wait_ok(self):
        done = False
        counter = 0
        msgs = []
        while done == False and counter < 3:
            line = self.__datasource.readline()
            line = line.decode()
            #print(line)
            msgs.append(line)
            if line == 'OK\r\n':
                done = True
            elif line == 'ERROR\r\n':
                done = False
                raise Exception('Failed')
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
        if len(line) > 1 and line[0] == '+':
            self.__process_plus(line)
        elif len(line) > 4 and line[:4] == 'RING':
            #incoming call
            # need to use at+clcc to get phone number
            self.__process_incoming_call()
        elif len(line) > 11 and line[:11] == 'MISSED_CALL':
            #missed call
            pass

    def __massage_recv_data(self, msgs):
        rtn = []
        for i in msgs:
            if i != '\r\n':
                if len(i) > 2 and i[-2:] == '\r\n':
                    i = i[:-2]
                if len(i) >= 4 and i == 'OK\r\n':
                    continue
                rtn.append(i)
        return rtn

    def __process_plus(self, line):
        tokens = line.split(':')
        datatype = tokens[0]
        if datatype.upper() == '+CMTI':
            sms_idx = tokens[1].split(',')[-1]
            tmp = ATCommands.readmsg(sms_idx)
            self.__datasource.write(tmp.encode())
            msgs = self.__wait_ok()
            msgs = self.__massage_recv_data(msgs)

            tmp = msgs[0].split(',')
            number = tmp[1]
            if number[0] == '\"' and number[-1] == '\"':
                number = number[1:-1]
            content = msgs[1:-1]
            self.on_message(ucs2decode(number),
                            '\n'.join([ucs2decode(i) for i in content if i is not None and i != '']))

            tmp = ATCommands.delallmsgs()
            self.__datasource.write(tmp.encode())
            self.__wait_ok()

    def __process_incoming_call(self):
        tmp = ATCommands.callerinfo()
        self.__datasource.write(tmp.encode())
        tmp = self.__wait_ok()
        tmp = self.__massage_recv_data(tmp)
        number = None
        for i in tmp:
            if i.find('+CLIP:') == 0:
                number = i.split(',')[0][8:-1]
                break
        if number is not None:
            self.on_call(number)

    def __worker(self):
        while True:
            try:
                line = self.__datasource.readline()
                line = line.decode()
                self.__process_data(line)
            except Exception as e:
                print(str(e))
                sys.exit(0)


