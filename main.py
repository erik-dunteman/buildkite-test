import modal
import subprocess
import time
import os

app = modal.App("buildkite-agent")

image = (
    modal.Image.debian_slim()
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
    secrets=[modal.Secret.from_name("buildkite-agent")]
)
def a100_agent():
    """
    GPU agent that runs the actual job
    """
    subprocess.run([
        "buildkite-agent", 
        "start",
        "--token", os.environ["AGENT_TOKEN"],
        "--disconnect-after-job",  # Agent will stop after completing one job
        "--tags", "queue=A100",  # Tag this agent for this specific job
    ])

@app.local_entrypoint()
def main(queue = "A100"):
    match queue:
        case "A100":
            print(f"Starting GPU for queue {queue}")
            a100_agent.remote()
        case _:
            print(f"Unsupported queue {queue}")