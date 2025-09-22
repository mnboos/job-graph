#!/bin/bash

PHOTON_DATA_DIR=photon_data
INDEX_URL=https://download1.graphhopper.com/public/experimental/extracts/by-country-code/ch/photon-db-ch-latest.tar.bz2

PHOTON_INDEX_FILE=${PHOTON_DATA_DIR}/$(basename $INDEX_URL)

# Download elasticsearch index
if [ ! -s $PHOTON_INDEX_FILE ]; then
    echo "Downloading search index"

    # Let graphhopper know where the traffic is coming from
    USER_AGENT="job-graph"
    wget \
    --no-check-certificate \
		--user-agent="$USER_AGENT" \
		--show-progress \
		--progress=bar:force:noscroll \
		-o $PHOTON_INDEX_FILE \
		$INDEX_URL
	
	pbzip2 -cd photon-db-ch-latest.tar.bz2 | tar x
fi

# Start photon if elastic index exists
if [ -s $PHOTON_INDEX_FIL ]; then
    echo "Start photon"
    java -jar photon.jar
else
    echo "Could not start photon, the search index could not be found"
fi
