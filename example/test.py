from sim_access.sim import  SIMModuleBase
from sim_access.datasource import SerialDataSource


class MySIM(SIMModuleBase):
    def on_message(self, number, text):
        print('Text from: {0}, Content: \"{1}\"'.format(number, text))
    
    def on_call(self, number):
        pass


if __name__ == '__main__':
    # You may need to run this at the parent
    # directory and use PYTHONPATH variable for now.
    tmp = SerialDataSource()
    a = MySIM(tmp)
    time.sleep(200)
