import json
import paho.mqtt.client as mqtt
from Device import Device

HOST = "localhost"
PORT = 1883


class LightDevice(Device):

    # setting up the intensity choices for Smart Light Bulb  
    _INTENSITY = ["LOW", "HIGH", "MEDIUM", "OFF"]

    def __init__(self, device_id, room,
                 device_register_topic='subscribe/add_devices',
                 device_add_status_topic='devices/add_device/{}/response'):

        # Assigning device level information for each of the devices. 
        # self._device_id = device_id
        # self._room_type = room
        self._light_intensity = self._INTENSITY[0]
        self._device_type = "LIGHT"
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
    #    pass

    # Getting the light intensity for the devices
    def _get_light_intensity(self):
        return self._light_intensity
        # pass

    # Setting the light intensity for devices
    def _set_light_intensity(self, light_intensity):
        self._light_intensity = light_intensity
        # pass

    # Checks the requested temperature and sets them if its within valid range
    def _set_controller_req(self, light_intensity):
        status_msg = ''
        if light_intensity.upper() in self._INTENSITY:
            if self._get_switch_status() == 'OFF':
                self._set_switch_status()
            self._set_light_intensity(light_intensity)
        else:
            status_msg = 'Intensity Change FAILED. Invalid Light Intensity level received'
        return status_msg

    # Process the get status request
    def _build_dev_status_res_msg(self, status_id):
        msg = super()._build_dev_status_res_msg(status_id)
        msg['intensity'] = self._get_light_intensity()
        return msg
