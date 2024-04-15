#include <SPI.h>
#include <LoRa.h>

#define RECEIVER_NODE_ID 2 // Receiver Node ID
#define BAND 433E6 // LoRa frequency
#define LED_BUILTIN 13 // Pin connected to the LED
#define LED_PIN 6 // Pin connected to the LED


void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  while (!Serial);

  Serial.println("LoRa Receiver");

  // LoRa module pins configuration
  LoRa.setPins(10, 9, 2); // NSS (CS), RST (Reset), DIO0

  // Set LED pin as output
  pinMode(LED_PIN, OUTPUT);

  if (!LoRa.begin(BAND)) {
    Serial.println("LoRa initialization failed. Check your connections.");
    while (true);
  }
}

void loop() {
  if (LoRa.parsePacket()) {
    String packet = LoRa.readStringUntil('\n');
    processMessage(packet);
  }
}

void processMessage(String packet) {
  packet.remove(packet.length()-1);
  // Split the packet into individual fields
  int separatorIndex1 = packet.indexOf(',');
  int separatorIndex2 = packet.lastIndexOf(',');

  String time = packet.substring(8, separatorIndex1);
  String unit = packet.substring(separatorIndex1 + 9, separatorIndex2);
  String data = packet.substring(separatorIndex2 + 10);

  if (data.charAt(0) == '"') {
//    Serial.print("*************************");
    data.remove(0, 1);
  }
  if (data.charAt(data.length() - 1) == '"') {
    data.remove(data.length() - 1);
  }

//    Serial.println(data);

  
  // Check if unit is "kmph" and speed is less than 0
  if (data.toFloat() < 0) {
//     Blink the LED
    Serial.print("--------------------------------------------------------");
    digitalWrite(LED_BUILTIN, HIGH); // Turn on the LED
    digitalWrite(LED_PIN, HIGH); // Turn on the LED

    delay(500); // Wait for 500 milliseconds
    digitalWrite(LED_BUILTIN, LOW); // Turn off the LED
    digitalWrite(LED_PIN, LOW); // Turn on the LED

    delay(500); // Wait for 500 milliseconds 
  }

  
  // Print the received data
  Serial.print("Time -->  ");
  Serial.print(time);
  Serial.print(", Unit --> ");
  Serial.print(unit);
  Serial.print(", Data --> ");
  Serial.println(data.toFloat());

  
}
