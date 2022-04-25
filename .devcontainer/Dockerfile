FROM python:3.9

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade colorlog black pylint
RUN python -m pip install --upgrade homeassistant
RUN cd && mkdir -p /config/custom_components
RUN cd && mkdir -p /www/custom-lovelace


WORKDIR /workspace

# Set the default shell to bash instead of sh
ENV SHELL /bin/bash