# syntax=docker/dockerfile:1.7

############################
# 0) 공통 ARG/ENV
############################
ARG PY_VER=3.12.12
ARG DEBIAN_DIST=trixie
ARG H2ORESTART_URL="https://github.com/ebandal/H2Orestart/releases/latest/download/H2Orestart.oxt"
ARG APP_VENV=/app/.venv
ARG NLTK_PACKAGES=all
ARG UID=1000
ARG GID=1000
ARG UNAME=genos
ARG GNAME=genos

############################
# 1) Base (APT + LibreOffice)
############################
FROM python:${PY_VER}-slim-${DEBIAN_DIST} AS base
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    XDG_CONFIG_HOME=/app/.config \
    XDG_DATA_HOME=/app/.local/share \
    XDG_RUNTIME_DIR=/tmp/xdg \
    TMPDIR=/app/tmp \
    HF_HOME=/app/.cache/huggingface
# [1/7] 시스템 도구 및 라이브러리
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      net-tools \
      curl \
      wget \
      fontconfig \
      procps \
      supervisor \
      vim \
      libmagic1 \
      libmagic-dev \
      libpango-1.0-0 \
      libpangocairo-1.0-0 \
      libcairo2 \
      libgdk-pixbuf-xlib-2.0-0 \
      libffi-dev \
      libgl1 \
      ffmpeg \
      unzip \
      sudo

# [2/7] 폰트
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends \
      fonts-dejavu \
      fonts-noto-cjk \
      fonts-noto-cjk-extra \
      fonts-nanum

# [3/7] 문서 처리 도구 (imagemagick, poppler, tesseract)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends \
      imagemagick \
      poppler-utils \
      tesseract-ocr \
      tesseract-ocr-eng \
      tesseract-ocr-kor

# [4/7] LibreOffice + Java (trixie only, sid 추가 전 — 의존성 충돌 방지)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends \
      locales-all \
      libreoffice \
      libreoffice-java-common \
      libreoffice-writer \
      libreoffice-impress \
      libreoffice-l10n-ko \
      openjdk-21-jre-headless \
      ca-certificates-java

# [5/7] sid 소스 추가 + Perl 5.40
# LibreOffice 설치 완료 후 sid 를 추가해야 의존성 해결 시 sid 패키지 혼입을 방지할 수 있다.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    echo "deb http://deb.debian.org/debian sid main" > /etc/apt/sources.list.d/sid.list && \
    apt-get update && \
    apt-get install -y -t sid perl perl-modules-5.40 libperl5.40

# [6/7] CVE 보안 패치 — 기설치 패키지 업그레이드
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends --only-upgrade \
      openssl libssl3t64 openssl-provider-legacy \
      curl libcurl4t64 libcurl3t64-gnutls \
      imagemagick \
      imagemagick-7.q16 \
      libmagickcore-7.q16-10 \
      libmagickwand-7.q16-10

# [7/7] Archive::Tar (cpanm) + 디렉토리 초기화
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get install -y --no-install-recommends cpanminus make && \
    cpanm --notest Archive::Tar && \
    apt-get purge -y cpanminus make && \
    apt-get autoremove -y && \
    rm -rf /root/.cpanm && \
    mkdir -p /app/.cache/huggingface /app/.cache/fontconfig /app/.config /app/.local/share /app/.fontconfig /app/nltk_data /app/tmp /tmp/xdg
RUN sed -i 's/# \(ko_KR.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && fc-cache -f -v || true

############################
# 2) LibreOffice 확장 (공통)
############################
FROM base AS loext
ARG H2ORESTART_URL
COPY ./genon/preprocessor/resources /app
RUN --mount=type=cache,target=/opt/h2o_cache \
    set -eux; \
    mkdir -p /opt/h2orestart /usr/lib/libreoffice/share/extensions/h2orestart; \
    if [ ! -f /opt/h2o_cache/H2Orestart.oxt ]; then \
      wget -O /opt/h2o_cache/H2Orestart.oxt "${H2ORESTART_URL}"; \
    fi; \
    cp /opt/h2o_cache/H2Orestart.oxt /opt/h2orestart/H2Orestart.oxt; \
    unzip -q -o /opt/h2orestart/H2Orestart.oxt -d /usr/lib/libreoffice/share/extensions/h2orestart; \
    soffice --headless --nologo --nodefault --nofirststartwizard --terminate_after_init
RUN set -eux; \
    mkdir -p /usr/share/fonts && \
    tar zxf /app/HCRBatang.ttf.tar.gz -C /usr/share/fonts/ && \
    fc-cache -f -v && rm /app/HCRBatang.ttf.tar.gz

############################
# 3) Builder (앱 venv만)
############################
FROM loext AS builder
ARG APP_VENV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_VIRTUALENVS_CREATE=1 \
    UV_VIRTUALENVS_IN_PROJECT=0 \
    UV_NO_INTERACTION=1 \
    UV_PYTHON=/usr/local/bin/python \
    UV_PROJECT_ENVIRONMENT=${APP_VENV} \
    APP_VENV=${APP_VENV} \
    PATH="${APP_VENV}/bin:${PATH}" \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    XDG_CONFIG_HOME=/app/.config \
    XDG_DATA_HOME=/app/.local/share \
    XDG_RUNTIME_DIR=/tmp/xdg \
    TMPDIR=/app/tmp \
    HF_HOME=/app/.cache/huggingface \
    NLTK_DATA=/app/nltk_data

