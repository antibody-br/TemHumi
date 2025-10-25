#include <DHT.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>

#define DHT_PIN 2
#define DHT_TYPE DHT22

// LCD pins
#define CLK_PIN   3
#define DIN_PIN   4  
#define DC_PIN    5
#define RST_PIN   6
#define CE_PIN    7
#define LIGHT_PIN 8

DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_PCD8544 display = Adafruit_PCD8544(CLK_PIN, DIN_PIN, DC_PIN, CE_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  dht.begin();
  
  pinMode(LIGHT_PIN, OUTPUT);
  digitalWrite(LIGHT_PIN, HIGH);
  
  display.begin();
  display.setContrast(50);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // Send to serial (for your Python script)
  Serial.print(humidity);
  Serial.print(" , ");
  Serial.println(temperature);
  
  // Display on LCD
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("TemHumi Monitor");
  display.setCursor(0, 12);
  display.print("T: ");
  display.print(temperature, 1);
  display.println(" C");
  display.setCursor(0, 22);
  display.print("H: ");
  display.print(humidity, 1);
  display.println(" %");
  display.setCursor(0, 32);
  display.println("Live Data");
  display.display();
  
  delay(2000);
}