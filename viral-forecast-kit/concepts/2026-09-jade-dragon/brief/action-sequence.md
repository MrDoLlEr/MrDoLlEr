# Scene 2 — jade dragon extrusion

**Deliverable:** one vertical 9:16 clip, 7 seconds, 1080p, fixed camera, with
generated audio, no music, no voice.

## Mechanism preserved from the reference

`recognisable creature already at the nozzle → body follows → limbs land → tail last → free`

The reference's whole point: the seal's **face is visible at the nozzle in frame
one**. The animal does not form from a pile. Whatever emerges must be
recognisable the entire time.

| Beat | What must be visible |
| --- | --- |
| frame 1 | the dragon's **head** already protrudes one nozzle-diameter: black eyes, snout, two horn nubs. Neck and body still inside the tube |
| 0.0–1.5s | hand compresses the tube; head moves out and down; neck and shoulders squeeze through **behind** the head |
| 1.5–3.5s | more body emerges head-first; forelegs unfold as shoulders clear; forefeet reach the tabletop; it wriggles and pulls itself forward |
| 3.5–5.0s | hindquarters and folded wings pass out; hind feet settle; the **tapered tail is last** to slip free |
| 5.0–7.0s | fully out, it takes one tiny step and blinks toward camera; the empty nozzle lifts slightly away |

## Must not happen

- a pile or blob of gel that later becomes an animal
- a coiled strand or puddle transforming
- the torso emerging from anything other than the nozzle
- a second dragon
- extra paste anywhere on the tabletop
- teleportation or a cut — one continuous body, continuous contact

## Failed first attempt, recorded on purpose

The original instruction was *"extrude a pile of gel, then turn it into a
dragon."* The model did exactly that — and missed the only interesting part of
the reference. The correction is the head-first opening frame.

## Reference strategy: three stills, in order

| Still | Controls | Why it must come first |
| --- | --- | --- |
| `image-1-macro-setup.txt` | hand, silver tube, nozzle, charcoal tile, camera angle, light, empty landing area | establishes the whole physical setup with no creature yet |
| `image-2-creature-design.txt` | the finished dragon's face, material and silhouette | "use the supplied dragon" only works once a dragon has been supplied |
| `image-3-opening-frame.txt` | the actual first frame: head out, body in | the video's start frame |

Dependency is strict: 2 is generated **from** 1, and 3 **from** 2. They cannot
run in parallel.

## Video inputs

- start frame: the approved `images/dragon-start.png` (still 3)
- additional reference: the approved `images/dragon-design.png` (still 2)
- the motion prompt explicitly tells the model to **ignore the extra gel bead**
  that sits above the creature in the design reference

## Scale and material lock

One 6-centimeter dragon, translucent jade-green gel, luminous glass-like edges,
softly elastic — **not** faceted crystal, not a rigid figurine. Unbranded
brushed silver tube. Matte charcoal tabletop. 85 mm macro, shallow
three-quarter angle, fixed throughout.
