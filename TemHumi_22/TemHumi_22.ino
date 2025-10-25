/*
 * LAB Name: Arduino DHT22 Humidity & Temperature Sensor
 * Author: Khaled Magdy
 * For More Info Visit: www.DeepBlueMbedded.com
*/
#include <DHT.h>
 
#define DHT22_PIN 7
#define DHTTYPE DHT22
 
DHT DHT22_Sensor(DHT22_PIN, DHTTYPE);
 
void setup() {
  Serial.begin(9600); 
  DHT22_Sensor.begin();
}
 
void loop() {
  float DHT22_Humidity = DHT22_Sensor.readHumidity(); 
  float DHT22_TempC = DHT22_Sensor.readTemperature(); // Read Temperature(°C)
  //float DHT22_TempF = DHT22_Sensor.readTemperature(true);// Read Temperature(°F)
  
  //Serial.print("Humidity: "); 
  Serial.print(DHT22_Humidity);
  Serial.print(" , ");
  //Serial.print("Temperature: "); 
  Serial.println(DHT22_TempC);
  //Serial.print(" , ");
  //Serial.print(DHT22_TempF);
  //Serial.println(" °F");
 
  //delay(600000); // 60 sec.
  delay(5000); 
}
