import binascii
import logging
import os
import sys
import threading
import time
from abc import ABCMeta, abstractmethod

import six

from sim_access.adapter import AdapterBase, SerialAdapter

logger = logging.getLogger(__name__)


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
    def module_setecho(cls, enable):
        if enable == False:
            return atcmd('E', False) + '0\r\n'
        else:
            return atcmd('E', False) + '1\r\n'

    @classmethod
    def call_dial(cls, number):
        assert isinstance(number, str)
        return atcmd('D', False) + '{0};\r\n'.format(number)

    @classmethod
    def call_answer(cls):
        return atcmd('A', False) + '\r\n'

    @classmethod
    def call_hangup(cls):
        return atcmd('CHUP', True) + '\r\n'

    @classmethod
    def call_callerinfo(cls):
        return atread('CLCC', True) + '\r\n'

    @classmethod
    def module_checkready(cls):
        return atread('CPIN', True) + '\r\n'

    @classmethod
    def module_poweroff(cls):
        return atset('CPOF', True) + '1\r\n'

    @classmethod
    def module_regstatus(cls):
        return atread('COPS', True) + '\r\n'

    @classmethod
    def module_sapbr(cls, cmd):
        return atset('SAPBR', True) + '{0}\r\n'.format(cmd)

    @classmethod
    def gps_query(cls):
        return atset('CIPGSMLOC', True) + '1,1\r\n'

    @classmethod
    def network_setapn(cls, apn):
        return atset('CSTT', True) + '\"{0}\"\r\n'.format(apn)

    @classmethod
    def network_attach(cls):
        return atset('CGATT', True) + '1\r\n'

    @classmethod
    def network_bringup(cls):
        return atcmd('CIICR', True) + '\r\n'
    
    @classmethod
    def network_ipaddr(cls):
        return atcmd('CIFSR', True) + '\r\n'

    @classmethod
    def sms_fetch(cls, index):
        return atset('CMGR', True) + '{0}\r\n'.format(index)
    
    @classmethod
    def sms_unread(cls):
        return atset('CMGL', True) + '"REC UNREAD"\r\n'

    @classmethod
    def sms_send(cls, number, text):
        return [atset('CMGS', True) + '"{0}"\r'.format(ucs2encode(number)),
                '{0}\x1a\n'.format(ucs2encode(text))]

    @classmethod
    def sms_del(cls, idx):
        return atset('CMGD', True) + '{0},0\r\n'.format(idx)

    @classmethod
    def sms_delall(cls):
        return atset('CMGD', True) + '1,3\r\n'


