# 💼 Consolidador Financiero & Dashboard Patrimonial Personal

Sistema integral para el procesamiento, análisis y consolidación patrimonial multi-entidad de cuentas personales e inversiones (Bancos, Billeteras Virtuales, Brokers / ALyCs y Custodias de Valores).

---

## 🚀 Características Principales

- **Multi-Entidad y Detección Automática**:
  - **Banco Galicia**: Procesa reportes impositivos y consolidados Excel (`.xlsx`), extrayendo cajas de ahorro, cuentas corrientes, deudas de tarjeta, plazos fijos vigentes y resultados anuales con tasas e intereses devengados, y más de 150 movimientos bancarios.
  - **Balanz Capital**: Procesa el PDF de *Posición Consolidada por Concertación*, extrayendo carteras en Obligaciones Negociables (ONs corporativas), Bonos Soberanos (AL30), CEDEARs, Fondos y saldos líquidos en Pesos, USD MEP y USD Cable con cotizaciones oficiales.
  - **Mercado Pago**: Procesa reportes anuales de tenencia y rendimientos en PDF, calculando dinero disponible remunerado en FCI BIND, reservas, valor de cuotaparte y rendimientos anuales acumulados.
  - **Ualá Inversiones & Caja de Valores**: Procesa resúmenes de custodia y estados de cuenta, extrayendo tenencias de bonos (AL30, GD38), CEDEARs (Bitcoin Trust IBIT, Coinbase COIN), acciones locales (Ternium TXAR), Fondos Comunes Ualintec y cientos de movimientos bursátiles.
- **Dashboard Web Interactivo**:
  - Interfaz oscura moderna con diseño de alta gama y acentos visuales púrpura/violeta.
  - Indicadores clave (KPIs) en tiempo real: Patrimonio Neto Total (ARS & USD MEP), Liquidez Inmediata, Total Invertido, Rendimientos Generados y Deuda.
  - Gráficos interactivos de distribución por Institución y por Clase de Activo.
  - Filtro interactivo por entidad con un solo click.
  - Búsqueda en tiempo real y filtrado de más de 40 tenencias y más de 360 movimientos categorizados.
  - Switcher de moneda instantáneo (ARS / USD).
  - Botón de actualización en vivo (`Re-procesar Input`) para incorporar nuevos extractos al instante.
- **Exportación Ejecutiva a Excel**:
  - Genera automáticamente `output/Patrimonio_Consolidado_Alejandro.xlsx` con pestañas estilizadas: *Resumen Ejecutivo*, *Tenencias y Portafolio*, *Saldos Monetarios*, *Movimientos y Transacciones* y *Plazos Fijos Vigentes*.

---

## 📂 Estructura del Proyecto

```
financial-transaction-processor/
├── input/                          # Archivos de entrada consolidados (Excel y PDF)
├── output/                         # Reportes generados (Excel profesional consolidado)
├── src/
│   ├── models.py                   # Dataclasses tipadas (Holding, Balance, Transaction, etc.)
│   ├── classifier.py               # Clasificador inteligente de conceptos financieros
│   ├── consolidator.py             # Motor central de consolidación multi-entidad
│   ├── exporter.py                 # Exportador a Excel ejecutivo profesional
│   └── extractors/
│       ├── base_extractor.py       # Clase base e interfaz común
│       ├── galicia_extractor.py    # Extractor para Banco Galicia
│       ├── balanz_extractor.py     # Extractor para Balanz Capital
│       ├── mercadopago_extractor.py# Extractor para Mercado Pago
│       └── uala_extractor.py       # Extractor para Ualá Inversiones y Caja de Valores
├── web/                            # Frontend Web Dashboard moderno
│   ├── index.html                  # Dashboard SPA interactivo
│   ├── css/
│   │   └── dashboard.css           # Estilos de alta fidelidad (glassmorphism dark)
│   └── js/
│       └── app.js                  # Lógica de dashboard, Chart.js y filtros en vivo
├── dashboard_server.py             # Servidor HTTP local con API REST
├── main.py                         # CLI principal del proyecto
└── requirements.txt                # Dependencias de Python
```

---

## 🛠️ Cómo Utilizar el Proyecto

### 1. Consolidar y Generar Reporte Excel (CLI)
```bash
python main.py
```
Analiza los archivos de `input/`, imprime el resumen consolidado en la terminal y genera el reporte en `output/Patrimonio_Consolidado_Alejandro.xlsx`.

### 2. Iniciar el Dashboard Web
```bash
python main.py --dashboard
```
O directamente:
```bash
python dashboard_server.py
```
Abre automáticamente tu navegador en `http://localhost:8050`.
