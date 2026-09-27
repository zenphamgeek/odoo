# ==============================================================================
# Insilos Enterprise Platform — Production Container Image (Odoo 20 Hardfork)
# Multi-stage build with Python 3.12 & OWL 2.0 assets
# ==============================================================================

FROM python:3.12-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-deps ofxparse==0.21 lxml-html-clean==0.4.5 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir paramiko pyjwt xmlsec phonenumbers boto3 redis

# Production Runtime Stage
FROM python:3.12-slim-bookworm AS runner

ARG RELEASE_TAG=v20.0.0-qa

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    INSILOS_RC=/etc/insilos.conf \
    INSILOS_RELEASE_TAG=${RELEASE_TAG}

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    zlib1g \
    curl \
    ca-certificates \
    postgresql-client \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    libxrender1 \
    libxext6 \
    libx11-6 \
    fonts-liberation \
    && curl -o /tmp/wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get install -y --no-install-recommends /tmp/wkhtmltox.deb \
    && rm -f /tmp/wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/insilos

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application codebase
COPY . /app/insilos/

# Set up user, directories, symlinks, and permissions
RUN useradd -m -u 1000 -s /bin/bash insilos && \
    ln -s /app/insilos/enterprise /app/insilos/apps && \
    ln -s /app/insilos /opt/insilos && \
    mkdir -p /var/lib/insilos/filestore /var/log/insilos && \
    chown -R insilos:insilos /app /var/lib/insilos /var/log/insilos && \
    printf '[options]\naddons_path = /app/insilos/addons,/app/insilos/apps\ndata_dir = /var/lib/insilos/filestore\nlogfile = /var/log/insilos/insilos.log\nlog_level = info\nproxy_mode = True\n' > /etc/insilos.conf && \
    cp /etc/insilos.conf /etc/odoo.conf && \
    chown insilos:insilos /etc/insilos.conf /etc/odoo.conf

USER insilos

EXPOSE 8069 8072

ENTRYPOINT ["python3", "/app/insilos/insilos-bin"]
CMD ["-c", "/etc/insilos.conf"]
