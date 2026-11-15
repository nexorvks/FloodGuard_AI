
let districts = [];

async function loadDistricts() {
    const response = await fetch("/api/risk-map");

    if (!response.ok) {
        throw new Error("Unable to load district data");
    }

    const geojson = await response.json();

    districts = geojson.features.map(feature => ({
        ...feature.properties
    }));

    document.getElementById("districtOptions").innerHTML =
        districts.map(d => {
            const name = d.district || d.dtname;
            const state = d.state || d.stname;

            return `<option value="${name}, ${state}"></option>`;
        }).join("");
}

function showPrediction(district) {
    const risk = district.risk_level || "No data";
    const scores = district.risk_scores;

    const colors = {
        Low: "#29945b",
        Moderate: "#d99a20",
        High: "#d94343"
    };

    const dashboard = document.getElementById("predictionDashboard");

    dashboard.hidden = false;

    document.getElementById("districtName").textContent =
        district.district;

    document.getElementById("stateName").textContent =
        district.state;

    const result = document.getElementById("predictionResult");

    if (!scores || typeof scores !== "object") {
        result.innerHTML = `
            <h2>No prediction available</h2>
            <p>There is currently no model prediction for this district.</p>
        `;
        return;
    }

    const best = Object.entries(scores)
        .sort((a, b) => Number(b[1]) - Number(a[1]))[0];

    const confidence = Number(district.risk_probability);

    result.innerHTML = `
        <div class="risk-result">
            <p>Predicted flood-risk level</p>
            <h1 style="color:${colors[best[0]] || "#555"}">
                ${best[0].toUpperCase()}
            </h1>
            <p>Model confidence:
                ${Number.isFinite(confidence)
                    ? (confidence * 100).toFixed(2) + "%"
                    : "Unavailable"}
            </p>
        </div>

        <h3>Risk class scores</h3>

        ${["Low", "Moderate", "High"].map(level => {
            const value = Number(scores[level] || 0) * 100;

            return `
                <div class="score">
                    <p>${level} <strong>${value.toFixed(2)}%</strong></p>
                    <div class="track">
                        <div style="
                            width:${Math.max(0, Math.min(100, value))}%;
                            background:${colors[level]};
                        "></div>
                    </div>
                </div>
            `;
        }).join("")}

        <p class="disclaimer">
            Model confidence represents the classifier's confidence,
            not the probability that a flood will occur.
        </p>
    `;
}

function searchDistrict() {
    const query = document.getElementById("districtSearch")
        .value.trim().toLowerCase();

    const district = districts.find(d => {
        const name = (d.district || d.dtname || "").toLowerCase();
        const state = (d.state || d.stname || "").toLowerCase();

        return `${name}, ${state}` === query || name === query;
    });

    if (!district) {
        document.getElementById("searchMessage").textContent =
            "District not found. Try selecting a district from the suggestions.";

        document.getElementById("predictionDashboard").hidden = true;
        return;
    }

    document.getElementById("searchMessage").textContent = "";

    showPrediction(district);

    document.getElementById("predictionDashboard")
        .scrollIntoView({ behavior: "smooth" });
}

document.getElementById("searchDistrict")
    .addEventListener("click", searchDistrict);

document.getElementById("districtSearch")
    .addEventListener("keydown", event => {
        if (event.key === "Enter") searchDistrict();
    });

loadDistricts().catch(error => {
    console.error(error);
    document.getElementById("searchMessage").textContent =
        "Unable to load district information. Check the backend.";
});
