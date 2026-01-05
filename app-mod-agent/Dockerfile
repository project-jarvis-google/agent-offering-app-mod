# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

### Stage 1

FROM golang:1.22-alpine AS go-builder

ENV GOBIN=/go-installs

RUN go install github.com/go-enry/enry@latest

### Stage 2

FROM python:3.11-slim

RUN pip install --no-cache-dir uv==0.6.12 && \
    apt-get update && \
    apt-get install -y --no-install-recommends git nodejs npm && \
    npm install -g node-gyp && \
    npm install -g @google/gemini-cli && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN mkdir /go-installs

COPY ./pyproject.toml ./uv.lock* ./

COPY --from=go-builder /go-installs /go-installs

COPY ./app ./app

RUN uv sync --frozen

ARG COMMIT_SHA=""
ENV COMMIT_SHA=${COMMIT_SHA}

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]