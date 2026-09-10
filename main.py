import os
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

# --- GPU & MODEL SETUP ---
def load_pipeline():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA-compatible GPU was not detected.")

    print(f"Active GPU: {torch.cuda.get_device_name(0)}")
    model_id = "runwayml/stable-diffusion-v1-5"

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        use_safetensors=True
    )

    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")

    # 6GB VRAM Optimization
    pipe.enable_attention_slicing()

    return pipe

# --- ASSET GENERATOR ---
def generate_asset(pipe, prompt: str, output_path: str):
    negative_prompt = "deformed, ugly, bad anatomy, low quality, blurry, extra limbs, cropped"
    
    print(f"Generating: {output_path}...")
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=20,
        guidance_scale=7.5,
        height=512,
        width=512
    ).images[0]

    image.save(output_path)
    print(f"Saved: {output_path}")

# --- BATCH EXECUTION ---
def run_batch():
    output_dir = "rendered_assets"
    os.makedirs(output_dir, exist_ok=True)

    # Add your script prompts here
    batch_prompts = [
        ("3d animated robot mascot narrator, vibrant studio background", "robot_avatar.png"),
        ("3d cute animated owl mascot in a suit, high quality", "owl_avatar.png"),
    ]

    pipe = load_pipeline()

    print("\nStarting video asset batch...")
    for idx, (prompt, filename) in enumerate(batch_prompts, start=1):
        target_path = os.path.join(output_dir, filename)
        generate_asset(pipe, prompt, target_path)

    print("\nBatch execution complete! Assets saved in /rendered_assets")

if __name__ == "__main__":
    run_batch()