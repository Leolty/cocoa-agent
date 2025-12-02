FROM ghcr.io/agent-infra/sandbox:latest

RUN mkdir -p /home/gem/assets
COPY assets/series.csv /home/gem/assets/
RUN chown -R 1000:1000 /home/gem/

