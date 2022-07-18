#include "Arduino.h"
#include <WiFiManager.h>

// GLOBAL ENABLES
// Select which sensors / functionalities are enabled
// #define LOAD_CELLS
// #define MPU
// #define ENCODER
#define WIFI
// #define LOAD_CELL_CALIBRATION_1
// #define LOAD_CELL_CALIBRATION_2
#define TESTING



#ifdef MPU
#include <MPU6500_WE.h>
#include <Wire.h>
#define MPU6500_ADDR 0x68
#define SDA_1 19
#define SCL_1 18
#define SDA_2 26
#define SCL_2 25
// The ESP32 supports 2 i2c at the same time these are defined here
TwoWire I2Cone = TwoWire(0); TwoWire I2Ctwo = TwoWire(1);
MPU6500_WE MPU_1 = MPU6500_WE(&I2Cone, MPU6500_ADDR);
MPU6500_WE MPU_2 = MPU6500_WE(&I2Ctwo, MPU6500_ADDR);
void configureMPU(MPU6500_WE *mpu);
#define MPU_DIVISOR 16384
#endif

#ifdef LOAD_CELLS
#include <HX711_ADC.h>
// Load cell amplifier pin numbers
#define LOAD_DOUT_1 21
#define LOAD_SCK_1 22
#define LOAD_DOUT_2 14
#define LOAD_SCK_2 27
//HX711 constructor (dout pin, sck pin)
HX711_ADC LoadCell_1(LOAD_DOUT_1, LOAD_SCK_1);
HX711_ADC LoadCell_2(LOAD_DOUT_2, LOAD_SCK_2);
#endif

#if defined(LOAD_CELL_CALIBRATION_1) || defined(LOAD_CELL_CALIBRATION_2)
void calibrate(HX711_ADC &LoadCell);
#endif

#ifdef ENCODER
#include <ESP32Encoder.h>
#include <InterruptEncoder.h>
//Encoder pins
#define PIN_A 13
#define PIN_B 15
ESP32Encoder encoder;
#endif



// Define tasks for separating the cores of the main functions
TaskHandle_t Task1;
TaskHandle_t Task2;

// The time object for looping without using delay
unsigned long t = 0;

struct gyroData {
  float x;
  float y;
  float z;
};

struct imuData {
  float x;
  float y;
  float z;
};

struct SensorData {
  int32_t timestamp;
  float loadCell[2];
  struct gyroData gyro[2];
  struct imuData imu[2];
  int32_t encoder;
};

// Flag for indicating when data can be sent over wifi
bool wifi_flag = false;


// Global buffer for storing and sending sensor data via WiFi
struct SensorData sensorData;

void getSensorData(void * pvParameters) {
  // Defines the target read interval - may not be possible as reading and printing takes clock cycles
  int32_t targetMilliseconds = 10; 
  int32_t initialT = millis();
  // Printing will be in the order of 
  // Time L1 L2 A1 G1 A2 G2 E1 A B
  // Will change if different sensors are enabled or disabled
  while(true){
    t = millis();
    // Serial.print(String((int32_t) (t - initialT)) + " ");


    #ifdef LOAD_CELLS
      // only get data if update sucessfully returns with 1 to only fetch valid data
      if (LoadCell_1.update()) {
        float l1 = LoadCell_1.getData(); //Serial.print(String(l1, 8) + " ");
        sensorData.loadCell[0] = l1;
      }
      if (LoadCell_2.update()) {
        float l2 = LoadCell_2.getData(); //Serial.print(String(l2, 8) + " ");
        sensorData.loadCell[1] = l2;
      }
    #endif

    #ifdef MPU
      xyzFloat acc_1 = MPU_1.getCorrectedAccRawValues();
      xyzFloat acc_2 = MPU_2.getCorrectedAccRawValues();
      xyzFloat gyr_1 = MPU_1.getGyrValues();
      xyzFloat gyr_2 = MPU_2.getGyrValues();

      sensorData.imu[0] = {.x = acc_1.x, .y = acc_1.y, .z = acc_1.z};
      sensorData.imu[1] = {.x = acc_2.x, .y = acc_2.y, .z = acc_2.z};
      sensorData.gyro[0] = {.x = gyr_1.x, .y = gyr_1.y, .z = gyr_1.z};
      sensorData.gyro[1] = {.x = gyr_2.x, .y = gyr_2.y, .z = gyr_2.z};

      // Serial.print(String(acc_1.x / MPU_DIVISOR, 8) + " " + String(acc_1.y / MPU_DIVISOR, 8) + " " + String(acc_1.z / MPU_DIVISOR, 8) + " ");
      // Serial.print(String(gyr_1.x, 8) + " " + String(gyr_1.y, 8) + " " + String(gyr_1.z, 8) + " ");
      // Serial.print(String(acc_2.x / MPU_DIVISOR, 8) + " " + String(acc_2.y / MPU_DIVISOR, 8) + " " + String(acc_2.z / MPU_DIVISOR, 8) + " ");
      // Serial.print(String(gyr_2.x, 8) + " " + String(gyr_2.y, 8) + " " + String(gyr_2.z, 8) + " ");
    #endif

    #ifdef ENCODER
      // Serial.print(String((int32_t)encoder.getCount()) + " " + String((int32_t)digitalRead(PIN_A)) + " " + String((int32_t)digitalRead(PIN_B)) + " ");
      sensorData.encoder = encoder.getCount();
    #endif

    #ifdef TESTING
      sensorData.imu[0] = {.x = 0.5, .y = 0.10, .z = 0.15};
      sensorData.imu[1] = {.x = 0.20, .y = 0.25, .z = 0.30};
      sensorData.gyro[0] = {.x = 0.35, .y = 0.40, .z = 0.45};
      sensorData.gyro[1] = {.x = 0.50, .y = 0.55, .z = 0.55};

      sensorData.loadCell[0] = 0.60;
      sensorData.loadCell[1] = 0.65;

      sensorData.encoder = 5;
    #endif

    sensorData.timestamp = t - initialT;

    // TODO: Aggregate N datapoints before sending across wifi

    wifi_flag = true;

    // Serial.println();
    // Adaptive wait to reach target delay if possible
    if ((millis() - t) < targetMilliseconds) delay(targetMilliseconds - (millis() - t) + 1);
  }
}

