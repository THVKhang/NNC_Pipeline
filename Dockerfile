# NNC Pipeline with every tool it runs, at the versions CI uses (phase 22, docs/GUIDE.md "Docker").
#
#   docker build -t nnc-pipeline .
#   docker run --rm nnc-pipeline                      # nnc demo sync_fifo: no agent, no API key
#   docker run --rm nnc-pipeline nnc demo ot_gpio --formal
#   docker run --rm -it nnc-pipeline bash
#
# Build it from a clean clone (or `git archive HEAD | docker build -t nnc-pipeline -`): the image holds the
# committed files only. .dockerignore leaves out what git ignores (licensed standards, agent caches, logs).
FROM ubuntu:24.04

LABEL org.opencontainers.image.source="https://github.com/THVKhang/NNC_Pipeline" \
      org.opencontainers.image.description="NNC Pipeline: specification-driven RTL verification, with Verilator, Yosys, SymbiYosys and cocotb" \
      org.opencontainers.image.licenses="MIT"

# The same OSS CAD Suite release as CI (.github/workflows/ci.yml, OSS_CAD_SUITE) and its published SHA-256.
ARG OSS_CAD_SUITE=2026-11-07
ARG OSS_CAD_SUITE_SHA256=81f0f9a2fb6a4b720ea16d717dcdf031583bce224d73d2480e438207fd3c71f8
ARG COCOTB=2.1.0

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# make and g++ build the Verilator models; python3-dev links cocotb's embedded interpreter; poppler-utils
# reads PDF specifications (pdftotext); git fetches the corpus (nnc corpus).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git make g++ python3 python3-venv python3-dev poppler-utils \
 && rm -rf /var/lib/apt/lists/*

# The FPGA place-and-route tools, their chip databases and the waveform viewer are removed: the flow uses none.
RUN curl -fsSL -o /tmp/ocs.tgz \
      "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/${OSS_CAD_SUITE}/oss-cad-suite-linux-x64-$(echo ${OSS_CAD_SUITE} | tr -d -).tgz" \
 && echo "${OSS_CAD_SUITE_SHA256}  /tmp/ocs.tgz" | sha256sum -c - \
 && tar -xzf /tmp/ocs.tgz -C /opt \
 && rm /tmp/ocs.tgz \
 && cd /opt/oss-cad-suite \
 && rm -rf libexec/nextpnr-* share/nextpnr share/icebox share/trellis libexec/surfer

# The venv comes first on PATH so that `python3` is the one with cocotb and nnc; the OSS CAD Suite tools
# (verilator, yosys, sby, yices) come after it.
ENV PATH=/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/oss-cad-suite/bin

RUN useradd --create-home --shell /bin/bash nnc
WORKDIR /home/nnc/NNC_Pipeline
COPY --chown=nnc:nnc . .

# nnc from a wheel of this checkout (not editable), as a user installs it.
RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install "cocotb==${COCOTB}" \
 && /opt/venv/bin/pip wheel . --no-deps -w /tmp/wheel \
 && /opt/venv/bin/pip install /tmp/wheel/*.whl \
 && rm -rf /tmp/wheel build *.egg-info \
 && chown -R nnc:nnc /opt/venv

USER nnc
RUN nnc --version && verilator --version && yosys -V && cocotb-config --version

CMD ["nnc", "demo", "sync_fifo"]
