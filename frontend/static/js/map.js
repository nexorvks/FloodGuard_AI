
// ============================================
// FLOODGUARD AI - OPTIMIZED DISTRICT RISK MAP
// ============================================


// 1. INITIALIZE INDIA MAP

const indiaMap = L.map("indiaRiskMap", {
    center: [22.5, 79],
    zoom: 4,
    minZoom: 3,
    maxZoom: 12,
    preferCanvas: true
});


// 2. MAP LAYERS

const mapLayers = {
    street: L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        { attribution: "© OpenStreetMap contributors" }
    ),

    satellite: L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { attribution: "Tiles © Esri" }
    ),

    terrain: L.tileLayer(
        "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        { attribution: "© OpenTopoMap" }
    )
};

let activeLayer = mapLayers.street;
activeLayer.addTo(indiaMap);

document.getElementById("mapType").addEventListener("change", function () {
    const selectedLayer = mapLayers[this.value];

    if (!selectedLayer) return;

    indiaMap.removeLayer(activeLayer);
    activeLayer = selectedLayer;
    activeLayer.addTo(indiaMap);
});


// 3. GLOBAL VARIABLES

let districtFeatures = [];
let searchableDistricts = [];

let districtLayer = L.featureGroup().addTo(indiaMap);
let selectedDistrictLayer = null;

let mapDataLoaded = false;
let pendingSearch = false;
let mapRenderingComplete = false;

let currentDistrictMap = null;
let currentDistrictCode = null;

// Cache historical data to avoid repeated API calls.
const historyCache = new Map();

// Canvas renderer
const canvasRenderer = L.canvas({
    padding: 0.5
});


// 4. DISTRICT HELPERS

function getDistrictName(properties) {
    return (
        properties.district ||
        properties.dtname ||
        properties.district_name ||
        properties.name ||
        "Unknown district"
    );
}

function getStateName(properties) {
    return (
        properties.state ||
        properties.stname ||
        properties.state_name ||
        "Unknown state"
    );
}

function getDistrictRisk(properties) {
    return (
        properties.risk_level ||
        properties.risk_category ||
        properties.risk ||
        "No data"
    );
}

function getRiskProbability(properties) {
    const probability = Number(properties.risk_probability);

    return Number.isFinite(probability)
        ? `${(probability * 100).toFixed(2)}%`
        : "Not available";
}

function getRiskColor(risk) {
    const value = String(risk || "").toLowerCase();

    if (value === "low") return "#39A96B";

    if (value === "moderate" || value === "medium") {
        return "#E8AD37";
    }

    if (value === "high") return "#DF4F55";

    return "#929B96";
}

function districtStyle(feature) {
    const risk = getDistrictRisk(feature.properties);

    return {
        renderer: canvasRenderer,
        fillColor: getRiskColor(risk),
        color: "#FFFFFF",
        weight: 1,
        fillOpacity: risk !== "No data" ? 0.65 : 0.2
    };
}


// 5. PREPARE SEARCH DATA

function prepareSearchData(features) {
    searchableDistricts = features.map(feature => {
        const properties = feature.properties || {};

        const district = getDistrictName(properties);
        const state = getStateName(properties);

        return {
            feature: feature,
            district: district,
            state: state,
            districtLower: district.toLowerCase(),
            stateLower: state.toLowerCase(),
            label: `${district}, ${state}`
        };
    });
}


// 6. DISPLAY SELECTED DISTRICT

function showDistrictInfo(feature) {
    const properties = feature.properties || {};

    const district = getDistrictName(properties);
    const state = getStateName(properties);
    const risk = getDistrictRisk(properties);

    document.getElementById("mapMessage").textContent =
        `${district}, ${state} — ${risk} risk`;

    document.getElementById("districtSearch").value = district;

    // Highlight selected district on India map
    if (selectedDistrictLayer) {
        districtLayer.removeLayer(selectedDistrictLayer);
    }

    selectedDistrictLayer = L.geoJSON(feature, {
        renderer: canvasRenderer,
        style: {
            color: "#8951EF",
            weight: 3,
            fillColor: "#8951EF",
            fillOpacity: 0.35
        }
    }).addTo(districtLayer);

    const bounds = selectedDistrictLayer.getBounds();

    if (bounds.isValid()) {
        indiaMap.fitBounds(bounds, {
            padding: [25, 25],
            maxZoom: 8
        });
    }

    displayDistrictDashboard(feature);
}


// 7. DISTRICT DASHBOARD

