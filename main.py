import modal
import subprocess
import time
import os

BUILDKITE_COMMIT = os.getenv("BUILDKITE_COMMIT")
BUILDKITE_COMMIT = "bfd610430c04d2962a03a2db304fb13b09b4f1b3" # todo: remove this override
BASE_IMG = f"public.ecr.aws/q9t5s3a7/vllm-ci-postmerge-repo:{BUILDKITE_COMMIT}"

app = modal.App("buildkite-agent")
hf_cache = modal.Volume.from_name("vllm-benchmark-hf-cache", create_if_missing=True)

image = (
    modal.Image.from_registry(BASE_IMG, add_python="3.12")
    .workdir("/vllm-workspace")
    .apt_install(["apt-transport-https", "dirmngr", "curl", "gpg"])
    .run_commands([
        "curl -fsSL https://keys.openpgp.org/vks/v1/by-fingerprint/32A37959C2FA5C3C99EFBC32A79206696452D198 | gpg --dearmor -o /usr/share/keyrings/buildkite-agent-archive-keyring.gpg",
        "echo \"deb [signed-by=/usr/share/keyrings/buildkite-agent-archive-keyring.gpg] https://apt.buildkite.com/buildkite-agent stable main\" | tee /etc/apt/sources.list.d/buildkite-agent.list",
        "apt-get update",
    ])
    .apt_install(["buildkite-agent"])
)

@app.function(
    image=image,
    gpu="a100",
    timeout=60*60, # One hour max timeout
    secrets=[modal.Secret.from_name("buildkite-agent")],
    volumes={"/root/.cache/huggingface": hf_cache},
)
def a100_agent(script: str = ""):
    """
    GPU agent that runs the actual job
    """
    print("Would run script", script)
    subprocess.run(["env"])

@app.local_entrypoint()
def main(queue = "A100"):
    if queue == "A100":
        print(f"Starting GPU for queue {queue}")
        a100_agent.remote()
    else:
        print(f"Unsupported queue {queue}")