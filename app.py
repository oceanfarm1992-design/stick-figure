import os
import uuid

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from flask import Flask, jsonify, render_template, request, send_from_directory

MODEL_ID = "runwayml/stable-diffusion-v1-5"
OUTPUT_DIR = os.path.join("static", "generated")

app = Flask(__name__)
os.makedirs(OUTPUT_DIR, exist_ok=True)

_pipe = None


def get_pipeline():
    global _pipe
    if _pipe is None:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA-compatible GPU was not detected.")

        print(f"Active GPU: {torch.cuda.get_device_name(0)}")
        pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            use_safetensors=True,
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe.to("cuda")
        pipe.enable_attention_slicing()
        _pipe = pipe
    return _pipe


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    negative_prompt = data.get("negative_prompt") or (
        "deformed, ugly, bad anatomy, low quality, blurry, extra limbs, cropped"
    )
    steps = int(data.get("steps", 20))
    guidance_scale = float(data.get("guidance_scale", 7.5))

    try:
        pipe = get_pipeline()
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            height=512,
            width=512,
        ).images[0]
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    filename = f"{uuid.uuid4().hex}.png"
    image.save(os.path.join(OUTPUT_DIR, filename))

    return jsonify({"image_url": f"/static/generated/{filename}"})


@app.route("/static/generated/<path:filename>")
def generated_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
