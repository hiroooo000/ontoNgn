FROM mcr.microsoft.com/devcontainers/python:3.12

# Install LibreOffice, Poppler, Git, Vim, and other dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    libreoffice \
    poppler-utils \
    git \
    vim \
    curl

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && corepack enable pnpm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv package manager and Playwright system dependencies
RUN pip install --no-cache-dir uv playwright \
    && playwright install-deps \
    && pip uninstall -y playwright

# [Optional] Set the default shell to bash
ENV SHELL=/bin/bash
