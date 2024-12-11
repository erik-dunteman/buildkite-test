import modal
import subprocess
import time
import os

BUILDKITE_COMMIT = os.getenv("BUILDKITE_COMMIT")
BUILDKITE_COMMIT = "bfd610430c04d2962a03a2db304fb13b09b4f1b3" # todo: remove this override
GPU = os.environ["GPU"]

BASE_IMG = f"public.ecr.aws/q9t5s3a7/vllm-ci-postmerge-repo:{BUILDKITE_COMMIT}"

app = modal.App("buildkite-agent")
hf_cache = modal.Volume.from_name("vllm-benchmark-hf-cache", create_if_missing=True)

image = (
    modal.Image.from_registry(BASE_IMG, add_python="3.12")
    .workdir("/vllm-workspace")
)


@app.function(
    image=image,
    gpu=GPU,
    timeout=60*60, # One hour max timeout
    secrets=[modal.Secret.from_name("buildkite-agent")],
    volumes={"/root/.cache/huggingface": hf_cache},
)
def runner(script: str = ""):
    """
    GPU agent that runs the actual job
    """
    print("Would run script", script)
    subprocess.run(["env"])

@app.local_entrypoint()
def main(script: str):
    print("Modal client started:")
    print(f"\t- Commit: {BUILDKITE_COMMIT}")
    print(f"\t- GPU: {GPU}")
    print(f"\t- Script: {script}")
    runner.remote(script)