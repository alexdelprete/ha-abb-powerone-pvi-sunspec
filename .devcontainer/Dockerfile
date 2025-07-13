FROM mcr.microsoft.com/vscode/devcontainers/base:debian

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies needed for Home Assistant development
RUN \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        # Additional library needed by some tests and accordingly by VScode Tests Discovery
        bluez \
        ffmpeg \
        libudev-dev \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libgammu-dev \
        libswscale-dev \
        libswresample-dev \
        libavfilter-dev \
        libpcap-dev \
        libturbojpeg0 \
        libyaml-dev \
        libxml2 \
        git \
        cmake \
        autoconf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add go2rtc binary for streaming support
COPY --from=ghcr.io/alexxit/go2rtc:latest /usr/local/bin/go2rtc /bin/go2rtc

WORKDIR /usr/src

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python 3.13.2 (matches current HA version)
RUN uv python install 3.13.2

# Switch to vscode user
USER vscode

# Create Python virtual environment
ENV VIRTUAL_ENV="/home/vscode/.local/ha-venv"
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /tmp

# Install Home Assistant and development dependencies
RUN uv pip install homeassistant

# Install testing dependencies for custom component development
RUN uv pip install \
    pytest \
    pytest-homeassistant-custom-component \
    pytest-cov \
    pytest-timeout \
    pytest-mock \
    pre-commit \
    ruff \
    mypy

# Install additional tools for integration development
RUN uv pip install \
    voluptuous \
    pydantic \
    aiohttp \
    async-timeout

WORKDIR /workspaces

# Set the default shell to bash instead of sh
ENV SHELL=/bin/bash