#include "Arduino.h"
#include <WiFiManager.h>
/*
In platform IO install the libraries
  HX711_ADC by Olav Kallhovd 
  MPU9250_WE by Wolfgang Ewald
  Encoder by Paul Stoffregen (this is untested so you may have to find a different one if it doesnt work)

*/

// Select which test you want to run by commenting the ones you dont (this is a compiled setting)
#define LOAD_CELLS
#define MPU
#define ENCODER
// Load cell amplifier pin numbers
#define LOAD_DOUT_1 21
#define LOAD_SCK_1 22
#define LOAD_DOUT_2 14
#define LOAD_SCK_2 27

// Accelerometer/Gyro Pins
#define SDA_1 19
#define SCL_1 18
#define SDA_2 26
#define SCL_2 25

//Encoder pins
#define PIN_A 13
#define PIN_B 15

// If we want to see the accelerometer/gyro data
#ifdef MPU
// Includes
#include <MPU6500_WE.h>
#include <Wire.h>
// i2c address of the sensor
#define MPU6500_ADDR 0x68
// The ESP32 supports 2 i2c at the same time these are defined here
TwoWire I2Cone = TwoWire(0);
TwoWire I2Ctwo = TwoWire(1);

TaskHandle_t Task1;
TaskHandle_t Task2;

// Creating the Acc/gyro instances 
MPU6500_WE MPU_1 = MPU6500_WE(&I2Cone, MPU6500_ADDR);
MPU6500_WE MPU_2 = MPU6500_WE(&I2Ctwo, MPU6500_ADDR);
// c++ throws an error if we try to call this before its defined
void configureMPU(MPU6500_WE *mpu);
#endif

// If we want to see the load cells data
#ifdef LOAD_CELLS
// Include the library
#include <HX711_ADC.h>

//HX711 constructor instances of load cells (dout pin, sck pin)
HX711_ADC LoadCell_1(LOAD_DOUT_1, LOAD_SCK_1); //HX711 1
HX711_ADC LoadCell_2(LOAD_DOUT_2, LOAD_SCK_2); //HX711 2

#endif

// Encoder
#ifdef ENCODER
#include <ESP32Encoder.h>

ESP32Encoder encoder;
ESP32Encoder encoder2;

// timer and flag for example, not needed for encoders
unsigned long encoder2lastToggled;
bool encoder2Paused = false;



// Change these two numbers to the pins connected to your encoder.
//   Best Performance: both pins have interrupt capability
//   Good Performance: only the first pin has interrupt capability
//   Low Performance:  neither pin has interrupt capability

#endif

// The time object for looping without using delay
unsigned long t = 0;

