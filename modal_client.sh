 pip install -U modal
    
# Create modal config file using secrets
cat << EOF > ~/.modal.toml
[default]
token_id = "$(buildkite-agent secret get modal_token_id)"
token_secret = "$(buildkite-agent secret get modal_token_secret)"
EOF

# Now run modal
modal run main.py