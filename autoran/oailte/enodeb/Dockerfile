# docker build -t oai-enb .
# docker build --file Dockerfile -t samiemostafavi/autoran:oai-enb .
# docker push samiemostafavi/autoran:oai-enb

FROM rdefosseoai/oai-enb:develop
COPY generic.conf /opt/oai-enb/enb.conf
COPY entrypoint.sh /opt/oai-enb/entrypoint.sh
