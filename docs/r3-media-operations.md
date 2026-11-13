# Andy Write R3 ImageGen operations

Use authorized US Mac mini and current GPT-6.1 Terra Codex login. No API Key needed for the built-in ImageGen tool. Never restart Chrome, DC Workers, or live WordPress.

## Commands from repo root

    python3 -m andy_write media-plan --job examples/jobs/pairdoll-unboxing.json --draft .runs/pairdoll-unboxing/article-auto-final.md
    python3 -m andy_write media-generate --job examples/jobs/pairdoll-unboxing.json
    python3 -m andy_write media-import --job examples/jobs/pairdoll-unboxing.json
    python3 -m andy_write media-export --job examples/jobs/pairdoll-unboxing.json

The media-generate command calls the Codex built-in ImageGen tool for missing assets and requires separate generated raster photos for cover and each H2. No SVG or code-generated substitutes are accepted. Images with existing files but lacking visual observations are NOT overwritten automatically.

Actual PNG originals stay in Git-ignored .runs on the Mac. WebP review copies and the Markdown article preview may be committed to this private repo, not production WordPress.

## Safeguards

All generated images must exist as real files, fit expected dimensions, and have SHA-256 checksums. Machine vision observations must report matching scene, actual observed objects, and zero issues. The Title, Alt, Caption and Description text must be based on the image and be unique across assets. WordPress upload is forbidden until Owner human approval.

The articles use illustrations, not evidence of real customer orders or authentic PairDoll packaging. Captions say AI-generated illustration.

## Limitations

Codex input/output Token metrics do not state the actual separate image-tool cost or the remaining 5-hour Plus allocation. R3 test ran 7 real generations, but repeated jobs should be monitored and obey quota and failure limits.

A source page returning HTTP 200 does not prove its content claims. Human article and product fact review is still required.
