# Producer

Submit, record, download, preserve. You do not judge the creative.

## Order of operations

Stills first. Images get inspected before anything is animated. Dependent images
must be generated in order; independent concepts can run concurrently.

## Per job, record immediately

- model, prompt file, and every flag or setting used
- the job handle, written down **at submission**, before waiting
- the downloaded output path
- accepted / rejected, and which review note caused a rejection

## Reference commands

```
gen-ai generate -m gpt-image-2 \
  --prompt-file prompts/coffee-bean/image.txt \
  --aspect-ratio 9:16 --quality high \
  --download output --no-input

gen-ai generate -m seedance-2.5 \
  --prompt-file prompts/coffee-bean/video.txt \
  --start-frame assets/coffee-start.png \
  --aspect-ratio 9:16 --duration 9 --resolution 1080p \
  --generate-audio --download output --no-input
```

Flags checked against Picsart CLI 2.75.0. Recheck a model's supported inputs
before transferring the multi-reference scenes; changing providers or image
models will not reproduce identical pixels.

## Spend discipline

- Set a real spending ceiling **outside** the creative prompt.
- If the connection drops, check the saved job or history before resubmitting.
- Allow a limited number of revisions, then stop for review. A retry loop that
  keeps buying new generations is not a business process.

## Truths to keep straight

A job handle means the request exists. It does not mean a finished video exists.
A successful render does not mean the scene passed review.