void getSensorData(void * pvParameters) {
  while(true){
    #ifdef LOAD_CELLS
    static boolean newDataReady = 0;
    const int serialPrintInterval = 0; //increase value to slow down serial print activity

    // check for new data/start next conversion:
    if (LoadCell_1.update()) newDataReady = true;
    LoadCell_2.update();

    //get smoothed value from data set
    if ((newDataReady)) {
      if (millis() > t + serialPrintInterval) {
        float a = LoadCell_1.getData();
        float b = LoadCell_2.getData();
        // This is where you would hook in to get the values from the load cells
        Serial.print("Load_cell 1 output val: ");
        Serial.print(a);
        Serial.print("    Load_cell 2 output val: ");
        Serial.println(b);
        newDataReady = 0;
        t = millis();
      }
    }
    // allows for zeroing of the load cells from the terminal
    // receive command from serial terminal, send 't' to initiate tare operation:
    if (Serial.available() > 0) {
      char inByte = Serial.read();
      if (inByte == 't') {
        LoadCell_1.tareNoDelay();
        LoadCell_2.tareNoDelay();
      }
    }

    //check if last tare operation is complete
    if (LoadCell_1.getTareStatus() == true) {
      Serial.println("Tare load cell 1 complete");
    }
    if (LoadCell_2.getTareStatus() == true) {
      Serial.println("Tare load cell 2 complete");
    }
    #endif

    #ifdef MPU
    xyzFloat gValue_1 = MPU_1.getCorrectedAccRawValues();
    xyzFloat gyr_1 = MPU_1.getGyrValues();
    xyzFloat gValue_2 = MPU_2.getCorrectedAccRawValues();
    xyzFloat gyr_2 = MPU_2.getGyrValues();
    float temp_1 = MPU_1.getTemperature();
    float temp_2 = MPU_2.getTemperature();
    xyzFloat ggValue_1 = MPU_1.getGValues();
    float resultantG_1 = MPU_1.getResultantG(ggValue_1);
    xyzFloat ggValue_2 = MPU_2.getGValues();
    float resultantG_2 = MPU_2.getResultantG(ggValue_2);

    Serial.print("Acc1 (x,y,z): (");
    Serial.print(gValue_1.x / 4096);
    Serial.print(",");
    Serial.print(gValue_1.y / 4096);
    Serial.print(",");
    Serial.print(gValue_1.z / 4096);
    Serial.print(")");
    Serial.print(" Gyro1: (");
    Serial.print(gyr_1.x);
    Serial.print(",");
    Serial.print(gyr_1.y);
    Serial.print(",");
    Serial.print(gyr_1.z);
    Serial.print(") Acc2: (");
    Serial.print(gValue_2.x / 4096);
    Serial.print(",");
    Serial.print(gValue_2.y / 4096);
    Serial.print(",");
    Serial.print(gValue_2.z / 4096);
    Serial.print(")");
    Serial.print(" Gyro2: (");
    Serial.print(gyr_2.x);
    Serial.print(",");
    Serial.print(gyr_2.y);
    Serial.print(",");
    Serial.print(gyr_2.z);
    Serial.println(")");
    Serial.print("Resultant g_1: ");
    Serial.println(resultantG_1); // should always be 1 g if only gravity acts on the sensor.
    Serial.println();
    Serial.print("Resultant g_2: ");
    Serial.println(resultantG_2); // should always be 1 g if only gravity acts on the sensor.
    Serial.println();

    Serial.print("Current code ID in loop is SDFDSFDSFDSF: ");
    Serial.println(xPortGetCoreID());
    delay(200);
    #endif

    #ifdef ENCODER
    Serial.println("TESTING THIS ENCODER CODE");
    // Loop and read the count
    Serial.println("Encoder count = " + String((int32_t)encoder.getCount()) + " " + String((int32_t)encoder2.getCount()));
    delay(100);

    // every 5 seconds toggle encoder 2
    if (millis() - encoder2lastToggled >= 5000) {
      if(encoder2Paused) {
        Serial.println("Resuming Encoder 2");
        encoder2.resumeCount();
      } else {
        Serial.println("Paused Encoder 2");
        encoder2.pauseCount();
      }

      encoder2Paused = !encoder2Paused;
      encoder2lastToggled = millis();
    }
    #endif
  }
}

void Task2code( void * pvParameters ){
  String taskMessage = "Task 2 running on core ";
  taskMessage = taskMessage + xPortGetCoreID();

  while(true){
      Serial.println(taskMessage);
      delay(1000);
  }
}

void IRAM_ATTR isr() {
  int i = 2;
}

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


// TODO: Sensors running on one core with multithreading and writing to a buffer, 
// 		 WiFi running on the other core and sending data over WiFi
const int ledPin = 2;