#define MAX_IP_LEN 15

// WiFi Configurations, TODO: Abstract out
char ssid[MAX_SSID_LEN] = "";
char password[MAX_PASSPHRASE_LEN] = "";

uint16_t port = 5000;
char host[MAX_IP_LEN] = "172.20.10.2";

#define TRIGGER_PIN 0

WiFiClient client;
WiFiManager wm;

void init_wifi();
void wifi_send_data();
bool clientConnect();
void wifiTask(void *parameter);


void setup() {

  // Connects to the serial output
  Serial.begin(115200); delay(10);
  
  #ifdef LOAD_CELLS
    LoadCell_1.begin(); LoadCell_2.begin();
    float calibrationValue_1 = (-15861.51-15822.44-15865.00-15947.65-15809.39)/5; // obtained from 5 samples of calibration of varying weight
    float calibrationValue_2 = 1.0; // calibrationValue_2 = LoadCell_2.getNewCalibration(-500);
    unsigned long stabilisingtime = 2000; // tare precision improved by adding some stabilising time
    boolean _tare = true; // set this to false if you don't want tare to be performed in the next step
    byte loadcell_1_rdy = 0;
    byte loadcell_2_rdy = 0;
    while ((loadcell_1_rdy + loadcell_2_rdy) < 2) { //run startup, stabilization and tare, both modules simultaniously
      if (!loadcell_1_rdy) loadcell_1_rdy = LoadCell_1.startMultiple(stabilisingtime, _tare);
      if (!loadcell_2_rdy) loadcell_2_rdy = LoadCell_2.startMultiple(stabilisingtime, _tare);
    }
    if (LoadCell_1.getTareTimeoutFlag()) Serial.println("Timeout, check MCU>HX711 no.1 wiring and pin designations");
    if (LoadCell_2.getTareTimeoutFlag()) Serial.println("Timeout, check MCU>HX711 no.2 wiring and pin designations");
    LoadCell_1.setCalFactor(calibrationValue_1); // user set calibration value (float)
    LoadCell_2.setCalFactor(calibrationValue_2); // user set calibration value (float)

    #ifdef LOAD_CELL_CALIBRATION_1
      Serial.println("CALIBRATION FOR LOAD CELL 1, PINS: [" + String(LOAD_DOUT_1) + ", " + String(LOAD_SCK_1) + "]");
      calibrate(LoadCell_1);
    #endif

    #ifdef LOAD_CELL_CALIBRATION_2
      Serial.println("CALIBRATION FOR LOAD CELL 2, PINS: [" + String(LOAD_DOUT_2) + ", " + String(LOAD_SCK_2) + "]");
      calibrate(LoadCell_2);
    #endif

    Serial.println("Loadcell startup is complete");
  #endif

  // Start up code for the load cells
  #ifdef MPU
    I2Cone.begin(SDA_1, SCL_1);
    I2Ctwo.begin(SDA_2, SCL_2);
    configureMPU(&MPU_1);
    configureMPU(&MPU_2);
  #endif 

  // Start up code for the encoder 
  #ifdef ENCODER
    ESP32Encoder::useInternalWeakPullResistors=NONE;
    encoder.attachFullQuad(PIN_A, PIN_B);
    encoder.clearCount();
    // Serial.println("Encoder Start = " + String((int32_t)encoder.getCount()));
  #endif

  #ifdef WIFI
    init_wifi();
    xTaskCreatePinnedToCore(wifiTask, "SumTask", 5000, NULL, 2, &Task2, 1); // Assign wifi tasks to Core 2
  #endif
  xTaskCreatePinnedToCore(getSensorData, "Task1", 5000, NULL, 1, &Task1,0); // Assign core tasks to Core 1

}

