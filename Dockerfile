FROM fedora:latest

RUN dnf install -y \
    curl \
    unzip \
    python3 \
    python3-pip \
    nodejs \
    npm \
    git \
    jq \
    && dnf clean all

RUN npm install -g @google/gemini-cli
RUN curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
ENV NODE_PATH="/usr/local/lib/node_modules"

RUN useradd -u 1000 -m gemini
USER gemini
WORKDIR /home/gemini/workspace