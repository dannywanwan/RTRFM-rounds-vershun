FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-requests tzdata

COPY run.sh /run.sh
COPY rtrfm_audio_archive.py /rtrfm_audio_archive.py

RUN chmod a+x /run.sh

CMD ["/run.sh"]
