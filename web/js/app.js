/**
 * Personal Finance Dashboard Application - Edición Argentina
 * Handles data fetching, currency conversions, interactive Chart.js charts, and live filtering.
 */

let state = {
  data: null,
  cedears: null,
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
  loadCedearsData();
});

function initEventListeners() {
  // Currency Toggle
  document.getElementById("btn-ars").addEventListener("click", () => setCurrency("ARS"));
  document.getElementById("btn-usd").addEventListener("click", () => setCurrency("USD"));

  // Refresh Button
  document.getElementById("btn-refresh").addEventListener("click", refreshData);

  // CEDEARs Live Refresh Button
  const btnCedears = document.getElementById("btn-refresh-cedears");
  if (btnCedears) {
    btnCedears.addEventListener("click", () => loadCedearsData(true));
  }

  // Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });

  // Quick Filter Chips for Holdings
  document.querySelectorAll("#quick-filter-chips .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const cls = chip.getAttribute("data-class");
      state.filterAssetClass = cls;
      
      document.querySelectorAll("#quick-filter-chips .chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      const select = document.getElementById("filter-asset-class");
      if (select) select.value = cls;

      renderHoldingsTable();
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
      
      // Sync chip active state
      document.querySelectorAll("#quick-filter-chips .chip").forEach(chip => {
        chip.classList.toggle("active", chip.getAttribute("data-class") === e.target.value);
      });

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

window.resetInstitutionFilter = function() {
  state.selectedInstitution = "all";
  renderInstitutionCards();
  renderHoldingsTable();
  renderMovementsTable();
};

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
  btn.innerHTML = `<span class="spinner"></span> Reprocesando extractos...`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    state.data = data;
    renderAll();
    showToast("¡Extractos y comprobantes consolidados con éxito!", "success");
  } catch (err) {
    console.error("Error refreshing data:", err);
    showToast("Error al actualizar los extractos", "error");
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
  renderCedears();
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

  // Header and Market Ticker info
  const d = state.data;
  document.getElementById("owner-name").textContent = d.owner_name;
  document.getElementById("meta-info").textContent = `${d.period_label} • TC MEP Oficial: $${Number(d.fx_rate_mep).toLocaleString('es-AR', {minimumFractionDigits: 2})} • Balanz & Bancos de Argentina`;

  const mepEl = document.getElementById("ticker-mep");
  if (mepEl) mepEl.textContent = `$ ${Number(d.fx_rate_mep).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;

  const cclEl = document.getElementById("ticker-ccl");
  if (cclEl) cclEl.textContent = `$ ${Number(d.fx_rate_ccl).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;

  const footerMep = document.getElementById("footer-mep-val");
  if (footerMep) footerMep.textContent = `$ ${Number(d.fx_rate_mep).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;

  renderKPIs();
  renderInstitutionCards();
  renderCharts();
  populateAssetClassDropdown();
  renderHoldingsTable();
  renderBalancesTable();
  renderMovementsTable();
  renderPlazosFijos();
  renderCedears();

  // Badges count
  document.getElementById("badge-holdings").textContent = d.holdings.length;
  document.getElementById("badge-balances").textContent = d.balances.length;
  document.getElementById("badge-movements").textContent = d.transactions.length;
  document.getElementById("badge-pf").textContent = d.plazos_fijos.length;
  const cedearsCount = d.holdings.filter(h => (h.asset_class || '').toLowerCase().includes('cedear') || ['ibit','vist','coin','ogzd'].includes((h.ticker||'').toLowerCase())).length;
  const badgeCedEl = document.getElementById("badge-cedears");
  if (badgeCedEl) badgeCedEl.textContent = cedearsCount;
}

function renderKPIs() {
  const d = state.data;
  if (!d) return;

  document.getElementById("kpi-net-worth").textContent = formatMoney(d.total_net_worth_ars);
  document.getElementById("kpi-net-worth-sub").textContent = state.currency === "ARS" 
    ? `Equivalente en Dólar MEP: USD ${Number(d.total_net_worth_usd).toLocaleString("es-AR", {minimumFractionDigits: 2})}`
    : `En Moneda Nacional: $ ${Number(d.total_net_worth_ars).toLocaleString("es-AR", {minimumFractionDigits: 2})}`;

  document.getElementById("kpi-liquidity").textContent = formatMoney(d.total_liquidity_ars);
  const liqPct = ((d.total_liquidity_ars / d.total_net_worth_ars) * 100).toFixed(1);
  document.getElementById("kpi-liquidity-sub").textContent = `${liqPct}% del patrimonio en saldo disponible y billeteras`;

  document.getElementById("kpi-invested").textContent = formatMoney(d.total_invested_ars);
  const invPct = ((d.total_invested_ars / d.total_net_worth_ars) * 100).toFixed(1);
  document.getElementById("kpi-invested-sub").textContent = `${invPct}% en ONs, Bonos Soberanos, PFs y CEDEARs`;

  document.getElementById("kpi-yields").textContent = formatMoney(d.total_earned_yields_ars);
  document.getElementById("kpi-debt").textContent = formatMoney(d.total_debt_ars);
}

function renderInstitutionCards() {
  const grid = document.getElementById("institutions-grid");
  if (!grid) return;
  grid.innerHTML = "";

  const clearBtn = document.getElementById("btn-clear-inst");
  if (clearBtn) {
    clearBtn.style.display = state.selectedInstitution !== "all" ? "inline-block" : "none";
  }

  const institutions = state.data.institutions;
  const brandConfig = {
    "Banco Galicia": {
      icon: "🏛️",
      badge: "Banca Éminent",
      badgeClass: "badge-inst-galicia",
      cardClass: "brand-galicia",
      barClass: "bar-galicia"
    },
    "Balanz Capital": {
      icon: "📈",
      badge: "ALyC Nº 210 CNV",
      badgeClass: "badge-inst-balanz",
      cardClass: "brand-balanz",
      barClass: "bar-balanz"
    },
    "Mercado Pago": {
      icon: "💳",
      badge: "Cuenta & CVU",
      badgeClass: "badge-inst-mp",
      cardClass: "brand-mp",
      barClass: "bar-mp"
    },
    "Ualá Inversiones": {
      icon: "🚀",
      badge: "ALyC Ualintec",
      badgeClass: "badge-inst-uala",
      cardClass: "brand-uala",
      barClass: "bar-uala"
    }
  };

  for (const [name, inst] of Object.entries(institutions)) {
    const config = brandConfig[name] || {
      icon: "💼",
      badge: "Entidad Financiera",
      badgeClass: "badge-cielo",
      cardClass: "",
      barClass: "bar-balanz"
    };

    const card = document.createElement("div");
    const isSelected = state.selectedInstitution === name;
    card.className = `glass-card inst-card ${config.cardClass} ${isSelected ? "active-filter" : ""}`;
    card.title = isSelected ? "Haz clic para quitar el filtro" : `Filtrar por ${name}`;

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

    card.innerHTML = `
      <div class="inst-top">
        <span class="inst-name">${config.icon} ${name}</span>
        <span class="inst-badge-official ${config.badgeClass}">${config.badge}</span>
      </div>
      <div class="inst-val">${formatMoney(inst.total_ars)}</div>
      <div class="inst-bar-bg">
        <div class="inst-bar-fill ${config.barClass}" style="width: ${inst.share_pct}%;"></div>
      </div>
      <div class="inst-meta">
        <span>${inst.holdings_count} activos (${inst.share_pct}%)</span>
        <span>Disp: ${formatMoney(inst.liquidity_ars)}</span>
      </div>
    `;
    grid.appendChild(card);
  }
}

function renderCharts() {
  const d = state.data;
  if (!d) return;

  // 1. Institutions Doughnut Chart with Authentic Argentine Brand Colors
  const instCtx = document.getElementById("chart-institutions")?.getContext("2d");
  if (instCtx) {
    if (state.charts.inst) state.charts.inst.destroy();

    const labels = Object.keys(d.institutions);
    const dataVals = labels.map(k => state.currency === "ARS" ? d.institutions[k].total_ars : d.institutions[k].total_usd);

    const colorMap = {
      "Banco Galicia": "#F36F21",       // Naranja oficial Galicia
      "Balanz Capital": "#00A3E0",      // Cyan oficial Balanz
      "Mercado Pago": "#009EE3",       // Celeste oficial MP
      "Ualá Inversiones": "#FF3366"     // Coral oficial Ualá
    };
    const defaultColors = ["#00A3E0", "#F36F21", "#009EE3", "#FF3366", "#10b981"];
    const bgColors = labels.map((name, i) => colorMap[name] || defaultColors[i % defaultColors.length]);

    state.charts.inst = new Chart(instCtx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: dataVals,
          backgroundColor: bgColors,
          borderColor: "#060c17",
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: "#94a3b8",
              font: { family: "Outfit, Plus Jakarta Sans, sans-serif", size: 12, weight: 600 },
              padding: 14
            }
          },
          tooltip: {
            backgroundColor: "rgba(6, 12, 23, 0.95)",
            titleColor: "#74ACDF",
            bodyColor: "#ffffff",
            borderColor: "rgba(116, 172, 223, 0.3)",
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${formatMoney(ctx.raw, state.currency)} (${((ctx.raw / dataVals.reduce((a,b)=>a+b, 0))*100).toFixed(1)}%)`
            }
          }
        },
        cutout: "68%"
      }
    });
  }

  // 2. Asset Class Doughnut Chart with National & Financial Palette
  const acCtx = document.getElementById("chart-asset-classes")?.getContext("2d");
  if (acCtx) {
    if (state.charts.ac) state.charts.ac.destroy();

    const acLabels = Object.keys(d.asset_classes);
    const acVals = acLabels.map(k => {
      const arsVal = d.asset_classes[k];
      return state.currency === "ARS" ? arsVal : arsVal / d.fx_rate_mep;
    });

    const assetColors = [
      "#00A3E0", // Cyan / Balanz
      "#FFB81C", // Sol de Mayo Gold (PFs)
      "#74ACDF", // Celeste Albiceleste
      "#38BDF8", // Sky Blue
      "#10B981", // Emerald (Liquidity)
      "#818CF8", // Indigo (Bonos)
      "#F59E0B", // Amber
      "#F43F5E", // Rose
      "#64748B"  // Slate
    ];

    state.charts.ac = new Chart(acCtx, {
      type: "doughnut",
      data: {
        labels: acLabels,
        datasets: [{
          data: acVals,
          backgroundColor: assetColors.slice(0, acLabels.length),
          borderColor: "#060c17",
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: "#94a3b8",
              font: { family: "Outfit, Plus Jakarta Sans, sans-serif", size: 11, weight: 600 },
              padding: 10
            }
          },
          tooltip: {
            backgroundColor: "rgba(6, 12, 23, 0.95)",
            titleColor: "#FFB81C",
            bodyColor: "#ffffff",
            borderColor: "rgba(255, 184, 28, 0.3)",
            borderWidth: 1,
            padding: 12,
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
    const f = state.filterAssetClass.toLowerCase();
    list = list.filter(h => {
      const cls = (h.asset_class || "").toLowerCase();
      if (f === "bonos soberanos") return cls === "bonos soberanos" || cls.includes("soberano");
      if (f === "cedears") return cls === "cedears" || cls.includes("cedear");
      if (f === "acciones") return cls === "acciones" || cls.includes("accion");
      if (f === "corporativos / on" || f === "corporativos" || f === "on") {
        return cls === "corporativos / on" || cls.includes("corporativo") || (/\bon\b/i.test(cls));
      }
      if (f.includes("plazo")) return cls.includes("plazo");
      if (f.includes("fondo") || f.includes("fci")) return cls.includes("fondo") || cls.includes("fci");
      if (f.includes("liquidez")) return cls.includes("liquidez") || cls.includes("vista") || cls.includes("reserva");
      return cls === f;
    });
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
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:36px; color:var(--text-muted); font-size:14px;">No se encontraron activos con los filtros seleccionados.</td></tr>`;
    return;
  }

  list.forEach(h => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-cielo";
    if (h.asset_class.includes("Bonos") || h.asset_class.includes("Bopreal")) badgeClass = "badge-primary";
    if (h.asset_class.includes("Plazos")) badgeClass = "badge-gold";
    if (h.asset_class.includes("Liquidez") || h.asset_class.includes("vista")) badgeClass = "badge-success";
    if (h.asset_class.includes("CEDEAR") || h.asset_class.includes("Acciones")) badgeClass = "badge-gold";

    tr.innerHTML = `
      <td><span class="ticker-tag">${h.ticker}</span></td>
      <td><strong>${h.description}</strong></td>
      <td><span class="badge-tag ${badgeClass}">${h.asset_class}</span></td>
      <td>${h.institution}</td>
      <td style="text-align:right; font-family:'JetBrains Mono', monospace;">${Number(h.quantity).toLocaleString("es-AR", {maximumFractionDigits: 4})}</td>
      <td style="text-align:right; font-weight:800; font-family:'Outfit', sans-serif;">${formatMoney(h.total_value_ars)}</td>
      <td style="text-align:right;"><span class="badge-tag badge-cielo">${h.weight_pct}%</span></td>
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
      <td><code style="font-family:'JetBrains Mono', monospace; font-size:12px;">${b.account_number}</code></td>
      <td style="text-align:center;"><span class="badge-tag badge-cielo">${b.currency}</span></td>
      <td style="text-align:right; font-family:'JetBrains Mono', monospace;">${Number(b.balance).toLocaleString("es-AR", {minimumFractionDigits: 2})}</td>
      <td style="text-align:right; font-weight:800; font-family:'Outfit', sans-serif;">${formatMoney(b.balance_ars)}</td>
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

  const displayList = list.slice(0, 100);

  if (displayList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:36px; color:var(--text-muted); font-size:14px;">No se encontraron movimientos registrados con este criterio.</td></tr>`;
    return;
  }

  displayList.forEach(t => {
    const tr = document.createElement("tr");
    const isPos = t.amount >= 0;
    const amountClass = isPos ? "amount-positive" : "amount-negative";

    tr.innerHTML = `
      <td><code style="font-family:'JetBrains Mono', monospace; font-size:12px;">${t.date}</code></td>
      <td><strong>${t.institution}</strong></td>
      <td>${t.description}</td>
      <td><span class="badge-tag badge-cielo">${t.category}</span></td>
      <td><span class="badge-tag ${isPos ? 'badge-success' : 'badge-warning'}">${t.tx_type}</span></td>
      <td style="text-align:right; font-family:'Outfit', sans-serif;" class="${amountClass}">
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
          <span style="font-size:12px; color:var(--text-muted); margin-left:8px; font-family:'JetBrains Mono', monospace;">Nº ${pf.number}</span>
        </div>
        <span class="badge-tag badge-success">${pf.status}</span>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Fecha Imposición:</span>
        <span style="font-weight:600;">${pf.start_date}</span>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Fecha Vencimiento:</span>
        <strong style="color:var(--cielo-light);">${pf.end_date}</strong>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Tasa Nominal Anual (TNA):</span>
        <strong style="color:var(--oro-mayo);">${pf.rate_tna}%</strong>
      </div>
      <div class="pf-val-row">
        <span style="color:var(--text-muted);">Capital Inicial Depositado:</span>
        <span>${formatMoney(pf.capital)}</span>
      </div>
      <div class="pf-val-row main">
        <span>Monto Total a Cobrar:</span>
        <span style="color:#34d399;">${formatMoney(pf.maturity_amount)}</span>
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
  toast.innerHTML = `<span>${type === 'success' ? '🇦🇷' : 'ℹ️'}</span> <span>${message}</span>`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}

/* ──────────────────────────────────────────────────────────────────────────
   CEDEARs & Yahoo Finance BYMA Live Integration
   ────────────────────────────────────────────────────────────────────────── */

async function loadCedearsData(forceRefresh = false) {
  const syncEl = document.getElementById("cedears-last-sync");
  const btn = document.getElementById("btn-refresh-cedears");
  
  if (syncEl) syncEl.textContent = forceRefresh ? "Consultando BYMA / Yahoo Finance..." : "Sincronizando precios...";
  if (btn) btn.disabled = true;

  try {
    const url = `/api/cedears${forceRefresh ? "?force=1" : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Error en cotizaciones CEDEAR");
    const data = await res.json();
    state.cedears = data.quotes || {};

    if (syncEl) {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      syncEl.textContent = `Actualizado ${timeStr} ${data.cached ? '(Caché 5m)' : '(En vivo)'}`;
    }

    renderCedears();
    if (forceRefresh) {
      showToast("Precios de CEDEARs actualizados desde BYMA", "success");
    }
  } catch (err) {
    console.error("Error al cargar CEDEARs:", err);
    if (syncEl) syncEl.textContent = "Error al obtener cotizaciones en vivo";
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderCedears() {
  if (!state.data) return;

  const holdings = state.data.holdings || [];
  const movements = state.data.transactions || state.data.movements || [];
  const quotes = state.cedears || {};

  // 1. Filter active CEDEAR holdings
  const cedearHoldings = holdings.filter(h => {
    const cls = (h.asset_class || "").toLowerCase();
    const desc = (h.description || "").toLowerCase();
    const t = (h.ticker || "").toLowerCase();
    return cls.includes("cedear") || desc.includes("cedear") || ["ibit", "vist", "coin", "ogzd"].includes(t);
  });

  // Update Badge count
  const badgeEl = document.getElementById("badge-cedears");
  if (badgeEl) badgeEl.textContent = cedearHoldings.length;

  let totalMarketARS = 0;
  let totalBookARS = 0;

  // Render Holdings Table
  const tbodyHoldings = document.getElementById("cedears-holdings-tbody");
  if (tbodyHoldings) {
    tbodyHoldings.innerHTML = "";

    cedearHoldings.forEach(h => {
      const ticker = (h.ticker || "").toUpperCase();
      const quote = quotes[ticker] || quotes[ticker.replace(".BA", "")] || {};
      const qty = Number(h.quantity) || 0;
      const bookTotal = Number(h.total_value_ars || h.amount_ars) || 0;
      const bookUnit = qty > 0 ? (bookTotal / qty) : 0;
      totalBookARS += bookTotal;

      let currentPrice = quote.price;
      let marketTotal = bookTotal;
      let pnl = 0;
      let pnlPct = 0;
      let changePct = quote.change_pct || 0;

      if (currentPrice && currentPrice > 0) {
        marketTotal = currentPrice * qty;
        pnl = marketTotal - bookTotal;
        pnlPct = bookTotal > 0 ? ((pnl / bookTotal) * 100) : 0;
      }
      totalMarketARS += marketTotal;

      const row = document.createElement("tr");
      
      // Change pill
      let changePill = `<span class="price-change-pill neutral">0.00%</span>`;
      if (changePct > 0) {
        changePill = `<span class="price-change-pill positive">▲ +${changePct.toFixed(2)}%</span>`;
      } else if (changePct < 0) {
        changePill = `<span class="price-change-pill negative">▼ ${changePct.toFixed(2)}%</span>`;
      }

      // PnL pill
      let pnlDisplay = `<span style="color:var(--text-muted); font-family:'JetBrains Mono', monospace;">-</span>`;
      if (currentPrice) {
        const pnlColor = pnl >= 0 ? "var(--success)" : "var(--danger)";
        const pnlSign = pnl >= 0 ? "+" : "";
        pnlDisplay = `<div style="text-align:right;">
          <strong style="color:${pnlColor}; font-family:'JetBrains Mono', monospace;">${pnlSign}${formatMoney(pnl)}</strong>
          <div style="font-size:11px; color:${pnlColor};">${pnlSign}${pnlPct.toFixed(1)}%</div>
        </div>`;
      }

      row.innerHTML = `
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="ticker-tag" style="background:rgba(255,184,28,0.15); border-color:var(--border-gold); color:var(--oro-mayo);">${ticker}</span>
            <span style="font-size:11px; color:var(--text-muted); font-family:'JetBrains Mono', monospace;">${quote.symbol || ticker + '.BA'}</span>
          </div>
        </td>
        <td>
          <div style="font-weight:600; color:var(--text-primary);">${quote.name || h.description}</div>
          <span style="font-size:11px; color:var(--text-muted);">CEDEAR BYMA • Ratio Oficial</span>
        </td>
        <td>
          <span class="institution-pill inst-${(h.institution || '').toLowerCase().replace(/\s+/g, '')}">${h.institution}</span>
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace; font-weight:600;">
          ${qty.toLocaleString("es-AR")}
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace; color:var(--text-secondary);">
          ${formatMoney(bookUnit)}
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace;">
          ${currentPrice ? `<strong style="color:var(--cielo-light);">${formatMoney(currentPrice)}</strong>` : '<span style="color:var(--text-muted);">Sin cotiz.</span>'}
        </td>
        <td style="text-align:right;">
          ${changePill}
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace; font-weight:700;">
          ${formatMoney(marketTotal)}
        </td>
        <td>
          ${pnlDisplay}
        </td>
      `;
      tbodyHoldings.appendChild(row);
    });
  }

  // Update KPI Cards
  const totalPnL = totalMarketARS - totalBookARS;
  const totalPnLPct = totalBookARS > 0 ? ((totalPnL / totalBookARS) * 100) : 0;

  const kpiMarketEl = document.getElementById("cedear-kpi-market-val");
  const kpiBookEl = document.getElementById("cedear-kpi-book-val");
  const kpiPnlEl = document.getElementById("cedear-kpi-pnl");
  const kpiPnlSub = document.getElementById("cedear-kpi-pnl-sub");

  if (kpiMarketEl) kpiMarketEl.textContent = formatMoney(totalMarketARS);
  if (kpiBookEl) kpiBookEl.textContent = formatMoney(totalBookARS);
  if (kpiPnlEl) {
    const sign = totalPnL >= 0 ? "+" : "";
    kpiPnlEl.textContent = `${sign}${formatMoney(totalPnL)}`;
    kpiPnlEl.style.color = totalPnL >= 0 ? "var(--success)" : "var(--danger)";
  }
  if (kpiPnlSub) {
    const sign = totalPnL >= 0 ? "+" : "";
    kpiPnlSub.textContent = `${sign}${totalPnLPct.toFixed(2)}% sobre costo de adquisición`;
  }

  // 2. Render Historical Closed Trades & Realized PnL
  const tbodyTrades = document.getElementById("cedears-trades-tbody");
  if (tbodyTrades) {
    tbodyTrades.innerHTML = "";
    
    // Group boletos by ticker and number to avoid duplicates
    const seenBoletoKeys = new Set();
    const tickerTrades = {};

    movements.forEach(m => {
      const desc = String(m.description || "");
      if (desc.includes("Boleto /")) {
        const parts = desc.split("/").map(p => p.trim());
        if (parts.length >= 5) {
          const num = parts[1];
          const op = parts[2].toUpperCase(); // CPRA or VENTA
          const ticker = parts[4].toUpperCase();
          const key = `${num}_${op}`;

          if (seenBoletoKeys.has(key)) return;
          seenBoletoKeys.add(key);

          if (!tickerTrades[ticker]) {
            tickerTrades[ticker] = { buys: [], sells: [] };
          }

          const rawAmount = Math.abs(Number(m.amount) || 0);
          if (op.includes("CPRA") || op.includes("COMPRA")) {
            tickerTrades[ticker].buys.push({
              date: m.date,
              amount: rawAmount,
              ticketNum: num,
              desc: desc
            });
          } else if (op.includes("VENTA")) {
            tickerTrades[ticker].sells.push({
              date: m.date,
              amount: rawAmount,
              ticketNum: num,
              desc: desc
            });
          }
        }
      }
    });

    // Pair and render each closed trade or position
    Object.keys(tickerTrades).sort().forEach(ticker => {
      const data = tickerTrades[ticker];
      const totalBuys = data.buys.reduce((sum, b) => sum + b.amount, 0);
      const totalSells = data.sells.reduce((sum, s) => sum + s.amount, 0);

      const isClosed = data.buys.length > 0 && data.sells.length > 0;
      const isOnlySold = data.buys.length === 0 && data.sells.length > 0; // e.g. GOOGL bought in earlier year
      const isStillOpen = data.buys.length > 0 && data.sells.length === 0; // e.g. IBIT, COIN

      // Dates summary
      const buyDates = data.buys.map(b => b.date).filter(Boolean).join(", ") || "-";
      const sellDates = data.sells.map(s => s.date).filter(Boolean).join(", ") || "-";

      let statusBadge = `<span class="badge-tag badge-success">Cerrado (Ganancia)</span>`;
      let pnlDisplay = `<span style="color:var(--text-muted);">-</span>`;
      let pctDisplay = `<span style="color:var(--text-muted);">-</span>`;

      if (isClosed) {
        const pnl = totalSells - totalBuys;
        const pnlPct = totalBuys > 0 ? ((pnl / totalBuys) * 100) : 0;
        const pnlColor = pnl >= 0 ? "var(--success)" : "var(--danger)";
        const pnlSign = pnl >= 0 ? "+" : "";
        statusBadge = pnl >= 0 
          ? `<span class="badge-tag badge-success">Trade Cerrado (Ganancia)</span>`
          : `<span class="badge-tag badge-danger">Trade Cerrado (Pérdida)</span>`;
        
        pnlDisplay = `<strong style="color:${pnlColor}; font-family:'JetBrains Mono', monospace;">${pnlSign}${formatMoney(pnl)}</strong>`;
        pctDisplay = `<span class="price-change-pill ${pnl >= 0 ? 'positive' : 'negative'}">${pnlSign}${pnlPct.toFixed(2)}%</span>`;
      } else if (isOnlySold) {
        statusBadge = `<span class="badge-tag badge-cielo">Venta de Custodia Previa</span>`;
        pnlDisplay = `<strong style="color:var(--success); font-family:'JetBrains Mono', monospace;">Cobrado: ${formatMoney(totalSells)}</strong>`;
        pctDisplay = `<span style="font-size:11px; color:var(--text-muted);">Sin compra previa en extracto</span>`;
      } else if (isStillOpen) {
        statusBadge = `<span class="badge-tag badge-gold">Posición Abierta (En Cartera)</span>`;
        pnlDisplay = `<span style="font-size:12px; color:var(--text-muted);">Ver P&L en vivo arriba</span>`;
        pctDisplay = `<span style="font-size:11px; color:var(--text-muted);">-</span>`;
      }

      const row = document.createElement("tr");
      row.innerHTML = `
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="ticker-tag" style="background:rgba(255,184,28,0.15); border-color:var(--border-gold); color:var(--oro-mayo);">${ticker}</span>
            <span style="font-weight:700; color:var(--text-primary); font-size:13px;">${ticker}</span>
          </div>
        </td>
        <td>
          ${statusBadge}
        </td>
        <td style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--text-secondary);">
          ${buyDates}
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace; font-weight:600;">
          ${totalBuys > 0 ? formatMoney(totalBuys) : '<span style="color:var(--text-muted);">-</span>'}
        </td>
        <td style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--text-secondary);">
          ${sellDates}
        </td>
        <td style="text-align:right; font-family:'JetBrains Mono', monospace; font-weight:600;">
          ${totalSells > 0 ? formatMoney(totalSells) : '<span style="color:var(--text-muted);">-</span>'}
        </td>
        <td style="text-align:right;">
          ${pnlDisplay}
        </td>
        <td style="text-align:right;">
          ${pctDisplay}
        </td>
      `;
      tbodyTrades.appendChild(row);
    });
  }
}

