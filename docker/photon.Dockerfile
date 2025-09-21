FROM eclipse-temurin:24-jre

RUN apt update -y &&\
	apt install -y pbzip2 &&\
	rm -rf /var/lib/apt/lists/*

WORKDIR /photon

ADD https://github.com/komoot/photon/releases/download/0.7.4/photon-opensearch-0.7.4.jar photon.jar

COPY docker/photon-entrypoint.sh entrypoint.sh

#CMD ["java", "-jar", "/photon/photon.jar"]
#ENTRYPOINT java -jar /photon/photon.jar

ENTRYPOINT /photon/entrypoint.sh