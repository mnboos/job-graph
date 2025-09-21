FROM eclipse-temurin:24-jre

#RUN apt update -y &&\
#	rm -rf /var/lib/apt/lists/*

WORKDIR /graphhopper

ADD https://github.com/graphhopper/graphhopper/releases/download/10.2/graphhopper-web-10.2.jar graphhopper.jar

COPY docker/graphhopper-entrypoint.sh entrypoint.sh

ENTRYPOINT /graphhopper/entrypoint.sh