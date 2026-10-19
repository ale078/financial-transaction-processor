/**
 * Personal Finance Dashboard Application
 * Handles data fetching, currency conversions, interactive Chart.js charts, and live filtering.
 */

let state = {
  data: null,
  currency: "ARS", // 'ARS' or 'USD'
  selectedInstitution: "all",
  activeTab: "holdings",
  searchHoldings: "",
  filterAssetClass: "all",
  searchMovements: "",
  filterTxType: "all",
  charts: {}
};

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadDashboardData();
});

function initEventListeners() {
  // Currency Toggle
  document.getElementById("btn-ars").addEventListener("click", () => setCurrency("ARS"));
  document.getElementById("btn-usd").addEventListener("click", () => setCurrency("USD"));

  // Refresh Button
  document.getElementById("btn-refresh").addEventListener("click", refreshData);

  // Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });

  // Holdings Filter & Search
  const searchHoldingsEl = document.getElementById("search-holdings");
  if (searchHoldingsEl) {
    searchHoldingsEl.addEventListener("input", (e) => {
      state.searchHoldings = e.target.value.toLowerCase();
      renderHoldingsTable();
    });
  }

  const filterAssetEl = document.getElementById("filter-asset-class");
  if (filterAssetEl) {
    filterAssetEl.addEventListener("change", (e) => {
      state.filterAssetClass = e.target.value;
      renderHoldingsTable();
    });
  }

  // Movements Filter & Search
  const searchMovEl = document.getElementById("search-movements");
  if (searchMovEl) {
    searchMovEl.addEventListener("input", (e) => {
      state.searchMovements = e.target.value.toLowerCase();
      renderMovementsTable();
    });
  }

  const filterTxEl = document.getElementById("filter-tx-type");
  if (filterTxEl) {
    filterTxEl.addEventListener("change", (e) => {
      state.filterTxType = e.target.value;
      renderMovementsTable();
    });
  }
}

async function loadDashboardData() {
  try {
    const res = await fetch("/api/data");
    if (!res.ok) throw new Error("Network response was not ok");
    const data = await res.json();
    state.data = data;
    renderAll();
  } catch (err) {
    console.error("Error loading dashboard data:", err);
    showToast("Error al cargar los datos del portfolio", "error");
  }
}

async function refreshData() {
  const btn = document.getElementById("btn-refresh");
  const origHtml = btn.innerHTML;
  btn.innerHTML = `<span class="spinner"></span> Procesando...`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    state.data = data;
    renderAll();
    showToast("¡Archivos re-procesados con éxito!", "success");
  } catch (err) {
    console.error("Error refreshing data:", err);
    showToast("Error al actualizar los archivos", "error");
  } finally {
    btn.innerHTML = origHtml;
    btn.disabled = false;
  }
}

function setCurrency(curr) {
  state.currency = curr;
  document.getElementById("btn-ars").classList.toggle("active", curr === "ARS");
  document.getElementById("btn-usd").classList.toggle("active", curr === "USD");
  renderKPIs();
  renderInstitutionCards();
  renderCharts();
  renderHoldingsTable();
  renderBalancesTable();
  renderPlazosFijos();
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.getAttribute("data-tab") === tabId));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.toggle("active", c.id === `tab-${tabId}`));
}

