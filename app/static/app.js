const $ = id => document.getElementById(id);
const history = [];
function setState(state) {
  document.querySelectorAll(".state").forEach(el => el.classList.remove("active"));
  $(state.toLowerCase()).classList.add("active");
}
async function refresh() {
  try {
    const response = await fetch("/api/status", {cache:"no-store"});
    if (!response.ok) throw new Error("API unavailable");
    const data = await response.json();
    $("sim").textContent = "SIMULATOR ACTIVE";
    $("rpm").textContent = data.engine_rpm;
    $("temp").textContent = data.coolant_temp_c.toFixed(1) + "°C";
    $("volt").textContent = data.system_voltage_v.toFixed(2) + "V";
    $("hz").textContent = data.frequency_hz + " HZ";
    setState(data.operational_state);
    $("status").textContent = data.operational_state === "Normal"
      ? "Model training pipeline currently in progress. CAN message simulation and structured data engineering fully operational."
      : data.operational_state === "Warning"
      ? "Warning threshold reached in simulated telemetry. Review coolant temperature and system voltage."
      : "Critical threshold reached in simulated telemetry. Inspect the simulated vehicle state.";
    history.push(data.engine_rpm);
    if (history.length > 50) history.shift();
    $("line").setAttribute("points", history.map((value,index) =>
      `${index * 500 / Math.max(49, history.length - 1)},${25 - (value - 2200) / 1500 * 22}`
    ).join(" "));
  } catch (error) {
    $("sim").textContent = "API DISCONNECTED";
    $("status").textContent = "Cannot reach telemetry API. Start the FastAPI service and refresh.";
  }
}
refresh();
setInterval(refresh, 1500);
