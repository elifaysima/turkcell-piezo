from __future__ import annotations
"""
Fake publisher:
- Sensör yokken MQTT'ye StepPacket basar
- Demo için spike pencereleri üretir

ÇALIŞTIRMA:
  python src/fake_publisher.py
"""

import time
import random
import paho.mqtt.client as mqtt

from common import StepPacket, encode_packet

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
TOPIC = "piyon/v1/steps"

SITE_ID = "DEMO_CORRIDOR_1"
MODULES = ["MOD_01", "MOD_02", "MOD_03"]

BASE_FLOW = 3
SPIKE_FLOW = 12
SPIKE_EVERY_S = 30
SPIKE_LEN_S = 5


def main():
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    t0 = int(time.time())
    print(f"[fake_publisher] publishing to {MQTT_HOST}:{MQTT_PORT} topic={TOPIC}")

    while True:
        ts = int(time.time())
        elapsed = ts - t0
        in_spike = (elapsed % SPIKE_EVERY_S) < SPIKE_LEN_S
        target = SPIKE_FLOW if in_spike else BASE_FLOW

        for mid in MODULES:
            # dir1/dir2 bölüşüm bias
            bias = 0.5 + 0.35 * random.uniform(-1, 1)
            total = max(0, int(random.gauss(target, 1.2)))
            d1 = int(round(total * bias))
            d2 = max(0, total - d1)

            pkt = StepPacket(
                site_id=SITE_ID,
                module_id=mid,
                ts=ts,
                window_s=1,
                steps_dir1=d1,
                steps_dir2=d2,
                vcap=None,
            )
            client.publish(TOPIC, encode_packet(pkt), qos=0, retain=False)

        time.sleep(1)


if __name__ == "__main__":
    main()
