#!/usr/bin/env bash

set -euo pipefail

# Source shared functions
source "$(dirname "$0")/devcontainer-functions.sh"

sudo apt-get install -y help2man
pip install -r requirements-dev.txt

log_info "Project-specific setup complete"