void loop() {
  while(true) sleep(100000);
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
  mpu->setSampleRateDivider(0);

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
  mpu->setAccRange(MPU6500_ACC_RANGE_2G);

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
  int err = client.connect(host, port);
  if (!err) {
	// if (!client.connect(host, port)) {
	
		Serial.print("Connection to host failed. Err: ");
    Serial.println(err);
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
  // WiFi.disconnect();
	// WiFi.begin(ssid, password);
  WiFi.reconnect();
}

void clientLost(WiFiEvent_t event, WiFiEventInfo_t info) {
	Serial.print("CLIENT LOST D:");
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

void wifi_send_data(uint8_t *buf, unsigned int size) {
  if (wifi_flag == false) return;

  memcpy(buf + size, (const void *)&sensorData, sizeof(sensorData));
  client.write(buf, sizeof(sensorData) + size);

  wifi_flag = false;
}

void wifiTask(void *parameter) {

  // initialise buffer to use for sending sensor data over via wifi
  char startBytes[] = "START";
  uint8_t buf[(sizeof(startBytes) + sizeof(sensorData))];
  memcpy(buf, startBytes, sizeof(startBytes) - 1);

  Serial.println(sizeof(startBytes) + sizeof(sensorData));
  int target_ms = 15, curr, t;

	while (true) {
    t = millis();
		if (WiFi.status() == WL_CONNECTED)
			if (client.connected())
				wifi_send_data(buf, sizeof(startBytes) - 1);
			else {
				WiFi.disconnect();
				// clientConnect();
			}
		else {
      // TODO: what we do if WiFi is nont connnnected?
		}
    curr = millis();
		if ((curr - t) < target_ms) delay(target_ms - (curr - t) + 1); 
	}
}

#if defined(LOAD_CELL_CALIBRATION_1) || defined(LOAD_CELL_CALIBRATION_2)
void calibrate(HX711_ADC &LoadCell) {
  Serial.println("***");
  Serial.println("Start calibration:");
  Serial.println("Place the load cell an a level stable surface.");
  Serial.println("Remove any load applied to the load cell.");
  Serial.println("Send 't' from serial monitor to set the tare offset.");

  boolean _resume = false;
  while (_resume == false) {
    LoadCell.update();
    if (Serial.available() > 0) {
      if (Serial.available() > 0) {
        char inByte = Serial.read();
        if (inByte == 't') LoadCell.tareNoDelay();
      }
    }
    if (LoadCell.getTareStatus() == true) {
      Serial.println("Tare complete");
      _resume = true;
    }
  }

  Serial.println("Now, place your known mass on the loadcell.");
  Serial.println("Then send the weight of this mass (i.e. 100.0) from serial monitor.");

  float known_mass = 0;
  _resume = false;
  while (_resume == false) {
    LoadCell.update();
    if (Serial.available() > 0) {
      known_mass = Serial.parseFloat();
      if (known_mass != 0) {
        Serial.print("Known mass is: ");
        Serial.println(known_mass);
        _resume = true;
      }
    }
  }

  LoadCell.refreshDataSet(); //refresh the dataset to be sure that the known mass is measured correct
  float newCalibrationValue = LoadCell.getNewCalibration(known_mass); //get the new calibration value

  Serial.print("New calibration value has been set to: ");
  Serial.print(newCalibrationValue);
  Serial.println(", use this as calibration value (calFactor) in your project sketch.");

  Serial.println("End calibration");
  Serial.println("***");
  Serial.println("To re-calibrate, send 'r' from serial monitor.");
  Serial.println("For manual edit of the calibration value, send 'c' from serial monitor.");
  Serial.println("***");
}
#endif