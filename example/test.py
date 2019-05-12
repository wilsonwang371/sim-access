import logging
import time

from sim_access.adapter import SerialAdapter
from sim_access.sim import SIMModuleBase


logger = logging.getLogger(__name__)

APN = 'pwg'

class MySIM(SIMModuleBase):
    def on_sms(self, number, content):
        logger.info('Text from: {0}, Content: \"{1}\"'.format(number, content))
    
    def on_call(self, number):
        logger.info('Got phone call from {0}'.format(number))
        time.sleep(5)
        self.call_hangup()
        self.sms_send(number, '😫Sorry I missed your call!')
    
    def on_missed_call(self, number):
        self.sms_send(number, '😫Sorry I missed your call!')


if __name__ == '__main__':
    # You may need to run this at the parent
    # directory and use PYTHONPATH variable for now.
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    tmp = SerialAdapter(devfile='/dev/cu.usbserial-1410')
    a = MySIM(tmp)

    #based on https://m2msupport.net/m2msupport/atciicr-bring-up-gprs-or-circuit-switch-connection/
    a.network_attach()
    a.network_setapn(APN) # usmobile apn
    a.network_bringup()
    addr = a.network_ipaddr()
    print('My IP: {0}'.format(addr))

    ((mylong, mylat), mydate, mytime) = sim.gps_location_date_time(APN)
    print('Longitude: {0}\nLatitude: {1}\nDate: {2}\nTime: {3}\n'.format(mylong, mylat, mydate, mytime))
    
    a.mainloop()
