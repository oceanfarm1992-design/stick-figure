import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

# Verify RTX 3050 recognition
if not torch.cuda.is_available():
    raise RuntimeError("CUDA is not available. Ensure NVIDIA drivers are active.")

print(f"Target GPU Detected: {torch.cuda.get_device_name(0)}")

# Load SD 1.5 in FP16 precision
model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(
    model_id, 
    torch_dtype=torch.float16,
    use_safetensors=True
)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.to("cuda")

# RTX 3050 VRAM Optimizations
pipe.enable_attention_slicing()  # Acceleration for Ampere GPUs
pipe.enable_attention_slicing()                     # Reduces VRAM spikes

def generate_character(prompt: str, output_path: str = "character.png"):
    negative_prompt = "deformed, ugly, bad anatomy, low quality, blurry, extra arms"
    
    print(f"Generating character...")
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=20,
        guidance_scale=7.5,
        height=512,
        width=512
    ).images[0]
    
    image.save(output_path)
    print(f"Character successfully saved to {output_path}")

if __name__ == "__main__":
    prompt = (
        "full body character design of a cute robot mascot, "
        "3d animated movie style, smooth render, isolated studio lighting"
    )
    generate_character(prompt, "robot_character.png")
