# printer_police
Source code for the ESP32 communications, notes and data analysis

In platform IO install the libraries:
- HX711_ADC by Olav Kallhovd 
- MPU9250_WE by Wolfgang Ewald
- Encoder by Paul Stoffregen (this is untested so you may have to find a different one if it doesnt work)

# How to find your wifi IP address
You need to know your wifi ip address for your network before connecting to wifi on the exp32

To find what your wifi ip adress is
1. go to "command prompt" on windows or "terminal" on mac
2. type ipconfig on windows or ifconfig -a on mac
3. under the section "Wireless LAN adapter Wifi" copy the address next to "IPv4 Address" or "Default Gateway"
Note: we have been using the one on "IPv4 Address" for testing, but upon research the one on "Default Gateway" may be a better option
![image](https://user-images.githubusercontent.com/106965302/174427507-f072d176-7c37-4d25-8e02-430c3db42f92.png)

4. Now you have your router/wifi ip address!


# How to run wifi
1. On data_rcv.py file change the IP address on it to your wifi IP addess
![image](https://user-images.githubusercontent.com/106965302/174428092-a332782f-2be6-4d2b-a602-e081ac14a852.png)

2. Run the files main.cpp and data_rcv.py
3. Go to your wifi and internet settings and click thw wifi "onDemandAP"

![image](https://user-images.githubusercontent.com/106965302/174426112-4ef3007b-5a36-43a9-b5cb-2a858868fdae.png)

4. Once you click on it, click "configure wifi"
5. Then select your internet
6.
   * Enter SSID (wifi name)
   * Enter your wifi password
   * your Wifi IP address
   * The port you wish to connect to (e.g 5000)

7. Then click save