# 앱 관련 pyproject만
COPY docling /app/docling
COPY pyproject.toml /app/pyproject.toml
COPY genon/preprocessor/pyproject.toml /app/genon/preprocessor/pyproject.toml
COPY genon/preprocessor/uv.lock /app/genon/preprocessor/uv.lock

WORKDIR /app/genon/preprocessor

# ✅ 공통 위치에 venv 생성
RUN uv venv ${APP_VENV}

# ✅ 그 venv에 설치
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen || \
    uv sync

############################
# 4a) 모델 아티팩트 — HuggingFace
############################
FROM builder AS models_hf
ARG APP_VENV
ARG HF_MODELS_VER=1.3.7

ENV PATH="${APP_VENV}/bin:${PATH}" \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    XDG_CONFIG_HOME=/app/.config \
    XDG_DATA_HOME=/app/.local/share \
    XDG_RUNTIME_DIR=/tmp/xdg \
    TMPDIR=/app/tmp \
    HF_HOME=/app/.cache/huggingface

RUN --mount=type=cache,target=/app/.cache/huggingface \
    echo "HF models ver: ${HF_MODELS_VER}"; \
    mkdir -p /models/doc_parser_models; \
    huggingface-cli download mncai/doc_parser_models --local-dir /models/doc_parser_models

RUN --mount=type=cache,target=/app/.cache/huggingface \
    huggingface-cli download mncai/doc_parser_models --include "sentence-transformers-all-MiniLM-L6-v2/*" --local-dir /models/doc_parser_models/sentence-transformers-all-MiniLM-L6-v2

############################
# 4b) 모델 아티팩트 — NLTK
############################
FROM builder AS models_nltk
ARG APP_VENV
ARG NLTK_PACKAGES=all

ENV PATH="${APP_VENV}/bin:${PATH}" \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    XDG_CONFIG_HOME=/app/.config \
    XDG_DATA_HOME=/app/.local/share \
    XDG_RUNTIME_DIR=/tmp/xdg \
    TMPDIR=/app/tmp \
    HF_HOME=/app/.cache/huggingface \
    NLTK_DATA=/app/nltk_data

RUN --mount=type=cache,target=/root/.cache/nltk \
    python - <<'PY'
import os
import nltk

target = os.environ.get("NLTK_DATA", "/app/nltk_data")
os.makedirs(target, exist_ok=True)

packages = os.environ.get("NLTK_PACKAGES", "all")
if packages == "all":
    nltk.download("all", download_dir=target)
else:
    for pkg in [p.strip() for p in packages.split(",") if p.strip()]:
        nltk.download(pkg, download_dir=target)
PY

############################
# 5) Runtime
############################
FROM loext AS runtime
ARG APP_VENV
ARG UID
ARG GID
ARG UNAME
ARG GNAME
ENV UV_PROJECT_ENVIRONMENT=${APP_VENV} \
    PATH="${APP_VENV}/bin:${PATH}" \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache \
    XDG_CONFIG_HOME=/app/.config \
    XDG_DATA_HOME=/app/.local/share \
    XDG_RUNTIME_DIR=/tmp/xdg \
    TMPDIR=/app/tmp \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    HF_HOME=/app/.cache/huggingface \
    NLTK_DATA=/app/nltk_data \
    LANG=ko_KR.UTF-8 \
    LC_ALL=ko_KR.UTF-8 \
    LC_CTYPE=ko_KR.UTF-8

WORKDIR /app
COPY ./genon/preprocessor/configs /app/configs
COPY ./genon/preprocessor/env /app/env
COPY ./genon/preprocessor/src /app/src

# ✅ 공통 venv 위치만 복사
COPY --from=builder ${APP_VENV} ${APP_VENV}

# ✅ 모델/자료 (스테이지별 독립 레이어)
COPY --from=models_hf /models/doc_parser_models /models/doc_parser_models
COPY --from=models_nltk /app/nltk_data /app/nltk_data

RUN ln -sf /app/configs/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
RUN getent group "${GID}" || groupadd -g "${GID}" "${GNAME}" && \
    getent passwd "${UID}" || useradd -m -u "${UID}" -g "${GID}" -s /bin/bash "${UNAME}" && \
    UNAME_ACTUAL="$(getent passwd "${UID}" | cut -d: -f1)" && \
    usermod -aG sudo "${UNAME_ACTUAL}" && \
    echo "${UNAME_ACTUAL} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /app/.cache/huggingface /app/.config/libreoffice /app/.cache/libreoffice /app/.local/share /app/tmp /tmp/xdg && \
    chown -R "${UID}:${GID}" /app /run /var/log /etc/supervisor /models /app/nltk_data /app/.cache /app/.config /app/.local /tmp/xdg
USER ${UID}:${GID}
CMD ["supervisord", "-n"]
