# Estate Service Catalog

## Image Generation

Service ID: `image.generation`

Capabilities:

- `image.generate`
- `image.workflow`

Providers:

- ComfyUI
- SDXL

Purpose:

Generate images using local ComfyUI and installed model assets.

Current status:

Available when ComfyUI paths and SDXL model directories exist.

Future work:

Actual workflow execution, prompt routing, output artifact management.

## Speech Transcription

Service ID: `speech.transcription`

Capabilities:

- `audio.transcribe`
- `speech.to_text`

Providers:

- Whisper

Purpose:

Transcribe audio files into text.

Future work:

Direct Alfred transcription execution.

## Speech Synthesis

Service ID: `speech.synthesis`

Capabilities:

- `text.to_speech`
- `voice.generate`

Providers:

- Kokoro
- F5-TTS

Purpose:

Generate speech from text.

Future work:

Voice selection, batch generation, artifact routing.

## Code Assistance

Service ID: `code.assistance`

Capabilities:

- `code.read`
- `code.write`
- `code.review`
- `debug`

Providers:

- Ollama
- qwen2.5-coder:7b

Purpose:

Support local code reading, repair planning, and implementation assistance.

Future work:

Safe patch generation and execution gates.

## Local Reasoning

Service ID: `reasoning.local_llm`

Capabilities:

- `reason`
- `summarize`
- `plan`

Providers:

- Ollama
- llama3.2:3b

Purpose:

Private local reasoning and lightweight planning.

Future work:

Direct local LLM invocation from Alfred executors.
