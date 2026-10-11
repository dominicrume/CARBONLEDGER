# CarbonLedger API serving the app from one origin. Railway builds this; PORT is injected.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY packages ./packages
COPY services ./services
COPY apps/web ./apps/web
COPY db ./db
COPY scripts/start.sh scripts/migrate.py ./scripts/
RUN rm -rf apps/web/node_modules apps/web/test apps/web/test-results && chmod +x scripts/start.sh
ENV PYTHONPATH=/srv/packages/core:/srv/services/api WEB_DIR=/srv/apps/web APP_ENV=demo CHAIN_MODE=dry-run
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health')"
CMD ["scripts/start.sh"]
