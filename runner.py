import modal
import subprocess
import os
import sys

# Env vars used for constructing modal image
BUILDKITE_COMMIT = os.getenv("BUILDKITE_COMMIT")
BUILDKITE_COMMIT = "bfd610430c04d2962a03a2db304fb13b09b4f1b3" # todo: remove this override
GPU = os.getenv("GPU")

# Local env vars from buildkite job that we'll want to drill through to GPU container
PASSTHROUGH_ENV_VARS = {
    "BUILDKITE_COMMIT": BUILDKITE_COMMIT,
    "HF_TOKEN": os.getenv("HF_TOKEN"),
    "VLLM_USAGE_SOURCE": os.getenv("VLLM_USAGE_SOURCE"),
}

# Modal app and associated volumes
app = modal.App("buildkite-runner")
hf_cache = modal.Volume.from_name("vllm-benchmark-hf-cache", create_if_missing=True)

# Image to use for runner
BASE_IMG = f"public.ecr.aws/q9t5s3a7/vllm-ci-postmerge-repo:{BUILDKITE_COMMIT}"
image = (
    modal.Image.from_registry(BASE_IMG, add_python="3.12")
    .workdir("/vllm-workspace/vllm")
    .run_commands("VLLM_USE_PRECOMPILED=1 pip install -e .")
    .workdir("/vllm-workspace")
)

# Remote function to run in the container
@app.function(
    image=image,
    gpu=GPU, # GPU can be "A100", "A10G", "H100", "T4"
    timeout=60*60, # One hour max timeout
    volumes={"/root/.cache/huggingface": hf_cache},
)
def runner(env: dict, cmd: str = ""):
    # Set passthrough environment variables in remote container
    for k, v in env.items():
        os.environ[k] = v

    # Debug Python environment
    print("\n=== Python Environment Info ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Path: {sys.path}")
    
    # List all installed packages
    print("\n=== Installed Packages ===")
    subprocess.run(["pip", "list"])
    
    # Try to get vllm package info specifically
    print("\n=== VLLM Package Info ===")
    subprocess.run(["pip", "show", "vllm"])
    
    # Show current working directory and its contents
    print("\n=== Working Directory Info ===")
    print(f"Current Directory: {os.getcwd()}")
    subprocess.run(["ls", "-la"])

    # TODO: remove this cmd override
    cmd = "python3 -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3.1-8B-Instruct"
    
    # Execute the original command
    print("\n=== Executing Command ===")
    print(f"Command: {cmd}")

    
    # Execite command
    subprocess.run(cmd.split(" "))

@app.local_entrypoint()
def main(command: str = ""):
    print("Modal client started:")
    print(f"\t- Commit:  {BUILDKITE_COMMIT}")
    print(f"\t- GPU:     {GPU}")
    print(f"\t- Command: {command}")
    runner.remote(env=PASSTHROUGH_ENV_VARS, cmd=command)