import time
from EdgeServer import Edge_Server
from LightDevice import LightDevice
from ACDevice import ACDevice

WAIT_TIME = 0.25  

print("\nSmart Home Simulation started.")
# Creating the edge-server for the communication with the user

edge_server_1 = Edge_Server('edge_server_1')
time.sleep(WAIT_TIME)  

print('\n******************* REGISTRATION OF LIGHT DEVICES INITIATED *******************\n')
# Creating the light_device
print("Initiate the device creation and registration process." )
print("\nCreating the Light devices for their respective rooms.")
light_device_1 = LightDevice("light_1", "Kitchen")
time.sleep(WAIT_TIME)  
time.sleep(WAIT_TIME)
light_device_2 = LightDevice("light_2", "Hall")
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)
light_device_3 = LightDevice("light_3", "BR1")
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)

print('\n******************* REGISTRATION OF AC DEVICES INITIATED *******************\n')
# Creating the ac_device  
print("\nCreating the AC devices for their respective rooms.")
ac_device_1 = ACDevice("ac_1", "BR1")
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)
ac_device_2 = ACDevice("ac_2", "BR2")
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)

print('\n******************* REGISTERED DEVICES ON THE SERVER *******************\n')
print('Fetching the list of registered devices from EdgeServer')
print('The Registered devices on Edge-Server:')
current_reg_device_list = edge_server_1.get_registered_device_list()
print(current_reg_device_list)


def check_status(status_req_id, no_of_devices_req):
    print('Status_id - {}, number of devices - {}.'.format(status_req_id, no_of_devices_req))
    wait_state = True
    resp_received = 0
    if no_of_devices_req > 0:
        while resp_received < no_of_devices_req and wait_state:
            wait_state, resp_received = edge_server_1.get_status_req_state(status_req_id)
            time.sleep(WAIT_TIME)

        if no_of_devices_req == resp_received:
            print('Here is the response for {}: \n'.format(status_req_id))
        else:
            print('Not all requests were process, {} processed for {} status id. \n'.format(resp_received, status_req_id))
            print('Here is the response for {}: \n'.format(status_req_id))

        if resp_received > 0:
            for device_response in edge_server_1.get_status_response(status_req_id):
                if 'device_id' in device_response:
                    print('Here is the current device-status for {}: {}'.format(device_response['device_id'],
                                                                                device_response))
                else:
                    print(device_response)
        else:
            print('No response received for {} status id. \n'.format(status_req_id))
    else:
        print('Status id - {}, not processed. Check the request call'.format(status_req_id))


print('\n******************* GETTING THE STATUS AND CONTROLLING THE DEVICES *******************\n')

print('******************* GETTING THE STATUS BY DEVICE_ID *******************\n')
status_id, no_of_devices = edge_server_1.get_status(request_mode='device_id', device_id='ac_1')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* GETTING THE STATUS BY DEVICE_TYPE *******************\n')
status_id, no_of_devices = edge_server_1.get_status(request_mode='device_type', device_type='light')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* GETTING THE STATUS BY ROOM_TYPE *******************\n')
status_id, no_of_devices = edge_server_1.get_status(request_mode='room', room_type='kitchen')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* GETTING THE STATUS BY ENTIRE_HOME *******************\n')
status_id, no_of_devices = edge_server_1.get_status()
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
time.sleep(WAIT_TIME)

print('******************* SETTING UP THE STATUS AND CONTROLLING THE DEVICE_ID *******************\n')
status_id, no_of_devices = edge_server_1.set_status(request_mode='device_id', device_id='ac_1')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
status_id, no_of_devices = edge_server_1.set_status(request_mode='device_id', device_id='ac_1', set_control=27)
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* SETTING UP THE STATUS AND CONTROLLING BY THE DEVICE_TYPE *******************\n')
status_id, no_of_devices = edge_server_1.set_status()
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
status_id, no_of_devices = edge_server_1.set_status(request_mode='all', device_type='light')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)
time.sleep(WAIT_TIME)

print('******************* SETTING UP THE STATUS AND CONTROLLING BY ROOM *******************\n')
status_id, no_of_devices = edge_server_1.set_status(request_mode='all', device_type='light', room_type='kitchen')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* SETTING UP THE STATUS AND CONTROLLING FOR INVALID REQUESTS *******************\n')
status_id, no_of_devices = edge_server_1.set_status(request_mode='device_id', device_id='ac_1', set_control=33)
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
status_id, no_of_devices = edge_server_1.set_status(set_control='lower')
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print('******************* CURRENT STATUS BEFORE CLOSING THE PROGRAM *******************\n')
status_id, no_of_devices = edge_server_1.get_status()
time.sleep(WAIT_TIME)
check_status(status_id, no_of_devices)
print("\nSmart Home Simulation stopped.")
edge_server_1.terminate()
light_device_1.terminate()
light_device_2.terminate()
ac_device_1.terminate()
