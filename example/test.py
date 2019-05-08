from sim_access.sim import  SIMModuleBase
from sim_access.adapter import SerialAdapter
import time

class MySIM(SIMModuleBase):
    def on_sms(self, number, content):
        print('Text from: {0}, Content: \"{1}\"'.format(number, content))
    
    def on_call(self, number):
        print('Got phone call from {0}'.format(number))
        time.sleep(5)
        self.call_hangup()
        time.sleep(5)
        self.sms_send(number, 'You called me!')


if __name__ == '__main__':
    # You may need to run this at the parent
    # directory and use PYTHONPATH variable for now.
    tmp = SerialAdapter()
    a = MySIM(tmp)
    a.mainloop()
