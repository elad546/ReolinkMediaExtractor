ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install python and deps
RUN apk add --no-cache python3 py3-pip && \
    python3 -m pip install --upgrade pip && \
    pip3 install flask requests

# Copy app
COPY run.sh /run.sh
RUN chmod a+x /run.sh
COPY app /app

# Default command
CMD ["/run.sh"]
