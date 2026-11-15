# CR Touch cable: SKR Mini E3 V3 (one 5-pin) → SKR 3 EZ (3-pin + 2-pin)

**Pictorial version:** `docs/cr-touch-repin.html` (open in a browser) or
`docs/cr-touch-repin.pdf` (print). It draws each crimp from its pin on the
Mini E3's Z-PROBE header to its pin on the SKR 3 EZ, over BTT's own
board images.

The Sprite's CR Touch cable ends in one 5-pin JST-XH that went into the
Mini E3's **Z-PROBE** header. The SKR 3 EZ splits the same five signals
over two headers, **SERVOS** (3-pin) and **Probe** (2-pin). Nothing is
re-crimped: lift the retaining tab on the 5-pin housing with a pin, slide
the crimps out, and push them into a 3-pin and a 2-pin JST-XH housing in
the order below. All five wires are black, so position is the only
reference; the meter check at the end tells you which end is pin 1.

## Pin map

Pin numbers on the Mini E3 side count from the **top** of its Z-PROBE
header, the end nearest the Neopixel header and the board's top (motor)
edge; pin 5 is nearest the bottom edge with the Z-STOP and thermistor
headers. Pin numbers on the SKR 3 EZ side count left to right with the
board held drivers-up, as BTT's pin diagram prints them.

| Mini E3 V3 Z-PROBE pin | Signal | Function | → SKR 3 EZ header · pin | Klipper |
|---|---|---|---|---|
| 1 (top) | PC14 | probe trigger signal | **Probe** · pin 2 (PC13) | `sensor_pin: ^PC13` |
| 2 | GND | probe ground | **Probe** · pin 1 (GND) | |
| 3 | PA1 | servo / deploy control | **SERVOS** · pin 3 (PE5) | `control_pin: PE5` |
| 4 | PWR | +5 V | **SERVOS** · pin 2 (+5V) | |
| 5 (bottom) | GND | servo ground | **SERVOS** · pin 1 (GND) | |

Read as two housings:

```
SKR 3 EZ  SERVOS (3-pin):   GND · +5V · PE5      ←  Mini E3 pins  5 · 4 · 3
SKR 3 EZ  Probe  (2-pin):   GND · PC13           ←  Mini E3 pins  2 · 1
```

So the old connector is split between pins 2 and 3, and both new housings
are the old order **reversed**: the old pin 5 becomes SERVOS pin 1, the old
pin 2 becomes Probe pin 1.

## Which end of the black cable is pin 1

The two GND wires are joined inside the CR Touch. With the cable still
plugged into the probe, set a meter to continuity and find the pair of
crimps that beep together: they are pins 2 and 5. The one of them that sits
at the **end** of the housing is pin 5 (servo GND); the other end of the
housing is then pin 1 (signal). If the beeping pair sits at positions 1 and
4 counted from the end you started at, you started at pin 5: count from
the other end.

A second check after re-pinning, before power: continuity from SERVOS
pin 1 to Probe pin 1 (both GND), and none between SERVOS pin 2 and either
GND.

## After it is plugged in

`QUERY_PROBE` in the console should say `open`; `BLTOUCH_DEBUG
COMMAND=pin_down` drops the pin, `pin_up` lifts it, and `QUERY_PROBE`
reads `TRIGGERED` while a finger holds the pin up. A probe that reads
TRIGGERED all the time with nothing touching it, or a pin that never
moves, means the two housings are swapped end for end: pull them and
reverse both.

Sources: BTT's [SKR Mini E3 V3.0 pin diagram](https://github.com/bigtreetech/BIGTREETECH-SKR-mini-E3/blob/master/hardware/BTT%20SKR%20MINI%20E3%20V3.0/Hardware/BTT%20E3%20SKR%20MINI%20V3.0_PIN.pdf)
(Z-PROBE: PC14, GND, PA1, PWR, GND) and [SKR 3 EZ V1.0 pin diagram](https://github.com/bigtreetech/SKR-3/blob/master/Hardware%20(SKR%203%20EZ)/BIGTREETECH%20SKR%203%20EZ%20V1.0-PIN.pdf)
(SERVOS: GND, +5V, PE5; Probe: GND, PC13).