'''TODO: we need to follow https://wiki.keyestudio.com/Ks0287_keyestudio_SIM5320E_3G_Module_(Black)
    to finish all the actions
'''
@six.add_metaclass(ABCMeta)
class SIMModuleBase(object):

    def __init__(self, adapter):
        assert isinstance(adapter, AdapterBase)
        self.__adapter = adapter
        self.__initialize()
        self.__parse_table = {
            '+CMTI': self.__sms_process,
            'RING': self.__call_process,
            'MISSED_CALL': self.__call_process_missed,
        }

    def __initialize(self):
        cmds = [
            'AT', #test if basic function is working
            'AT+CMGF=1', #we want to run in text mode
            'AT+CGATT=1', #enable GPS
            'AT+CSMP=17,167,0,8',
            'AT+CLIP=1', #we want caller info when receiving call
            'ATE0', #no echo is needed
            'AT+CSCS="UCS2"', #we want to be able to send unicode
        ]
        count = 0
        while count < 10 and not self.module_checkready():
            logger.debug('waiting SIM module to be ready...')
            count += 1
            time.sleep(1)
        logger.info('SIM module is ready.')
        if count >= 10:
            raise Exception('module not ready')
        for i in cmds:
            self.__adapter.write('{0}\r\n'.format(i).encode())
            self.__wait_ok()
        self.__network_up = False

    def __wait_ok(self):
        done = False
        counter = 0
        msgs = []
        while done == False and counter < 3:
            line = self.__adapter.readline()
            line = line.decode()
            logger.debug(line)
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
    def on_sms(self, number, content):
        ''' This is called when we received an sms message
        '''
        raise NotImplementedError()

    @abstractmethod
    def on_call(self, number):
        ''' This is called when we received a phone call
        '''
        raise NotImplementedError()

    @abstractmethod
    def on_missed_call(self, number):
        ''' This is called when we missed a call.
            This can happen when we hangup an incoming call.
            NOTE: this is not working on SIM800
        '''
        raise NotImplementedError()

    def sms_send(self, number, text):
        ''' send text to a destination number
        '''
        cmd = ATCommands.sms_send(number, text)
        for i in cmd:
            self.__adapter.write(i.encode())
            time.sleep(1)

    def call_answer(self):
        ''' answer current phone call
        '''
        tmp = ATCommands.call_answer()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()

    def call_hangup(self):
        ''' hangup current phone call
        '''
        tmp = ATCommands.call_hangup()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()

    def module_checkready(self):
        ''' check if module is ready
        '''
        tmp = ATCommands.module_checkready()
        self.__adapter.write(tmp.encode())
        tmp = self.__wait_ok()
        for i in tmp:
            if i.find('+CPIN: READY') == 0:
                return True
        return False

    def module_poweroff(self):
        ''' reset sim module
        '''
        tmp = ATCommands.module_poweroff()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()

    def gps_location_date_time(self, apn):
        ''' get gps location date and time
        '''
        tmp = ATCommands.module_sapbr('3,1,"CONTYPE","GPRS"')
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        tmp = ATCommands.module_sapbr('3,1,"APN","{0}"'.format(apn))
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        tmp = ATCommands.module_sapbr('1,1')
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        tmp = ATCommands.module_sapbr('2,1')
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        tmp = ATCommands.gps_query()
        self.__adapter.write(tmp.encode())
        result = self.__wait_ok()
        tmp = ATCommands.module_sapbr('0,1')
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        assert len(result) > 2
        tmp = result[1]
        assert tmp.find('+CIPGSMLOC') == 0
        vsuccess, vlongitude, vlatitude, vdate, vtime = tmp.split(' ')[1].split(',')
        assert vsuccess == '0'
        return ((vlongitude, vlatitude), vdate, vtime)

    def network_setapn(self, apn):
        ''' set up APN for network access
        '''
        tmp = ATCommands.network_setapn(apn)
        self.__adapter.write(tmp.encode())
        self.__wait_ok()

    def network_attach(self):
        ''' attach up network
        '''
        tmp = ATCommands.network_attach()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        time.sleep(2)

    def network_bringup(self):
        ''' bring up network
        '''
        tmp = ATCommands.network_bringup()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        self.__network_up = True

    def network_ipaddr(self):
        ''' get local ip address
        '''
        tmp = ATCommands.network_ipaddr()
        self.__adapter.write(tmp.encode())
        tmp = '\r\n'
        while tmp == '\r\n':
            tmp = self.__adapter.readline()
            tmp = tmp.decode()
        return tmp

    def mainloop(self, detached=False):
        ''' Currently we are doing nothing here except
            joining the thread
        '''
        self.__monitorthread = threading.Thread(target=self.__monitor_loop)
        self.__monitorthread.start()
        if not detached:
            try:
                self.__monitorthread.join()
            except KeyboardInterrupt:
                logger.info('Exiting...')
                os._exit(0)

    def loop_once(self):
        ''' This is doing the same as mainloop, but just once
        '''
        self.__loop_task()

    def __process_data(self, line):
        for k, v in six.iteritems(self.__parse_table):
            if line.find(k) == 0:
                try:
                    v(line)
                except Exception as e:
                    logger.error(str(e))
                break

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

    def __sms_process(self, line):
        tokens = line.split(':')
        datatype = tokens[0]
        if datatype.upper() == '+CMTI':
            sms_idx = tokens[1].split(',')[-1]
            tmp = ATCommands.sms_fetch(sms_idx)
            self.__adapter.write(tmp.encode())
            msgs = self.__wait_ok()
            msgs = self.__massage_recv_data(msgs)

            tmp = msgs[0].split(',')
            number = tmp[1]
            if number[0] == '\"' and number[-1] == '\"':
                number = number[1:-1]
            content = msgs[1:-1]
            self.on_sms(ucs2decode(number),
                            '\n'.join([ucs2decode(i) for i in content
                                       if i is not None and i != '']))

            tmp = ATCommands.sms_del(sms_idx)
            self.__adapter.write(tmp.encode())
            self.__wait_ok()

    def __call_process(self, line):
        tmp = ATCommands.call_callerinfo()
        self.__adapter.write(tmp.encode())
        tmp = self.__wait_ok()
        tmp = self.__massage_recv_data(tmp)
        number = None
        for i in tmp:
            if i.find('+CLIP:') == 0:
                number = i.split(',')[0][8:-1]
                break
        if number is not None:
            self.on_call(number)

    def __call_process_missed(self, line):
        ''' process missed call, something like:
            MISSED_CALL: 00:20AM 02132523094
        '''
        number = line.split(':').split()[-1]
        self.on_missed_call(number)

    def __loop_task(self):
        try:
            line = self.__adapter.readline()
            line = line.decode()
            self.__process_data(line)
        except Exception as e:
            logger.error(str(e))
            sys.exit(0)

    def __monitor_loop(self):
        while True:
            self.__loop_task()
