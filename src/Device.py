import json
import datetime
import time
import paho.mqtt.client as mqtt

HOST = "localhost"
PORT = 1883


# Parent class for smart home devices
# It retains all the common functionalities
# AC & Light Devices will be derived from this class
class Device:

    def __init__(self, device_id, room,
                 device_register_topic,
                 device_add_status_topic):
        # Assigning device level information for each of the devices.
        self._device_id = device_id
        self._room_type = room
        self._device_registration_flag = False
        self._connect_success = False
        self._bad_connection = False
        self._messages_dict = dict()
        self._device_req_topic = list()
        self._device_req_res_topic = ''
        self._device_publish_topic = ''
        self._device_register_topic = device_register_topic
        self._device_add_ack_topic = self._set_device_reg_ack_topic(device_add_status_topic)
        # self._device_status_req_topics = self._set_device_status_req_topic(device_stat_req_topics)
        self.client = mqtt.Client(self._device_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(HOST, PORT, keepalive=60)
        self.client.loop_start()
        self._connection_status_check()
        self._switch_status = "OFF"

    # calling registration method to register the device
    def _register_device(self, device_id, room_type, device_type, device_request='add'):
        device_add_msg = {"device_id": device_id,
                          "device_type": device_type.lower(),
                          "room": room_type.lower(),
                          "request": device_request,
                          "timestamp": self.get_current_timestamp()}
        self._pub_to_topic(self._device_register_topic, device_add_msg)

    # Connect method to subscribe to various topics.
    def _on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            print('{} Device {} has been connected with result_code {}'.format(self._device_type,
                                                                               self._device_id,
                                                                               result_code))
            self._connect_success = True
            print('{} Device {} will send registration request to {} topic'.format(self._device_type,
                                                                                   self._device_id,
                                                                                   self._device_add_ack_topic))
            self._sub_to_topic(self._device_add_ack_topic)
            self._register_device(self._device_id, self._room_type, self._device_type)
        else:
            print('Edge server {} connection failed with result_code {}'.format(self._device_id, result_code))
            self._bad_connection = True

    # method to process the received messages and publish them on relevant topics
    # this method can also be used to take the action based on received commands
    def _on_message(self, client, userdata, msg):
        temp_msg = json.loads(msg.payload.decode())
        msg_list = self._messages_dict.get(msg.topic, [])
        print('Message received -  ', temp_msg)
        if ((isinstance(temp_msg['device_id'], str) and temp_msg['device_id'] == self._device_id) or
                (isinstance(temp_msg['device_id'], list) and self._device_id in temp_msg['device_id'])):
            if msg.topic == self._device_add_ack_topic.format(self._device_type):
                msg_list.append(temp_msg)
                self._messages_dict[msg.topic] = msg_list
                self._dev_sub_req_ack_process(msg.topic)
            elif msg.topic in self._device_req_topic:
                msg_list.append(temp_msg)
                temp_topic = msg.topic
                if temp_msg['request'] == 'get_status':
                    temp_topic += 'get_status'
                    self._messages_dict[temp_topic] = msg_list
                    self._process_get_switch_status(temp_topic)
                elif temp_msg['request'] == 'set_status':
                    temp_topic += 'set_status'
                    self._messages_dict[temp_topic] = msg_list
                    self._process_set_switch_status(temp_topic)

    # Process the get switch status of devices
    def _process_get_switch_status(self, topic):
        switch_status_msgs = self._messages_dict[topic]
        for status_msg in switch_status_msgs:
            print('Received message from {} topic and payload is {}:'.format(topic,
                                                                             status_msg))
            msg = self._build_dev_status_res_msg(status_msg['status_id'])
            # print('Built response payload is {}'.format(msg))
            self._pub_to_topic(self._device_req_res_topic, msg)
        self._messages_dict[topic] = []

    # Getting the current switch status of devices
    def _get_switch_status(self):
        return self._switch_status

    # Processing the set request for devices
    def _process_set_switch_status(self, topic):
        switch_status_msgs = self._messages_dict[topic]
        for toggle_request in switch_status_msgs:
            print('Received message from {} topic and payload is {}:'.format(topic,
                                                                             toggle_request))
            status_msg = ''
            if not toggle_request['controller']:
                self._set_switch_status()
            else:
                status_msg = self._set_controller_req(toggle_request['controller'])

            if status_msg:
                msg = {'status_id': toggle_request['status_id'],
                       'error_msg': status_msg + ' for status_id - {}.'.format(toggle_request['status_id'])}
            else:
                msg = self._build_dev_status_res_msg(toggle_request['status_id'])
            self._pub_to_topic(self._device_req_res_topic, msg)
        self._messages_dict[topic] = []
        # pass

    # Setting the switch of devices
    def _set_switch_status(self):
        if self._get_switch_status() == 'OFF':
            self._switch_status = 'ON'
        else:
            self._switch_status = 'OFF'

    # Subscribe to the topic
    def _sub_to_topic(self, topic):
        self.client.subscribe(topic)

    # Publish to the topic
    def _pub_to_topic(self, topic, msg):
        self.client.publish(topic, json.dumps(msg))

    # Terminating the MQTT broker and stopping the execution
    def terminate(self):
        self.client.disconnect()
        self.client.loop_stop()

    # Process the device registration response message
    def _dev_sub_req_ack_process(self, topic):
        msg_payloads = self._messages_dict[topic]
        for msg_payload in msg_payloads:
            # if self._device_id == msg_payload['device_id'] and msg_payload['request'] == 'add':
            if msg_payload['request'] == 'add':
                if msg_payload['request_status'] == 'success':
                    self._device_registration_flag = True
                    self._device_publish_topic = msg_payload['device_topic']
                    self._device_req_res_topic = msg_payload['device_req_res_topic']
                    self._device_req_topic = msg_payload['request_topics']
                    print('{}-DEVICE Registered! - Registration status is available for {} : {}'.
                          format(self._device_type,
                                 self._device_id,
                                 self._device_registration_flag))

                    for device_req_topic in self._device_req_topic:
                        print('{}-DEVICE with {} id will subscribe to {} request topic'.
                              format(self._device_type, self._device_id, device_req_topic))
                        self._sub_to_topic(device_req_topic)

                    print('{}-DEVICE with {} id will respond to the request thru {} topic'.
                          format(self._device_type,
                                 self._device_id,
                                 self._device_req_res_topic))
                else:
                    print('{}-DEVICE Registration Failed - Registration status for {} is {}'.
                          format(self._device_type,
                                 self._device_id,
                                 self._device_registration_flag))
        self._messages_dict[topic] = []

    # Process the get status request
    def _build_dev_status_res_msg(self, status_id):
        msg = {"status_id": status_id,
               "device_id": self._device_id,
               "switch_state": self._get_switch_status()}
        return msg

    # Setting up device acknowledgment topic to subscribe
    # devices/add_device/{}/response - devices/add_device/AC/response
    def _set_device_reg_ack_topic(self, topic):
        if '{}' in topic:
            return topic.format(self._device_type.lower())
        else:
            return topic

    # Setting up topic for device's get status acknowledgment to subscribe
    # {'device_type': 'devices/status/{}', 'room': 'devices/status/{}'}
    #           - {'device_type': 'devices/status/LIGHT', 'room': 'devices/status/BR1'}
    def _set_device_status_req_topic(self, topics):
        for topic_type, topic in topics.items():
            if '{}' in topic and topic_type == 'device_type':
                topics[topic_type] = topic.format(self._device_type.lower())
            if '{}' in topic and topic_type == 'room':
                topics[topic_type] = topic.format(self._room_type.lower())
        return topics

    # Wait for the connection establishment and if it isn't successful call the terminate function to disconnect
    def _connection_status_check(self):
        while not self._connect_success and not self._bad_connection:
            time.sleep(1)

        if not self._connect_success:
            print('{} Device {} connection failed, hence terminating the connection'.format(self._device_type,
                                                                                            self._device_id))
            self.terminate()

    # Returns current timestamp
    @staticmethod
    def get_current_timestamp():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
