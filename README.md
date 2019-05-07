# sim-access

A Python module for managing SIM modules

My current setup is:

- A serial sim module SIM7500A.
- A USB to serial module connecting my computer with SIM7500A. 

<img src="https://cdn10.bigcommerce.com/s-rs1s2e/products/1375/images/2743/SIM7500A-5__33469.1542867154.1280.1280.png?c=2" width=200> <img src="https://images-na.ssl-images-amazon.com/images/I/71Uo%2BlNcjTL._SX425_.jpg" width=200>


To receive SMS and calls, you need to write a class from base class SIMModuleBase. There are two method you need to implement. **on_message()** and **on_call()**. Here is one example.

```
class MySIM(SIMModuleBase):
    def on_message(self, number, text):
        print('Text from: {0}, Content: \"{1}\"'.format(number, text))
    
    def on_call(self, number):
        print('Got phone call from {0}'.format(number))
        time.sleep(5)
        self.call_hungup()
        time.sleep(5)
        self.sms_send(number, 'You called me!')
```

Whenever you received an SMS, **on_message()** willl be called. If you receive a phone call, **on_call()** will be called. Please note that **on_call()** could be called multiple times during a phone call.

There is no implemenation of answering the phone call right now. The SIM module I bought does not support answering phone calls.

