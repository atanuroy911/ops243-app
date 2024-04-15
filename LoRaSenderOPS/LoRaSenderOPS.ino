#include <SPI.h>
#include <LoRa.h>

#define SENDER_NODE_ID 1 // Sender Node ID
#define RECEIVER_NODE_ID 2 // Receiver Node ID
#define BAND 433E6 // LoRa frequency

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("LoRa Sender");

  // LoRa module pins configuration
  LoRa.setPins(5, 14, 2); // NSS (CS), RST (Reset), DIO0

  if (!LoRa.begin(BAND)) {
    Serial.println("LoRa initialization failed. Check your connections.");
    while (true);
  }
}

void loop() {
  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    sendMessage(message);
  }
}

void sendMessage(String message) {
  LoRa.beginPacket();
  LoRa.print(message);
  LoRa.endPacket();
}