function displayDistrictDashboard(feature) {
    const properties = feature.properties || {};

    const district = getDistrictName(properties);
    const state = getStateName(properties);
    const risk = getDistrictRisk(properties);

    const dashboard = document.getElementById("districtDashboard");

    dashboard.hidden = false;

    document.getElementById("selectedDistrictName").textContent = district;
    document.getElementById("selectedDistrictState").textContent = state;
    document.getElementById("districtRisk").textContent = risk;

    document.getElementById("historicalFloods").textContent =
        "Loading historical records...";

    document.getElementById("floodedAreaStats").innerHTML =
        "<li>Loading flooded area data...</li>";

    document.getElementById("riskFactors").innerHTML =
        "<li>Loading impact data...</li>";

    document.getElementById("historicalEvents").textContent =
        "Loading historical flood records...";

    const probability = getRiskProbability(properties);

    document.getElementById("forecastMessage").textContent =
        `ML Risk Classification: ${risk} | Model Probability: ${probability}`;

    document.getElementById("forecastResults").innerHTML = "";
    

    // Create or reuse the district map
    if (!currentDistrictMap) {
        currentDistrictMap = L.map("districtMap", {
            scrollWheelZoom: false,
            preferCanvas: true
        });

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            { attribution: "© OpenStreetMap contributors" }
        ).addTo(currentDistrictMap);
    }

    if (window.selectedDetailLayer) {
        currentDistrictMap.removeLayer(window.selectedDetailLayer);
    }

    window.selectedDetailLayer = L.geoJSON(feature, {
        renderer: L.canvas(),
        style: {
            color: "#8951EF",
            weight: 3,
            fillColor: "#8951EF",
            fillOpacity: 0.35
        }
    }).addTo(currentDistrictMap);

    const bounds = window.selectedDetailLayer.getBounds();

    if (bounds.isValid()) {
        currentDistrictMap.fitBounds(bounds, {
            padding: [20, 20]
        });
    }

    dashboard.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    requestAnimationFrame(() => {
        currentDistrictMap.invalidateSize();
    });

    loadDistrictHistory(feature);
}


// 8. LOAD HISTORICAL DATA WITH CACHE

async function loadDistrictHistory(feature) {
    const properties = feature.properties || {};

    const district = getDistrictName(properties);
    const code = properties.district_code;

    const historicalElement =
        document.getElementById("historicalFloods");

    const areaElement =
        document.getElementById("floodedAreaStats");

    const impactElement =
        document.getElementById("riskFactors");

    const eventsElement =
        document.getElementById("historicalEvents");

    if (!code) {
        historicalElement.textContent = "District code unavailable.";
        areaElement.textContent = "Data unavailable.";
        impactElement.textContent = "Data unavailable.";
        eventsElement.textContent = "Historical records unavailable.";

        console.error("Missing district code:", properties);
        return;
    }

    const requestCode = String(code);
    currentDistrictCode = requestCode;

    try {
        let historyPromise = historyCache.get(requestCode);

        if (!historyPromise) {
            historyPromise = fetch(
                `/api/district/${encodeURIComponent(code)}/history?district_name=${encodeURIComponent(district)}`
            ).then(response => {
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                return response.json();
            });

            historyCache.set(requestCode, historyPromise);
        }

        const data = await historyPromise;

        // Ignore outdated response if user selected another district.
        if (currentDistrictCode !== requestCode) return;

        historicalElement.textContent =
            `${data.total_historical_events ?? 0} recorded flood events`;

        // Flooded area
        areaElement.innerHTML = "";

        const area = data.flooded_area?.[0];

        if (area) {
            const stats = [
                `Flooded area: ${area.Percent_Flooded_Area ?? "Not available"}%`,
                `Corrected flooded area: ${area.Corrected_Percent_Flooded_Area ?? "Not available"}%`,
                `Permanent water: ${area.Parmanent_Water ?? "Not available"}`
            ];

            stats.forEach(value => {
                const li = document.createElement("li");
                li.textContent = value;
                areaElement.appendChild(li);
            });
        } else {
            areaElement.textContent =
                "Flooded area information unavailable.";
        }

        // Historical impact
        impactElement.innerHTML = "";

        const impact = data.flood_impact?.[0];

        if (impact) {
            const factors = [
                `Human fatalities: ${impact.Human_fatality ?? "Not available"}`,
                `Human injuries: ${impact.Human_injured ?? "Not available"}`,
                `Population: ${impact.Population ?? "Not available"}`,
                `Mean flood duration: ${impact.Mean_Flood_Duration ?? "Not available"} days`
            ];

            factors.forEach(value => {
                const li = document.createElement("li");
                li.textContent = value;
                impactElement.appendChild(li);
            });
        } else {
            impactElement.textContent =
                "Historical impact information unavailable.";
        }

        displayHistoricalEvents(data.historical_events || []);

    } catch (error) {
        console.error("District history error:", error);

        // Remove failed request from cache so it can be retried.
        historyCache.delete(requestCode);

        if (currentDistrictCode !== requestCode) return;

        historicalElement.textContent =
            "Unable to load historical records.";

        areaElement.textContent = "Data unavailable.";
        impactElement.textContent = "Data unavailable.";
        eventsElement.textContent = "Unable to load historical events.";
    }
}


// 9. DISPLAY HISTORICAL EVENTS