function formatMoney(amount, forceCurrency = null) {
  const curr = forceCurrency || state.currency;
  const fx = state.data?.fx_rate_mep || 1480.46;
  let val = amount;

  if (curr === "USD" && !forceCurrency) {
    val = amount / fx;
  }

  const prefix = curr === "USD" ? "USD " : "$ ";
  return prefix + Number(val).toLocaleString("es-AR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function renderAll() {
  if (!state.data) return;

  // Header info
  document.getElementById("owner-name").textContent = state.data.owner_name;
  document.getElementById("meta-info").textContent = `${state.data.period_label} • TC MEP: $${state.data.fx_rate_mep.toLocaleString('es-AR')}`;

  renderKPIs();
  renderInstitutionCards();
  renderCharts();
  populateAssetClassDropdown();
  renderHoldingsTable();
  renderBalancesTable();
  renderMovementsTable();
  renderPlazosFijos();

  // Badges count
  document.getElementById("badge-holdings").textContent = state.data.holdings.length;
  document.getElementById("badge-balances").textContent = state.data.balances.length;
  document.getElementById("badge-movements").textContent = state.data.transactions.length;
  document.getElementById("badge-pf").textContent = state.data.plazos_fijos.length;
}

function renderKPIs() {
  const d = state.data;
  if (!d) return;

  document.getElementById("kpi-net-worth").textContent = formatMoney(d.total_net_worth_ars);
  document.getElementById("kpi-net-worth-sub").textContent = state.currency === "ARS" 
    ? `Equivalente: USD ${Number(d.total_net_worth_usd).toLocaleString("es-AR", {minimumFractionDigits: 2})} MEP`
    : `En Pesos: $ ${Number(d.total_net_worth_ars).toLocaleString("es-AR", {minimumFractionDigits: 2})}`;

  document.getElementById("kpi-liquidity").textContent = formatMoney(d.total_liquidity_ars);
  const liqPct = ((d.total_liquidity_ars / d.total_net_worth_ars) * 100).toFixed(1);
  document.getElementById("kpi-liquidity-sub").textContent = `${liqPct}% del patrimonio en liquidez / reservas`;

  document.getElementById("kpi-invested").textContent = formatMoney(d.total_invested_ars);
  const invPct = ((d.total_invested_ars / d.total_net_worth_ars) * 100).toFixed(1);
  document.getElementById("kpi-invested-sub").textContent = `${invPct}% en Títulos, ONs, Plazos Fijos y FCIs`;

  document.getElementById("kpi-yields").textContent = formatMoney(d.total_earned_yields_ars);
  document.getElementById("kpi-debt").textContent = formatMoney(d.total_debt_ars);
}

function renderInstitutionCards() {
  const grid = document.getElementById("institutions-grid");
  grid.innerHTML = "";

  const institutions = state.data.institutions;
  const icons = {
    "Banco Galicia": "🏛️",
    "Balanz Capital": "📈",
    "Mercado Pago": "💳",
    "Ualá Inversiones": "🚀"
  };

  for (const [name, inst] of Object.entries(institutions)) {
    const card = document.createElement("div");
    card.className = `glass-card inst-card ${state.selectedInstitution === name ? "active-filter" : ""}`;
    card.addEventListener("click", () => {
      if (state.selectedInstitution === name) {
        state.selectedInstitution = "all";
      } else {
        state.selectedInstitution = name;
      }
      renderInstitutionCards();
      renderHoldingsTable();
      renderMovementsTable();
    });

    const icon = icons[name] || "💼";
    card.innerHTML = `
      <div class="inst-top">
        <span class="inst-name">${icon} ${name}</span>
        <span class="badge-tag badge-primary">${inst.share_pct}%</span>
      </div>
      <div class="inst-val">${formatMoney(inst.total_ars)}</div>
      <div class="inst-bar-bg">
        <div class="inst-bar-fill" style="width: ${inst.share_pct}%;"></div>
      </div>
      <div class="inst-meta">
        <span>${inst.holdings_count} activos</span>
        <span>Liq: ${formatMoney(inst.liquidity_ars)}</span>
      </div>
    `;
    grid.appendChild(card);
  }
}

function renderCharts() {
  const d = state.data;
  if (!d) return;

  // 1. Institutions Doughnut Chart
  const instCtx = document.getElementById("chart-institutions")?.getContext("2d");
  if (instCtx) {
    if (state.charts.inst) state.charts.inst.destroy();

    const labels = Object.keys(d.institutions);
    const dataVals = labels.map(k => state.currency === "ARS" ? d.institutions[k].total_ars : d.institutions[k].total_usd);

    state.charts.inst = new Chart(instCtx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: dataVals,
          backgroundColor: [
            "#8b5cf6", // Purple (Galicia / Balanz)
            "#38bdf8", // Sky blue
            "#10b981", // Emerald
            "#f59e0b"  // Amber
          ],
          borderColor: "#111827",
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#94a3b8", font: { family: "Inter", size: 12 }, padding: 14 }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${formatMoney(ctx.raw, state.currency)} (${((ctx.raw / dataVals.reduce((a,b)=>a+b, 0))*100).toFixed(1)}%)`
            }
          }
        },
        cutout: "70%"
      }
    });
  }

  // 2. Asset Class Doughnut Chart
  const acCtx = document.getElementById("chart-asset-classes")?.getContext("2d");
  if (acCtx) {
    if (state.charts.ac) state.charts.ac.destroy();

    const acLabels = Object.keys(d.asset_classes);
    const acVals = acLabels.map(k => {
      const arsVal = d.asset_classes[k];
      return state.currency === "ARS" ? arsVal : arsVal / d.fx_rate_mep;
    });

    state.charts.ac = new Chart(acCtx, {
      type: "doughnut",
      data: {
        labels: acLabels,
        datasets: [{
          data: acVals,
          backgroundColor: [
            "#6366f1", "#a855f7", "#ec4899", "#3b82f6",
            "#14b8a6", "#10b981", "#f59e0b", "#f97316", "#64748b"
          ],
          borderColor: "#111827",
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#94a3b8", font: { family: "Inter", size: 11 }, padding: 10 }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${formatMoney(ctx.raw, state.currency)} (${((ctx.raw / acVals.reduce((a,b)=>a+b, 0))*100).toFixed(1)}%)`
            }
          }
        },
        cutout: "65%"
      }
    });
  }
}

function populateAssetClassDropdown() {
  const select = document.getElementById("filter-asset-class");
  if (!select || select.children.length > 1) return;

  const classes = Object.keys(state.data.asset_classes);
  classes.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    select.appendChild(opt);
  });
}

