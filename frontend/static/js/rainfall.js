
const map = L.map("rainfallMap").setView([22.5, 82], 4);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

let geoLayer;
let rainfallRecords = [];
let selectedLayer = null;

function normalize(value) {
    return String(value || "")
        .toLowerCase()
        .trim()
        .replace(/&/g, "and")
        .replace(/\s+/g, " ");
}

function rainfallColor(value) {
    if (value < 250) return "#d9f0d3";
    if (value < 500) return "#91cf80";
    if (value < 1000) return "#f5df65";
    if (value < 2000) return "#f59b45";
    return "#d94343";
}

function getRainfall(feature) {
    const p = feature.properties || {};

    const district = p.district || p.dtname || p.DISTRICT;
    const state = p.state || p.stname || p.STATE;

    return rainfallRecords.find(record =>
        normalize(record.district) === normalize(district) &&
        normalize(record.state) === normalize(state)
    );
}

function showDistrict(record, layer) {
    if (selectedLayer) {
        geoLayer.resetStyle(selectedLayer);
    }

    selectedLayer = layer;

    if (selectedLayer) {
        selectedLayer.setStyle({
            color: "#102c22",
            weight: 3,
            fillOpacity: 0.95
        });
    }

    document.getElementById("districtDetails").innerHTML = `
        <h3>${record.district}, ${record.state}</h3>
        <p><strong>Total rainfall in 2026:</strong>
        ${Number(record.rainfall_mm).toFixed(2)} mm</p>
        <p><strong>Data through:</strong>
        ${record.data_through || "Not available"}</p>
    `;

    if (layer) {
        map.fitBounds(layer.getBounds(), { padding: [30, 30], maxZoom: 8 });
        layer.openPopup();
    }
}

function styleDistrict(feature) {
    const record = getRainfall(feature);

    return {
        fillColor: record
            ? rainfallColor(Number(record.rainfall_mm))
            : "#bfc9c2",
        weight: 0.7,
        color: "#53645a",
        fillOpacity: 0.8
    };
}

function loadMap(geojson) {
    geoLayer = L.geoJSON(geojson, {
        style: styleDistrict,

        onEachFeature: function(feature, layer) {
            const record = getRainfall(feature);
            const p = feature.properties || {};

            const district = p.district || p.dtname || p.DISTRICT || "Unknown";
            const state = p.state || p.stname || p.STATE || "";

            layer.bindPopup(record
                ? `<b>${record.district}, ${record.state}</b><br>
                   Annual rainfall: ${Number(record.rainfall_mm).toFixed(2)} mm`
                : `<b>${district}, ${state}</b><br>Rainfall data unavailable`
            );

            layer.on("click", function() {
                if (record) showDistrict(record, layer);
            });
        }
    }).addTo(map);

    if (geoLayer.getBounds().isValid()) {
        map.fitBounds(geoLayer.getBounds());
    }
}

function populateSearch() {
    const options = document.getElementById("districtOptions");

    options.innerHTML = rainfallRecords.map(record =>
        `<option value="${record.district}, ${record.state}"></option>`
    ).join("");
}

function updateSummary(data) {
    const valid = rainfallRecords.filter(
        r => Number.isFinite(Number(r.rainfall_mm))
    );

    const average = valid.length
        ? valid.reduce((sum, r) => sum + Number(r.rainfall_mm), 0) / valid.length
        : 0;

    const highest = valid.reduce(
        (best, r) => !best || Number(r.rainfall_mm) > Number(best.rainfall_mm)
            ? r : best,
        null
    );

    document.getElementById("indiaAverage").textContent =
        `${Number(data.average_rainfall_mm).toFixed(2)} mm`;

    document.getElementById("districtCount").textContent =
        `${valid.length} / ${data.total_districts}`;

    document.getElementById("highestDistrict").textContent =
        highest ? highest.district : "Unavailable";

    document.getElementById("highestValue").textContent =
        highest ? `${Number(highest.rainfall_mm).toFixed(2)} mm` : "";
}

async function initializeRainfall() {
    const loading = document.getElementById("loadingMessage");

    try {
        loading.textContent = "Loading annual rainfall data...";

        const [rainfallResponse, mapResponse] = await Promise.all([
            fetch("/api/rainfall/annual"),
            fetch("/api/risk-map")
        ]);

        if (!rainfallResponse.ok) {
            throw new Error("Rainfall API failed: " + rainfallResponse.status);
        }

        if (!mapResponse.ok) {
            throw new Error("District map API failed: " + mapResponse.status);
        }

        const rainfallData = await rainfallResponse.json();
        const mapData = await mapResponse.json();

        rainfallRecords = rainfallData.districts || [];

        updateSummary(rainfallData);
        populateSearch();
        loadMap(mapData);

        loading.textContent =
            `Rainfall data from ${rainfallData.data_through || "2026"} loaded.`;

    } catch (error) {
        console.error(error);
        loading.textContent =
            "Unable to load rainfall data. Check the backend API and browser console.";
    }
}

document.getElementById("districtSearch").addEventListener("change", function() {
    const query = normalize(this.value);

    const record = rainfallRecords.find(r =>
        normalize(`${r.district}, ${r.state}`) === query ||
        normalize(r.district) === query
    );

    if (!record) {
        document.getElementById("districtDetails").innerHTML =
            "<h3>District not found</h3><p>Try selecting a district from the suggestions.</p>";
        return;
    }

    let matchingLayer = null;

    geoLayer.eachLayer(layer => {
        const found = getRainfall(layer.feature);

        if (found &&
            normalize(found.district) === normalize(record.district) &&
            normalize(found.state) === normalize(record.state)) {
            matchingLayer = layer;
        }
    });

    showDistrict(record, matchingLayer);
});

initializeRainfall();
