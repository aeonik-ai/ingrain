# Visual Demo

The launch visual should make the loop obvious in five seconds:

```text
agent run -> ledger -> promotions -> practice -> hydration -> better next run
```

Use [assets/ingrain-flow-animated.svg](../assets/ingrain-flow-animated.svg) as the first version. It is a self-contained SVG with CSS animation, no build step, no hosted backend, and no JavaScript.

## What The Animation Shows

1. A runner agent does real work.
2. Ingrain records source-linked ledger events.
3. Durable corrections, decisions, lessons, and outcomes are promoted.
4. The compiler writes practice artifacts.
5. Hydration injects compact background experience.
6. The next run behaves differently.

The key frame is the bottom line:

> Logs are what happened. Learned experience is what should change next time.

## Where To Use It

| Surface | Use |
|---|---|
| README | Link it as an optional visual asset. Keep the static architecture diagram as the main image because GitHub can be inconsistent about animated SVG playback. |
| X / Twitter | Export to MP4/GIF from a browser or screen recording. |
| LinkedIn | Use a still frame or MP4 export. |
| YouTube | Use it as the intro bumper before the terminal demo. |
| Website | Embed the SVG directly so the animation runs without a video player. |

## Export Options

Lowest overhead:

1. Open `assets/ingrain-flow-animated.svg` in a browser.
2. Record a 6-8 second loop.
3. Export as MP4 for social posts.

Optional Remotion path:

1. Keep the exact same story beats and labels.
2. Rebuild the nodes as React components.
3. Animate one packet around the loop.
4. Export square, 16:9, and vertical crops.

Do not add Remotion to this repo unless we are actively producing launch videos. The SVG is the source-of-truth visual for v0.