function displayHistoricalEvents(events) {
    const container = document.getElementById("historicalEvents");

    if (!container) return;

    container.innerHTML = "";

    if (!Array.isArray(events) || events.length === 0) {
        container.textContent =
            "No matching historical flood records found.";
        return;
    }

    events.forEach(event => {
        const card = document.createElement("div");
        card.className = "historical-event-card";

        const title = document.createElement("h4");
        title.textContent = event["UEI"] || "Historical flood event";

        const details = document.createElement("p");
        details.textContent =
            `Start: ${event["Start Date"] || "N/A"} | ` +
            `End: ${event["End Date"] || "N/A"} | ` +
            `Duration: ${event["Duration(Days)"] ?? "N/A"} days`;

        const cause = document.createElement("p");
        cause.textContent =
            `Cause: ${event["Main Cause"] || "Not recorded"}`;

        const severity = document.createElement("p");
        severity.textContent =
            `Severity: ${event["Severity"] || "Not recorded"}`;

        const casualties = document.createElement("p");
        casualties.textContent =
            `Fatalities: ${event["Human fatality"] ?? "N/A"} | ` +
            `Injuries: ${event["Human injured"] ?? "N/A"} | ` +
            `Displaced: ${event["Human Displaced"] ?? "N/A"}`;

        card.append(title, details, cause, severity, casualties);
        container.appendChild(card);
    });
}


// 10. RENDER DISTRICTS IN SMALL BATCHES

function renderDistrictsInBatches(features) {
    let index = 0;

    const batchSize = 25;

    function renderBatch() {
        const fragment = features.slice(index, index + batchSize);

        fragment.forEach(feature => {
            const layer = L.geoJSON(feature, {
                renderer: canvasRenderer,
                style: districtStyle,

                onEachFeature: function (geoFeature, geoLayer) {

                    const properties = geoFeature.properties || {};

                    const popupContent = document.createElement("div");

                    const title = document.createElement("strong");
                    title.textContent =
                        `${getDistrictName(properties)}, ${getStateName(properties)}`;

                    const risk = document.createElement("p");
                    risk.textContent =
                        `Risk Level: ${getDistrictRisk(properties)}`;

                    const probability = document.createElement("p");
                    probability.textContent =
                        `Model Probability: ${getRiskProbability(properties)}`;

                    popupContent.append(title, risk, probability);

                    geoLayer.bindPopup(popupContent);

                    geoLayer.on("click", function () {
                        showDistrictInfo(geoFeature);
                    });
                }
            });

            districtLayer.addLayer(layer);
        });

        index += batchSize;

        if (index < features.length) {
            requestAnimationFrame(renderBatch);
        } else {
            mapRenderingComplete = true;

            document.getElementById("mapMessage").textContent =
                `${features.length} district features loaded.`;
            
            console.log("District rendering completed.");
        }
    }

    requestAnimationFrame(renderBatch);
}


// 11. LOAD INDIA DISTRICT DATA

async function loadRiskMap() {
    const message = document.getElementById("mapMessage");

    message.textContent = "Downloading district data...";

    console.time("Risk map download");

    try {
        const response = await fetch("/api/risk-map");

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        console.timeEnd("Risk map download");

        if (!Array.isArray(data.features)) {
            throw new Error("Invalid GeoJSON response.");
        }

        districtFeatures = data.features;

        if (districtFeatures.length === 0) {
            throw new Error("No district features received.");
        }

        console.log("District features received:", districtFeatures.length);

        // Search is ready immediately after data arrives.
        prepareSearchData(districtFeatures);

        mapDataLoaded = true;

        // Automatically perform a search that was waiting for map data.
        if (pendingSearch) {
            searchDistrict();
        }

        message.textContent =
            `District data downloaded. Rendering ${districtFeatures.length} districts...`;

        // Render map separately in batches.
        renderDistrictsInBatches(districtFeatures);

    } catch (error) {
        console.timeEnd("Risk map download");

        console.error("Risk map error:", error);

        message.textContent =
            "Unable to load district boundaries. Check the risk-map API.";
    }
}


// 12. FAST DISTRICT SEARCH

function searchDistrict() {
    const query = document
        .getElementById("districtSearch")
        .value.trim()
        .toLowerCase();

    const results = document.getElementById("searchResults");

    results.innerHTML = "";

    if (!query) {
        pendingSearch = false;
        results.textContent = "Enter a district name.";
        return;
    }

    // Remember the search if district data is still loading.
    if (!mapDataLoaded) {
        pendingSearch = true;
        results.textContent = "Loading district data. Your search will appear automatically...";
        return;
    }

    pendingSearch = false;

    const matches = searchableDistricts.filter(item =>
        item.districtLower.includes(query) ||
        item.stateLower.includes(query)
    );

    if (matches.length === 0) {
        results.textContent = "No matching district found.";
        return;
    }

    matches.slice(0, 20).forEach(item => {
        const button = document.createElement("button");

        button.className = "district-result";
        button.textContent = item.label;

        button.addEventListener("click", () => {
            showDistrictInfo(item.feature);
            results.innerHTML = "";
        });

        results.appendChild(button);
    });
}


// 13. SEARCH EVENTS

document
    .getElementById("searchDistrict")
    .addEventListener("click", searchDistrict);

document
    .getElementById("districtSearch")
    .addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            searchDistrict();
        }
    });


// 14. START APPLICATION

loadRiskMap();