void setup() {
  // Connects to the serial output
  Serial.begin(115200); delay(10);

  pinMode(PIN_A, INPUT_PULLUP);
  attachInterrupt(PIN_A, isr, FALLING);
  // The Load cell start up code
  #ifdef LOAD_CELLS
  // These will need to be adjusted in testing essentially handing a known weight from them

  float calibrationValue_1 = 1.0;
  float calibrationValue_2 = 1.0;
  // Start the connection with the amplifiers
  LoadCell_1.begin();
  LoadCell_2.begin();

  // float  calibrationValue_1 = LoadCell_1.getNewCalibration(-500);
  // float  calibrationValue_2 = LoadCell_2.getNewCalibration(-500);

  unsigned long stabilizingtime = 2000; // tare preciscion can be improved by adding a few seconds of stabilizing time
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  byte loadcell_1_rdy = 0;
  byte loadcell_2_rdy = 0;
  // while ((loadcell_1_rdy + loadcell_2_rdy) < 2) { //run startup, stabilization and tare, both modules simultaniously
  //   if (!loadcell_1_rdy) loadcell_1_rdy = LoadCell_1.startMultiple(stabilizingtime, _tare);
  //   if (!loadcell_2_rdy) loadcell_2_rdy = LoadCell_2.startMultiple(stabilizingtime, _tare);
  // }
  LoadCell_1.tare();
  LoadCell_2.tare();
  if (LoadCell_1.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 no.1 wiring and pin designations");
  }
  if (LoadCell_2.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 no.2 wiring and pin designations");
  }
  LoadCell_1.setCalFactor(calibrationValue_1); // user set calibration value (float)
  LoadCell_2.setCalFactor(calibrationValue_2); // user set calibration value (float)
  Serial.println("Loadcell startup is complete");

  Serial.print("Current code ID in startup is: ");
  Serial.println(xPortGetCoreID());


    // Enable the weak pull down resistors

    //ESP32Encoder::useInternalWeakPullResistors=DOWN;
    // Enable the weak pull up resistors
    ESP32Encoder::useInternalWeakPullResistors=UP;

    // use pin 19 and 18 for the first encoder
    encoder.attachHalfQuad(19, 18);
    // use pin 17 and 16 for the second encoder
    encoder2.attachHalfQuad(17, 16);
      
    // set starting count value after attaching
    encoder.setCount(37);

    // clear the encoder's raw count and set the tracked count to zero
    encoder2.clearCount();
    Serial.println("Encoder Start = " + String((int32_t)encoder.getCount()));
    // set the lastToggle
    encoder2lastToggled = millis();



      // Initialise WiFi scan
    init_wifi();

    // Assign wifi tasks to Core 2
    xTaskCreatePinnedToCore(wifiTask, "SumTask", 5000, NULL, 2, &Task2, 1);

    xTaskCreatePinnedToCore(
                  getSensorData,   /* Task function. */
                  "Task1",     /* name of task. */
                  5000,       /* Stack size of task */
                  NULL,        /* parameter of the task */
                  1,           /* priority of the task */
                  &Task1,      /* Task handle to keep track of created task */
                  0); 
  #endif

  // Start up code for the 
  #ifdef MPU
  I2Cone.begin(SDA_1, SCL_1);
  I2Ctwo.begin(SDA_2, SCL_2);
  
  configureMPU(&MPU_1);
  configureMPU(&MPU_2);
  delay(200);
  #endif 
  #ifdef ENCODER
  // If the encoder requires setup add it here
  #endif
}

void loop() {
  delay(100);



}



