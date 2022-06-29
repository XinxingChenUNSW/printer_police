#include <Arduino.h>
#include <WiFiManager.h>

#define MAX_IP_LEN 15

// WiFi Configurations, TODO: Abstract out
char ssid[MAX_SSID_LEN] = "";
char password[MAX_PASSPHRASE_LEN] = "";

uint16_t port = 5000;
char host[MAX_IP_LEN] = "172.20.10.2";

#define TRIGGER_PIN 0

// Buffer for storing sensor data
uint8_t buf[200] = {};

WiFiClient client;
WiFiManager wm;

void init_wifi();
void wifi_send_data();
bool clientConnect();
void wifiTask(void *parameter);

// Handles for the two cores
TaskHandle_t Task1, Task2;
int a = 1;

// TODO: Sensors running on one core with multithreading and writing to a buffer, 
// 		 WiFi running on the other core and sending data over WiFi
const int ledPin = 2;

void rando(void *parameter) {

	while (true) {
		Serial.print(a);

		delay(500);
	}
} 

void setup() {
	// put your setup code here, to run once:
	Serial.begin(115200);
	pinMode (ledPin, OUTPUT);

	// Initialise WiFi scan
	init_wifi();

	// Assign wifi tasks to Core 2
	xTaskCreatePinnedToCore(rando, "Hello", 5000, NULL, 2, &Task1, 0);
	xTaskCreatePinnedToCore(wifiTask, "SumTask", 5000, NULL, 2, &Task2, 1);
	
}

int timeout = 120;

void loop() {
	// put your main code here, to run repeatedly:
	// TODO: 
 
    delay(100);
}


bool clientConnect() {
	if (!client.connect(host, port)) {
	
		Serial.println("Connection to host failed");
		return false;
	}

	Serial.print("Connected to ");
	Serial.print(host);
	Serial.print(" at port ");
	Serial.println(port);

	return true;
}

// UNUSED
void wifiConnected(WiFiEvent_t event, WiFiEventInfo_t info) {
	Serial.print("Connected to WiFi with IP: ");
	Serial.println(WiFi.localIP());
	while (!clientConnect()) {
		delay(500);
	}
}

// UNUSED
void wifiDisconnected(WiFiEvent_t event, WiFiEventInfo_t info) {
	Serial.println("Disconnected from WIFI access point");
	Serial.println("Reconnecting...");
	WiFi.begin(ssid, password);
}

void clientLost(WiFiEvent_t event, WiFiEventInfo_t info) {
	Serial.print("CLIENNT LOST D:");
}

void configModeCallback (WiFiManager *myWiFiManager) {
	Serial.println("Entered config mode");
	Serial.println(WiFi.softAPIP());

	Serial.println(myWiFiManager->getConfigPortalSSID());
	
}

void init_wifi() {

	WiFi.mode(WIFI_STA);

	int portal_timeout = 180;

	// Set up Wifi Manager Portal
	wm.resetSettings();

	wm.setAPCallback(configModeCallback);

	// Extra form parameters
	WiFiManagerParameter port_number("portId", "Port Label", "5000", 10);
	wm.addParameter(&port_number);


	WiFiManagerParameter ip_address("ipPop", "Ip Address", "0.0.0.0", 15);
	wm.addParameter(&ip_address);

	// wm.setConfigPortalTimeout(portal_timeout);

	if (!wm.startConfigPortal("OnDemandAP")) {
		Serial.println("Failed to connect");
		return;
	}

	Serial.println("CONNECTED");
	// Set up WiFi events
	WiFi.onEvent(wifiDisconnected, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);
	WiFi.onEvent(wifiConnected, ARDUINO_EVENT_WIFI_STA_CONNECTED);

	// Get SSID and Password from WiFi Manager
	strcpy(ssid, wm.getWiFiSSID().c_str());
	strcpy(password, wm.getWiFiPass().c_str());

	// Port number and Host parameters
	port = std::stoi(port_number.getValue());
	strcpy(host, ip_address.getValue());

	Serial.println(host);

	WiFi.begin(ssid, password);
}

void wifi_send_data(uint8_t *buf) {
	// char temp[] = "\r\tHELLO THERE\r\n";

	// uint8_t *tempBuf; (uint8_t *)temp;
	// memcpy(buf, temp, sizeof(temp));
	float temp[5] = {
		10.0,
		15.0
		-0.5,
		3.0,
		2.0
	};

	char startBytes[] = "COVID";
	// char stopBytes[] = "DOVIC";

	uint8_t buf[sizeof(startBytes) + sizeof(sensorData)] = startBytes;

	int curr_ptr = 0;
	
	memcpy(buf, startBytes, sizeof(startBytes) - 1);
	curr_ptr += sizeof(startBytes) - 1;
	memcpy(buf+curr_ptr, temp, sizeof(temp));
	curr_ptr += sizeof(temp);
	memcpy(buf+curr_ptr, stopBytes, sizeof(stopBytes));

	client.write(buf, sizeof(buf));
}

void wifiTask(void *parameter) {
	char startBytes[] = "COVID";
	uint8_t buf[sizeof(startBytes) + sizeof(sensorData)] = startBytes;

	memcpy(buf, startBytes, sizeof(startBytes) - 1);

	while (true) {
		if (WiFi.status() == WL_CONNECTED)
			if (client.connected())
				wifi_send_data(buf, sizeof(startBytes) - 1);
			else {
				WiFi.disconnect();
				clientConnect();
			}
		else {
			
		}
		delay(100);

		a += 1;
	}
}