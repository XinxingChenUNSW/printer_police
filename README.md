# printer_police
Source code for the ESP32 communications, notes and data analysis

In platform IO install the libraries:
- HX711_ADC by Olav Kallhovd 
- MPU9250_WE by Wolfgang Ewald
- ESP32Encoder by Madhephaestus 

# How to find your WiFi IP address
You need to know your WiFi IP address for your network before connecting to WiFi on the ESP32

To find what your WiFi IP address is:
1. Go to "command prompt" on windows or "terminal" on mac
2. Type ipconfig on windows or ifconfig -a on mac
3. Under the section "Wireless LAN adapter Wifi" copy the address next to "IPv4 Address" or "Default Gateway"
Note: we have been using the one on "IPv4 Address" for testing, but after testing, the one on "Default Gateway" may be a better option
![image](https://user-images.githubusercontent.com/106965302/174427507-f072d176-7c37-4d25-8e02-430c3db42f92.png)

4. Now you have your router/WiFi IP address!


# How to connect to the WiFi 

1. Ensure the ESP32 is turned on. Go to your WiFi and internet settings and click the wifi "onDemandAP"

![image](https://user-images.githubusercontent.com/106965302/174426112-4ef3007b-5a36-43a9-b5cb-2a858868fdae.png)

2. Once you click on it, your browser should automatically open a new window displaying some buttons. Click "Configure Wifi"
3. Select your WiFi SSID in the list of available networks. 
4. Input the WiFI, WiFi IP address (which you found above) as well as the port you wish to connect to (e.g 5000).
5. Click Save and wait a couple of seconds. 

*If you believe you have input any settings in correctly or want to connect to a different network, disconnect from onDemandAP and reconnect to it and repeat the above steps again. If this does not work, turn off the ESP32 before turning it on again and repeat the above steps again.* 

# How to run the Python script to get the live plots displaying:

1. Navigate to data_rcv.py and run the script in your IDE.
2. Input the IP address and port number (which you used above). 

![pythonscript](https://user-images.githubusercontent.com/42131486/183277694-df89ffd6-5eee-43e7-af2c-59a7eb8a9c1b.PNG)

3. Press Enter. If successful, a new window should open automatically displaying the plots and UI. Press the "Start Live Plotting" button and the UI should display the plots in real-time similar to the image below. 

![nozzle_firing_graph](https://user-images.githubusercontent.com/42131486/183277724-326f91f1-003f-4800-a754-21b5a03ef3d3.PNG)

4. If you want to stop the live plotting, press the "Stop Live Plotting" button. If you want to export the raw data to CSV, press the "Export to CSV" button. 

# How to update the code on the ESP32 

*By default, the ESP32 operates in wireless mode, which does not require a USB connection between a computer and itself. However, if you want to update the code on the ESP32, follow the steps below.*

1. Connect the ESP32 to a computer via micro-USB cable.
2. After updating the code, press the 'Build' button in the platformIO interface to ensure the code compiles correctly. This is represented by the tick in the image below.
3. If the build is successful, you can upload the code onto the ESP32 by pressing the 'Upload' button. This is represented by the arrow next to the build button in the image below. 

![buildupload](https://user-images.githubusercontent.com/42131486/183278157-cb4f4fc8-cca1-4a05-8c76-35bd7fffb8c0.PNG)

# How to perform debugging on the ESP32

*Debugging requires a USB connection between the ESP32 and a computer. 

1. To perform debugging, add some print statements such as the image below in the main.cpp file where the ESP32 code is located. 
![serialprint](https://user-images.githubusercontent.com/42131486/183277930-b9e97f2f-78b6-44a8-b77c-2531c925b616.PNG)

2. Open the 'Serial Monitor' in platformIO. This is represented by the power plug button as shown in the image below.
![serialmonitor](https://user-images.githubusercontent.com/42131486/183278014-7018200b-79af-4884-93ec-d21e00b032ec.PNG)
 
3. Output should now be viewable. 