function renderHoldingsTable() {
  const tbody = document.getElementById("holdings-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  let list = state.data.holdings;

  // Filter institution
  if (state.selectedInstitution !== "all") {
    list = list.filter(h => h.institution === state.selectedInstitution);
  }

  // Filter asset class
  if (state.filterAssetClass !== "all") {
    list = list.filter(h => h.asset_class === state.filterAssetClass);
  }

  // Search
  if (state.searchHoldings) {
    list = list.filter(h => 
      h.ticker.toLowerCase().includes(state.searchHoldings) ||
      h.description.toLowerCase().includes(state.searchHoldings) ||
      h.institution.toLowerCase().includes(state.searchHoldings)
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-muted);">No se encontraron activos con los filtros aplicados.</td></tr>`;
    return;
  }

  list.forEach(h => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-primary";
    if (h.asset_class.includes("Bonos")) badgeClass = "badge-info";
    if (h.asset_class.includes("Plazos")) badgeClass = "badge-warning";
    if (h.asset_class.includes("Liquidez") || h.asset_class.includes("vista")) badgeClass = "badge-success";

    tr.innerHTML = `
      <td><span class="ticker-tag">${h.ticker}</span></td>
      <td><strong>${h.description}</strong></td>
      <td><span class="badge-tag ${badgeClass}">${h.asset_class}</span></td>
      <td>${h.institution}</td>
      <td style="text-align:right;">${Number(h.quantity).toLocaleString("es-AR", {maximumFractionDigits: 4})}</td>
      <td style="text-align:right; font-weight:700;">${formatMoney(h.total_value_ars)}</td>
      <td style="text-align:right;"><span class="badge-tag badge-primary">${h.weight_pct}%</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderBalancesTable() {
  const tbody = document.getElementById("balances-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  state.data.balances.forEach(b => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${b.institution}</strong></td>
      <td>${b.account_type}</td>
      <td><code>${b.account_number}</code></td>
      <td style="text-align:center;"><span class="badge-tag badge-info">${b.currency}</span></td>
      <td style="text-align:right;">${Number(b.balance).toLocaleString("es-AR", {minimumFractionDigits: 2})}</td>
      <td style="text-align:right; font-weight:700;">${formatMoney(b.balance_ars)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderMovementsTable() {
  const tbody = document.getElementById("movements-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  let list = state.data.transactions;

  if (state.selectedInstitution !== "all") {
    list = list.filter(t => t.institution === state.selectedInstitution);
  }

  if (state.filterTxType !== "all") {
    list = list.filter(t => t.tx_type === state.filterTxType);
  }

  if (state.searchMovements) {
    list = list.filter(t =>
      t.description.toLowerCase().includes(state.searchMovements) ||
      t.category.toLowerCase().includes(state.searchMovements) ||
      t.institution.toLowerCase().includes(state.searchMovements)
    );
  }

  // Limit display to 100 for optimal performance
  const displayList = list.slice(0, 100);

  if (displayList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:var(--text-muted);">No se encontraron transacciones.</td></tr>`;
    return;
  }

  displayList.forEach(t => {
    const tr = document.createElement("tr");
    const isPos = t.amount >= 0;
    const amountClass = isPos ? "amount-positive" : "amount-negative";

    tr.innerHTML = `
      <td><code>${t.date}</code></td>
      <td><strong>${t.institution}</strong></td>
      <td>${t.description}</td>
      <td><span class="badge-tag badge-primary">${t.category}</span></td>
      <td><span class="badge-tag ${isPos ? 'badge-success' : 'badge-warning'}">${t.tx_type}</span></td>
      <td style="text-align:right;" class="${amountClass}">
        ${isPos ? '+' : ''}${formatMoney(t.amount, t.currency === 'USD' ? 'USD' : null)}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPlazosFijos() {
  const grid = document.getElementById("pf-cards-grid");
  if (!grid) return;
  grid.innerHTML = "";

  state.data.plazos_fijos.forEach(pf => {
    const card = document.createElement("div");
    card.className = "glass-card pf-card";

    card.innerHTML = `
      <div class="pf-header">
        <div>
          <span class="ticker-tag">PF-${pf.number.slice(-6)}</span>
          <span style="font-size:12px; color:var(--text-muted); margin-left:8px;">Nro: ${pf.number}</span>
        </div>
        <span class="badge-tag badge-success">${pf.status}</span>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Constitución:</span>
        <span>${pf.start_date}</span>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Vencimiento:</span>
        <strong style="color:var(--secondary);">${pf.end_date}</strong>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Tasa TNA:</span>
        <strong style="color:var(--warning);">${pf.rate_tna}%</strong>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Capital Invertido:</span>
        <span>${formatMoney(pf.capital)}</span>
      </div>
      <div class="pf-val-row main">
        <span>Al Vencimiento:</span>
        <span style="color:var(--success);">${formatMoney(pf.maturity_amount)}</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

function showToast(message, type = "info") {
  let toast = document.getElementById("dashboard-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "dashboard-toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span>${type === 'success' ? '✅' : 'ℹ️'}</span> <span>${message}</span>`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}
