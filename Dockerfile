# SPDX-License-Identifier: AGPL-3.0-or-later
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts ./scripts
COPY editor ./editor
COPY LICENSES ./LICENSES
COPY NOTICE ./NOTICE
RUN useradd --create-home --uid 10001 editor8 && chown -R editor8:editor8 /app
USER editor8
ENV PYTHONUNBUFFERED=1 PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/healthz',timeout=3).read()"]
CMD ["python", "scripts/cloud_editor.py"]
