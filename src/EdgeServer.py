
import json
import datetime
import time
import paho.mqtt.client as mqtt

HOST = "localhost"
PORT = 1883
WAIT_TIME = 0.25


class Edge_Server:

    _status_id_prefix = 'Status_'
    _command_id_prefix = 'Command_'
    _status_id = 1
    _command_id = 1

    def __init__(self, instance_name,
                 device_register_topic='subscribe/add_devices',
                 device_stat_req_topics=''):

        self._instance_id = instance_name
        self._device_status_resp_topic = 'devices/get_status/response'
        self._device_add_status = 'devices/add_device/{}/response'
        self._light_device_add_status = 'devices/add_device/light/response'
        self._ac_device_add_status = 'devices/add_device/ac/response'
        self._device_msg_topic = 'home/devices/+/#'
        if len(device_stat_req_topics) > 1:
            self._device_stat_req_topics_template = device_stat_req_topics
        else:
            self._device_stat_req_topics_template = {'device_type': 'devices/get/status/{}',
                                                     'room': 'devices/get/status/{}'}
        self._room_types = list()
        self._device_types = list()
        self._device_stat_req_topics = dict()
        self.client = mqtt.Client(self._instance_id)
        self._connect_success = False
        self._bad_connection = False
        self._status_req_wait = True
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._device_register_topic = device_register_topic
        self.client.connect(HOST, PORT, keepalive=60)
        self.client.loop_start()
        self.connection_status_check()
        self._messages_dict = dict()
        self._status_response_dict = dict()
        self._status_request_stat = dict()
        self._registered_dict = dict()

    # Terminating the MQTT broker and stopping the execution
    def terminate(self):
        self.client.disconnect()
        self.client.loop_stop()

    # Connect method to subscribe to various topics.
    # device_register topic - new device addition will be done thru this topic.
    # device_status_response topic - topic to get the status response from device.
    def _on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            print('Edge server {} has been connected with result_code {}'.format(self._instance_id, result_code))
            self._connect_success = True
            print('Edge server {} will be connected to {}'.format(self._instance_id, self._device_register_topic))
            self._sub_to_topic(self._device_register_topic)
            print('Edge server {} will be connected to {}'.format(self._instance_id, self._device_msg_topic))
            self._sub_to_topic(self._device_msg_topic)
            print('Edge server {} will be connected to {}'.format(self._instance_id, self._device_status_resp_topic))
            self._sub_to_topic(self._device_status_resp_topic)
        else:
            print('Edge server {} connection failed with result_code {}'.format(self._instance_id, result_code))
            self._bad_connection = True
        # pass

    # method to process the received messages and publish them on relevant topics
    # this method can also be used to take the action based on received commands
    def _on_message(self, client, userdata, msg):
        temp_msg_payload = json.loads(msg.payload.decode())
        if msg.topic == self._device_register_topic:
            msg_list = self._messages_dict.get(msg.topic, [])
            msg_list.append(temp_msg_payload)
            # print(msg.payload.decode())
            self._messages_dict[msg.topic] = msg_list
            self._set_device_registration_list()
        # elif msg.topic == self._light_device_status_topic or msg.topic == self._ac_device_status_topic:
        elif msg.topic == self._device_status_resp_topic:
            print('Response received for {} status id.'.format(temp_msg_payload['status_id']))
            status_msgs = self._status_response_dict.get(temp_msg_payload['status_id'], [])
            status_msgs.append(temp_msg_payload)
            self._status_response_dict[temp_msg_payload['status_id']] = status_msgs
            self._update_response_status(temp_msg_payload['status_id'])
            # self._respond_status_to_client(msg.topic)

    # Returning the current registered list
    def get_registered_device_list(self):
        return self._registered_dict.keys()

    # Getting the status for the connected devices
    def get_status(self, request_mode='all', device_type='', room_type='', device_id=''):
        status_id = self._get_status_id()
        self._set_status_id()
        status_valid = False
        status_valid, status_topics, device_id_list = self._get_topic_device(request_mode,
                                                                             device_type,
                                                                             room_type,
                                                                             device_id,
                                                                             'get_status')
        if status_valid:
            for status_topic in status_topics:
                msg = self._build_status_req_msg_topic(status_id,
                                                       'get_status',
                                                       request_mode,
                                                       device_type,
                                                       room_type,
                                                       '',
                                                       device_id_list)
                print('Status request for {} status id will be sent to - {}'.format(status_id,
                                                                                    status_topic))
                print('status id {}, payload - {}'.format(status_id, msg))
                self._pub_to_topic(status_topic, msg)
            no_of_devices = 1
            if isinstance(device_id_list, list):
                no_of_devices = len(device_id_list)
            self._status_request_stat = {status_id: {'no_of_req_sent': no_of_devices,
                                                     'response_wait_time':
                                                         datetime.datetime.now() +
                                                         datetime.timedelta(seconds=no_of_devices * 2),
                                                     'no_of_resp_received': 0}}
            return status_id, no_of_devices
        else:
            print('Status request for {} status id will not be processed, do verify the request.'.
                  format(status_id))
            return status_id, 0

    # Builds the topic & device to which get / set request has to be published
    def _get_topic_device(self, request_mode, device_type, room_type, device_id, request_type):
        status_valid = True
        if request_type != 'get_status':
            if len(device_id) > 1:
                request_mode = 'device_id'
            elif len(room_type) > 1:
                request_mode = 'room'
            elif len(device_type) > 1:
                request_mode = 'device_type'
            else:
                status_valid = False

        if status_valid:
            status_valid, status_topics = self._get_status_req_topics(request_mode, device_type,
                                                                      room_type, device_id)
        if status_valid and status_topics:
            status_valid, device_id_list = self._get_device_ids(request_mode, device_id, device_type, room_type)
        return status_valid, status_topics, device_id_list

    # Returns number of responses and wait state to client
    # If wait time passed then will make the client to skip the wait loop
    def get_status_req_state(self, status_id):
        temp_wait_state = self._status_req_wait
        if datetime.datetime.now() > self._status_request_stat[status_id]['response_wait_time']:
            temp_wait_state = False
        return temp_wait_state, self._status_request_stat[status_id]['no_of_resp_received']

    # Returns the status response to client
    def get_status_response(self, status_id):
        resp_msg = list()
        for msg in self._status_response_dict[status_id]:
            if 'error_msg' in msg.keys():
                resp_msg.append(msg['error_msg'])
            else:
                temp_msg_dict = dict()
                for k, v in msg.items():
                    if k != 'status_id':
                        temp_msg_dict[k] = v
                resp_msg.append(temp_msg_dict)
        del self._status_response_dict[status_id]
        return resp_msg

    # Controlling and performing the operations on the devices
    # based on the request received
    def set_status(self, request_mode='all', device_type='light', room_type='', device_id='',
                   set_status='toggle', set_control=''):
        status_id = self._get_status_id()
        self._set_status_id()
        status_valid = False
        status_valid, status_topics, device_id_list = self._get_topic_device(request_mode,
                                                                             device_type,
                                                                             room_type,
                                                                             device_id,
                                                                             'set_status')
        if status_valid:
            for status_topic in status_topics:
                msg = self._build_status_req_msg_topic(status_id,
                                                       'set_status',
                                                       request_mode,
                                                       device_type,
                                                       room_type,
                                                       set_control,
                                                       device_id_list)
                print('Status request for {} status id will be sent to - {}'.format(status_id,
                                                                                    status_topic))
                print('status id {}, payload - {}'.format(status_id, msg))
                self._pub_to_topic(status_topic, msg)
            no_of_devices = 1
            if isinstance(device_id_list, list):
                no_of_devices = len(device_id_list)
            self._status_request_stat = {status_id: {'no_of_req_sent': no_of_devices,
                                                     'response_wait_time':
                                                         datetime.datetime.now() +
                                                         datetime.timedelta(seconds=no_of_devices * 2),
                                                     'no_of_resp_received': 0}}
            return status_id, no_of_devices
        else:
            print('Status request for {} status id will not be processed, do verify the request.'.
                  format(status_id))
            return status_id, 0

    # Wait for the connection establishment and if it isn't successful call the terminate function to disconnect
    def connection_status_check(self):
        while not self._connect_success and not self._bad_connection:
            time.sleep(1)

        if not self._connect_success:
            print('Edge server {} connection failed, hence terminating the connection'.format(self._instance_id))
            self.terminate()

    # Returning the connection status detail
    def get_edge_connect_success(self):
        return self._connect_success

    # Adds the newly registered device to registered list
    # Update the topics to be published when there is a get_status request for the devices
    def _set_device_registration_list(self):
        registered_device_list = self._messages_dict[self._device_register_topic]
        for device in registered_device_list:
            print('Registration request is acknowledged for device {} in {}'.format(device['device_id'],
                                                                                    device['room']))
            if device['device_id'] not in self._registered_dict.keys():
                self._registered_dict[device['device_id']] = {'device_type': device['device_type'],
                                                              'room': device['room']}
            if device['device_type'] not in self._device_types:
                self._device_types.append(device['device_type'])
                temp_device_type_topics = self._device_stat_req_topics.get('device_type', [])
                temp_device_type_topics.append(self._device_stat_req_topics_template['device_type'].
                                               format(device['device_type']))
                self._device_stat_req_topics['device_type'] = temp_device_type_topics

            if device['room'] not in self._room_types:
                self._room_types.append(device['room'])
                temp_device_type_topics = self._device_stat_req_topics.get('room', [])
                temp_device_type_topics.append(self._device_stat_req_topics_template['room'].
                                               format(device['room']))
                self._device_stat_req_topics['room'] = temp_device_type_topics

            request_topics = list()
            request_topics.append(self._device_stat_req_topics_template['device_type'].
                                  format(device['device_type']))
            request_topics.append(self._device_stat_req_topics_template['room'].
                                  format(device['room']))
            self._device_reg_ack(device['device_id'], device['device_type'], device['room'], request_topics)
            request_topics.clear()
            print('Request is processed for {}.'.format(device['device_id']))
            print('Available topics for get status request: ', self._device_stat_req_topics)
        self._messages_dict[self._device_register_topic] = []

    # Sends device registration acknowledgement to respective topic
    def _device_reg_ack(self, device_id, device_type, device_room, request_topics,
                        device_request="add", device_req_status="success"):
        device_req_res_topic = self._device_status_resp_topic

        device_ack = {"device_id": device_id,
                      "request": device_request,
                      "request_status": device_req_status,
                      "device_topic": self._device_msg_topic.replace('+', device_room).replace('#', device_id),
                      "request_topics": request_topics,
                      "device_req_res_topic": device_req_res_topic,
                      "timestamp": self.get_current_timestamp()}
        self._pub_to_topic(self._device_add_status.format(device_type), device_ack)

    # Subscribe to the topic
    def _sub_to_topic(self, topic):
        self.client.subscribe(topic)

    # Publish to the topic
    def _pub_to_topic(self, topic, msg):
        self.client.publish(topic, json.dumps(msg))

    # Builds the request message for the topic
    def _build_status_req_msg_topic(self, status_id, request, request_mode, device_type,
                                    room_type, control, device_ids):
        msg = {"status_id": status_id,
               "request": request,
               "request_mode": request_mode,
               "device_type": device_type,
               "room_type": room_type,
               "controller": control,
               "device_id": device_ids,
               "timestamp": self.get_current_timestamp()}
        return msg

    # Updates the response stats for the respective requests
    def _update_response_status(self, status_id):
        temp_count = self._status_request_stat[status_id]['no_of_resp_received'] + 1
        self._status_request_stat[status_id]['no_of_resp_received'] = temp_count

    # Returns current timestamp
    @staticmethod
    def get_current_timestamp():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Provides the list of topics to which status request messages has to be published
    def _get_status_req_topics(self, request_mode, device_type, room_type, device_id):
        status_req_topics = []
        request_status = False
        if request_mode == 'device_type':
            request_status = True
            if isinstance(device_type, str) and len(device_type) > 0:
                for device_type_topic in self._device_stat_req_topics['device_type']:
                    # print('device_type_topic - ', device_type_topic)
                    if device_type_topic.endswith(device_type):
                        status_req_topics.append(device_type_topic)
        elif request_mode == 'room':
            request_status = True
            if isinstance(room_type, str) and len(room_type) > 0:
                for device_type_topic in self._device_stat_req_topics['room']:
                    # print('device_type_topic - ', device_type_topic)
                    if device_type_topic.endswith(room_type):
                        status_req_topics.append(device_type_topic)
        elif request_mode == 'device_id':
            request_status = True
            device_type = self._get_device_type(device_id)
            for device_type_topic in self._device_stat_req_topics['device_type']:
                if device_type_topic.endswith(device_type):
                    status_req_topics.append(device_type_topic)
        elif request_mode == 'all':
            if 'device_type' in self._device_stat_req_topics:
                request_status = True
                status_req_topics = self._device_stat_req_topics['device_type']
            elif 'room' in self._device_stat_req_topics:
                request_status = True
                status_req_topics = self._device_stat_req_topics['room']

        return request_status, status_req_topics

    # Provides the list of topics to which status request messages has to be published
    def _get_device_ids(self, request_mode, device, device_type, room):
        request_status = True
        if isinstance(device, str) and len(device) > 1:
            if device not in self._registered_dict.keys():
                request_status = False
            return request_status, device
        else:
            status_req_devices = list()
        if request_mode == 'device_type':
            status_req_devices.clear()
            for device, device_info in self._registered_dict.items():
                if device_info['device_type'].lower() == device_type.lower():
                    status_req_devices.append(device)
        elif request_mode == 'room':
            status_req_devices.clear()
            for device, device_info in self._registered_dict.items():
                if device_info['room'].lower() == room.lower():
                    status_req_devices.append(device)
        elif request_mode == 'all':
            for device in self._registered_dict.keys():
                if device not in status_req_devices:
                    status_req_devices.append(device)
        else:
            request_status = False

        return request_status, status_req_devices.copy()

    # Returns the device type based on device id
    def _get_device_type(self, device_id):
        return self._registered_dict[device_id]['device_type']

    # Return the current status id
    @classmethod
    def _get_status_id(cls):
        return cls._status_id_prefix + str(cls._status_id)

    # Return the current command id
    @classmethod
    def _get_command_id(cls):
        return cls._command_id_prefix + str(cls._command_id)

    # Increments the status id
    @classmethod
    def _set_status_id(cls):
        cls._status_id += 1

    # Increments the command id
    @classmethod
    def _set_command_id(cls):
        cls._command_id += 1
