# docker build -t oai-lte-ue . 
# docker build --file Dockerfile -t samiemostafavi/autoran:oai-lte-ue .
# docker push samiemostafavi/autoran:oai-lte-ue
FROM rdefosseoai/oai-lte-ue:develop
COPY ue_generic.conf /opt/oai-lte-ue/ue_usim.conf
COPY entrypoint.sh /opt/oai-lte-ue/entrypoint.sh
