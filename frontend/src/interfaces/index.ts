/**
 * Represents a single feature from the Photon geocoder response.
 * This interface is comprehensive enough for all provided samples.
 */
export interface PhotonFeature {
    properties: {
        // Core identifiers
        name?: string;
        type?: string;

        // Address components
        street?: string;
        housenumber?: string;
        postcode?: string;
        city?: string;
        district?: string;
        county?: string;
        state?: string;
        country?: string;
        countrycode?: string;

        // Bounding box
        extent?: [number, number, number, number];

        // OpenStreetMap metadata
        osm_type?: "N" | "W" | "R";
        osm_id?: number;
        osm_key?: string;
        osm_value?: string;
    };
    // Every feature is guaranteed to have a geometry object with coordinates.
    geometry: {
        type: "Point";
        coordinates: [number, number]; // [longitude, latitude]
    };
}
