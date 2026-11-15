
// ======================================
// FLOODGUARD AI - HOMEPAGE JAVASCRIPT
// ======================================

// 1. INDIA SATELLITE MAP

const map = L.map("indiaMap", {
    center: [22.5, 79],
    zoom: 4,
    minZoom: 3,
    maxZoom: 12
});

// Map layers
const mapLayers = {

    satellite: L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
            attribution: "Tiles © Esri"
        }
    ),

    street: L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "© OpenStreetMap contributors"
        }
    ),

    terrain: L.tileLayer(
        "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        {
            attribution: "© OpenTopoMap contributors"
        }
    )
};

// Default satellite view
let activeLayer = mapLayers.satellite;
activeLayer.addTo(map);


// 2. CHANGE MAP TYPE

document.getElementById("mapType").addEventListener("change", function () {

    const selectedLayer = mapLayers[this.value];

    if (!selectedLayer) return;

    map.removeLayer(activeLayer);

    activeLayer = selectedLayer;

    activeLayer.addTo(map);

});


// 3. WEATHER PLACEHOLDER

// Do not show invented temperatures or rainfall values.
// These elements will be populated when a real weather API is connected.

function clearWeatherData() {

    document.getElementById("temperatureValue").textContent = "--";

    document.getElementById("rainfallValue").textContent = "--";

    document.getElementById("humidityValue").textContent = "--";

    document.getElementById("windValue").textContent = "--";

    document.getElementById("otherValue").textContent = "--";

    document.getElementById("weatherCondition").textContent =
        "Weather data unavailable";

    document.getElementById("gaugeProgress").style.strokeDashoffset =
        "261";

}


// 4. TEMPERATURE GRAPH

// Graph remains empty until actual forecast data is connected.

function clearTemperatureGraph() {

    document.getElementById("temperatureLine").setAttribute("d", "");

    document.getElementById("temperatureArea").setAttribute("d", "");

}


// 5. INITIALIZE

clearWeatherData();

clearTemperatureGraph();

console.log("FloodGuard AI Home satellite map initialized.");
