#!/bin/bash

# Download elasticsearch index
if [ -z "$( ls -A '/photon/photon_data' )" ]; then
    echo "Downloading search index"

    # Let graphhopper know where the traffic is coming from
    USER_AGENT="job-graph"
    wget \
		--user-agent="$USER_AGENT" \
		--no-verbose \
		--show-progress \
		--progress=dot:giga \
		-o /photon/photon_data/photon-db-ch-latest.tar.bz2 \
		https://download1.graphhopper.com/public/experimental/extracts/by-country-code/ch/photon-db-ch-latest.tar.bz2
	
	pbzip2 -cd photon-db-ch-latest.tar.bz2 | tar x
fi

# Start photon if elastic index exists
if [ -d "/photon/photon_data" ]; then
    echo "Start photon"
    java -jar photon.jar
else
    echo "Could not start photon, the search index could not be found"
fi