#ifdef MPU
void configureMPU(MPU6500_WE *mpu){
  mpu->init();
  /* The slope of the curve of acceleration vs measured values fits quite well to the theoretical 
   * values, e.g. 16384 units/g in the +/- 2g range. But the starting point, if you position the 
   * MPU6500 flat, is not necessarily 0g/0g/1g for x/y/z. The autoOffset function measures offset 
   * values. It assumes your MPU6500 is positioned flat with its x,y-plane. The more you deviate 
   * from this, the less accurate will be your results.
   * The function also measures the offset of the gyroscope data. The gyroscope offset does not   
   * depend on the positioning.
   * This function needs to be called at the beginning since it can overwrite your settings!
   */
  Serial.println("Position you MPU6500 flat and don't move it - calibrating...");
  delay(1000);
  mpu->autoOffsets();
  Serial.println("Done!");
  
  /*  This is a more accurate method for calibration. You have to determine the minimum and maximum 
   *  raw acceleration values of the axes determined in the range +/- 2 g. 
   *  You call the function as follows: setAccOffsets(xMin,xMax,yMin,yMax,zMin,zMax);
   *  Use either autoOffset or setAccOffsets, not both.
   */
  //myMPU6500.setAccOffsets(-14240.0, 18220.0, -17280.0, 15590.0, -20930.0, 12080.0);

  /*  The gyroscope data is not zero, even if you don't move the MPU6500. 
   *  To start at zero, you can apply offset values. These are the gyroscope raw values you obtain
   *  using the +/- 250 degrees/s range. 
   *  Use either autoOffset or setGyrOffsets, not both.
   */
  //myMPU6500.setGyrOffsets(45.0, 145.0, -105.0);

  /*  You can enable or disable the digital low pass filter (DLPF). If you disable the DLPF, you 
   *  need to select the bandwdith, which can be either 8800 or 3600 Hz. 8800 Hz has a shorter delay,
   *  but higher noise level. If DLPF is disabled, the output rate is 32 kHz.
   *  MPU6500_BW_WO_DLPF_3600 
   *  MPU6500_BW_WO_DLPF_8800
   */
  mpu->enableGyrDLPF();
  //myMPU6500.disableGyrDLPF(MPU6500_BW_WO_DLPF_8800); // bandwdith without DLPF
  
  /*  Digital Low Pass Filter for the gyroscope must be enabled to choose the level. 
   *  MPU6500_DPLF_0, MPU6500_DPLF_2, ...... MPU6500_DPLF_7 
   *  
   *  DLPF    Bandwidth [Hz]   Delay [ms]   Output Rate [kHz]
   *    0         250            0.97             8
   *    1         184            2.9              1
   *    2          92            3.9              1
   *    3          41            5.9              1
   *    4          20            9.9              1
   *    5          10           17.85             1
   *    6           5           33.48             1
   *    7        3600            0.17             8
   *    
   *    You achieve lowest noise using level 6  
   */
  mpu->setGyrDLPF(MPU6500_DLPF_6);

  /*  Sample rate divider divides the output rate of the gyroscope and accelerometer.
   *  Sample rate = Internal sample rate / (1 + divider) 
   *  It can only be applied if the corresponding DLPF is enabled and 0<DLPF<7!
   *  Divider is a number 0...255
   */
  mpu->setSampleRateDivider(5);

  /*  MPU6500_GYRO_RANGE_250       250 degrees per second (default)
   *  MPU6500_GYRO_RANGE_500       500 degrees per second
   *  MPU6500_GYRO_RANGE_1000     1000 degrees per second
   *  MPU6500_GYRO_RANGE_2000     2000 degrees per second
   */
  mpu->setGyrRange(MPU6500_GYRO_RANGE_250);

  /*  MPU6500_ACC_RANGE_2G      2 g   (default)
   *  MPU6500_ACC_RANGE_4G      4 g
   *  MPU6500_ACC_RANGE_8G      8 g   
   *  MPU6500_ACC_RANGE_16G    16 g
   */
  mpu->setAccRange(MPU6500_ACC_RANGE_8G);

  /*  Enable/disable the digital low pass filter for the accelerometer 
   *  If disabled the bandwidth is 1.13 kHz, delay is 0.75 ms, output rate is 4 kHz
   */
  mpu->enableAccDLPF(true);

  /*  Digital low pass filter (DLPF) for the accelerometer, if enabled 
   *  MPU6500_DPLF_0, MPU6500_DPLF_2, ...... MPU6500_DPLF_7 
   *   DLPF     Bandwidth [Hz]      Delay [ms]    Output rate [kHz]
   *     0           460               1.94           1
   *     1           184               5.80           1
   *     2            92               7.80           1
   *     3            41              11.80           1
   *     4            20              19.80           1
   *     5            10              35.70           1
   *     6             5              66.96           1
   *     7           460               1.94           1
   */
  mpu->setAccDLPF(MPU6500_DLPF_6);

  /* You can enable or disable the axes for gyroscope and/or accelerometer measurements.
   * By default all axes are enabled. Parameters are:  
   * MPU6500_ENABLE_XYZ  //all axes are enabled (default)
   * MPU6500_ENABLE_XY0  // X, Y enabled, Z disabled
   * MPU6500_ENABLE_X0Z   
   * MPU6500_ENABLE_X00
   * MPU6500_ENABLE_0YZ
   * MPU6500_ENABLE_0Y0
   * MPU6500_ENABLE_00Z
   * MPU6500_ENABLE_000  // all axes disabled
   */
  //myMPU6500.enableAccAxes(MPU6500_ENABLE_XYZ);
  //myMPU6500.enableGyrAxes(MPU6500_ENABLE_XYZ);
}
#endif

bool clientConnect() {
	if (!client.connect(host, port)) {
	
		Serial.println("Connection to host failed");
		return false;
	}

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

  Serial.print("Init wifi currently using core: ");
  Serial.println(xPortGetCoreID());

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

void wifi_send_data() {
	char temp[] = "HELLO THERE";
	// uint8_t *tempBuf; (uint8_t *)temp;
	memcpy(buf, temp, sizeof(temp));


	client.write(buf, sizeof(buf));
}

void wifiTask(void *parameter) {
	while (true) {
		if (WiFi.status() == WL_CONNECTED)
			if (client.connected())
				wifi_send_data();
			else {
				WiFi.disconnect();
				clientConnect();
			}
		else {
			
		}
		delay(100);
	}
}

