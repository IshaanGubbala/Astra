"""
Classifies BOM components into schematic node types and fetches product images.
Node types: MCU, SENSOR, ACTUATOR, POWER, MODULE, DISPLAY, MECHANICAL
"""
import logging
import re
import time

logger = logging.getLogger(__name__)

# Keyword → node type mapping (checked in order)
_TYPE_RULES: list[tuple[list[str], str]] = [
    (["display", "screen", "oled", "lcd", "tft", "st7789", "ssd1306", "epaper", "e-ink"], "DISPLAY"),
    (["arduino", "esp32", "esp8266", "raspberry pi", "pico", "stm32", "attiny", "atmega",
      "licheerv", "teensy", "nucleo", "mcu", "microcontroller", "nano", "uno", "mega",
      "zero", "feather", "bluepill"], "MCU"),
    (["sensor", "ultrasonic", "ir sensor", "pir", "temperature", "humidity", "pressure",
      "accelerometer", "gyroscope", "imu", "gps", "camera", "mic", "microphone",
      "photoresistor", "ldr", "lidar", "radar", "hall", "encoder", "potentiometer",
      "moisture", "gas", "ph sensor", "tof", "vl53", "mpu6050", "hc-sr04", "dht"], "SENSOR"),
    (["motor", "servo", "stepper", "solenoid", "relay", "pump", "fan", "led", "neopixel",
      "buzzer", "speaker", "vibration motor", "linear actuator", "driver", "h-bridge",
      "l298", "l293", "tb6612", "drv8833", "a4988", "tmc", "esc"], "ACTUATOR"),
    (["battery", "lipo", "nimh", "18650", "power bank", "solar panel", "supercapacitor",
      "buck", "boost", "regulator", "ldo", "voltage divider", "bms", "charger",
      "tp4056", "ups", "power supply", "usb-c power"], "POWER"),
    (["wifi", "bluetooth", "lora", "zigbee", "nrf24", "esp-01", "gsm", "gprs", "4g",
      "modem", "ethernet", "can bus", "rs485", "uart module", "level shifter",
      "multiplexer", "shift register", "dac", "adc module", "rtc", "sd card",
      "flash module", "eeprom", "rfid", "nfc"], "MODULE"),
    (["bolt", "nut", "screw", "standoff", "spacer", "washer", "bracket", "mount",
      "chassis", "frame", "enclosure", "box", "case", "track", "wheel", "gear",
      "sprocket", "axle", "bearing", "spring", "hinge", "rail", "rod", "shaft",
      "plate", "panel", "3d print", "acrylic", "aluminum", "pla", "abs", "arm assembly",
      "head assembly", "gripper", "claw", "joint"], "MECHANICAL"),
]

_COLOR_MAP = {
    "MCU": "#00bcd4",
    "SENSOR": "#ffc107",
    "ACTUATOR": "#ff7043",
    "POWER": "#ff9800",
    "MODULE": "#ce93d8",
    "DISPLAY": "#f48fb1",
    "MECHANICAL": "#78909c",
}

_EDGE_COLOR_MAP = {
    "DATA": "#4caf50",
    "POWER": "#ff9800",
    "GROUND": "#757575",
    "I2C": "#2196f3",
    "SPI": "#9c27b0",
    "UART": "#00bcd4",
    "PWM": "#ff7043",
}


def classify_component(component: str, description: str = "") -> str:
    text = f"{component} {description}".lower()
    for keywords, node_type in _TYPE_RULES:
        if any(kw in text for kw in keywords):
            return node_type
    return "MODULE"


def get_node_color(node_type: str) -> str:
    return _COLOR_MAP.get(node_type, "#78909c")


def get_edge_color(signal_type: str) -> str:
    signal_upper = signal_type.upper() if signal_type else "DATA"
    for key, color in _EDGE_COLOR_MAP.items():
        if key in signal_upper:
            return color
    return _EDGE_COLOR_MAP["DATA"]


def is_edge_dashed(signal_type: str) -> bool:
    """Power connections shown as dashed lines."""
    s = (signal_type or "").upper()
    return "POWER" in s or "VCC" in s or "SUPPLY" in s


def enrich_bom_with_classification(bom_items: list) -> list:
    """Add node_type and color to each BOM item."""
    result = []
    for item in bom_items:
        node_type = classify_component(
            item.get("component", ""),
            item.get("description", ""),
        )
        result.append({
            **item,
            "node_type": node_type,
            "node_color": get_node_color(node_type),
            "category": "Mechanical" if node_type == "MECHANICAL" else "Electrical",
        })
    return result


def fetch_component_images(bom_items: list) -> list:
    """Attempt to fetch a product image URL for each component."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo_search not installed — skipping image fetch")
        return bom_items

    enriched = []
    for item in bom_items:
        if item.get("node_type") == "MECHANICAL":
            enriched.append({**item, "image_url": None})
            continue

        query = f"{item.get('part_number') or item.get('component')} electronics component"
        image_url = None
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=3))
            for r in results:
                url = r.get("image", "")
                if url and url.startswith("http"):
                    image_url = url
                    break
            time.sleep(0.2)
        except Exception as e:
            logger.warning("Image fetch failed for %s: %s", item.get("component"), e)

        enriched.append({**item, "image_url": image_url})

    return enriched
