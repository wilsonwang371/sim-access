# sim-access
A Python module for managing SIM modules


## Setup
The setup is:
- A serial sim module SIM7500A.
- A USB to serial module connecting my computer with SIM7500A. 

The reason I am using a USB to Serial module is because I always want to make things easier to integrate with different setups. I hate connecting different GPIO wires with the SIM module and this is not sexy at all. With a USB to Serial module. It can be easier to plug and unplug to your systems.

<img src="https://cdn10.bigcommerce.com/s-rs1s2e/products/1375/images/2743/SIM7500A-5__33469.1542867154.1280.1280.png?c=2" width=200> <img src="https://images-na.ssl-images-amazon.com/images/I/71Uo%2BlNcjTL._SX425_.jpg" width=200>


To receive SMS and calls, you need to write a class from base class SIMModuleBase. There are two method you need to implement. **on_sms()** and **on_call()**. Here is one example.

```python
class MySIM(SIMModuleBase):
    def on_sms(self, number, content):
        print('Text from: {0}, Content: \"{1}\"'.format(number, content))

    def on_call(self, number):
        print('Got phone call from {0}'.format(number))
        time.sleep(5)
        self.call_hangup()

    def on_call_missed(self, number):
        self.sms_send(number, 'Sorry, I missed your call!')

if __name__ == '__main__':
    MySIM().mainloop()

```

Whenever you received an SMS, **on_sms()** willl be called. If you receive a phone call, **on_call()** will be called. Please note that **on_call()** could be called multiple times during a phone call.

There is no implemenation of answering the phone call right now. The SIM module I bought does not support answering phone calls.

## Implementation

Internally, I use a thread to monitor incoming texts and calls.
