
import json
import paho.mqtt.client as mqtt
from Device import Device

HOST = "localhost"
PORT = 1883


class ACDevice(Device):
    
    _MIN_TEMP = 18  
    _MAX_TEMP = 32  

    def __init__(self, device_id, room,
                 device_register_topic='subscribe/add_devices',
                 device_add_status_topic='devices/add_device/{}/response'):

        # self._device_id = device_id
        # self._room_type = room
        self._temperature = 22
        self._device_type = "AC"
        # self._device_registration_flag = False
        # self.client = mqtt.Client(self._device_id)
        # self.client.on_connect = self._on_connect
        # self.client.on_message = self._on_message
        # self.client.on_disconnect = self._on_disconnect
        # self.client.connect(HOST, PORT, keepalive=60)
        # self.client.loop_start()
        # self._register_device(self._device_id, self._room_type, self._device_type)
        # self._switch_status = "OFF"
        # super().__init__(device_id, room, device_register_topic, device_add_status_topic, device_stat_req_topics)
        super().__init__(device_id, room, device_register_topic, device_add_status_topic)

    # calling registration method to register the device
    # def _register_device(self, device_id, room_type, device_type):
    #    pass

    # Connect method to subscribe to various topics. 
    # def _on_connect(self, client, userdata, flags, result_code):
    #    pass

    # method to process the recieved messages and publish them on relevant topics 
    # this method can also be used to take the action based on received commands
    # def _on_message(self, client, userdata, msg):
    #    pass

    # Getting the current switch status of devices 
    # def _get_switch_status(self):
    #    pass

    # Setting the switch of devices
    # def _set_switch_status(self, switch_state):
        # pass

    # Getting the temperature for the devices
    def _get_temperature(self):
        return self._temperature
        # pass

    # Setting up the temperature of the devices
    def _set_temperature(self, temperature):
        self._temperature = temperature
        # pass

    # Checks the requested temperature and sets them if its within valid range
    def _set_controller_req(self, temperature):
        status_msg = ''
        if self._MIN_TEMP <= int(temperature) <= self._MAX_TEMP:
            if self._get_switch_status() == 'OFF':
                self._set_switch_status()
            self._set_temperature(int(temperature))
        else:
            status_msg = 'Temperature Change FAILED. Invalid temperature value received'
        return status_msg

    # Process the get status request
    def _build_dev_status_res_msg(self, status_id):
        msg = super()._build_dev_status_res_msg(status_id)
        msg['temperature'] = self._get_temperature()
        return msg
