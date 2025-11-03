# Problem Statement

### GreenOps for Automotive Manufacturing Sustainability

1. Automotive manufacturing is energy-intensive
2. You understand the domain deeply (authentic problem-solving)
3. No NDA issues (using synthetic but realistic data)

#### Problem: Automotive manufacturing plants operate:

- Paint shops (massive energy consumers - 40% of plant energy)
- Body shops (welding robots, ventilation)
- Assembly lines (conveyors, tools, lighting)
- HVAC systems (climate control for precision work)
- Compressed air systems (pneumatic tools)
- Battery
- Casting

#### Challenges:

- Energy consumption spikes go unnoticed until monthly bills
- Equipment inefficiencies (air leaks, aging compressors) waste 20-30% energy
- No real-time visibility into production vs energy efficiency
- Manual sustainability reporting takes weeks
- Difficult to meet carbon neutrality goals without AI insights

### Benchmark

| **Zone**                             | **Description**                              | **Typical Energy Load** |
| ------------------------------------ | -------------------------------------------- | ----------------------- |
| Paint Shop                           | Paint application, curing ovens, ventilation | 35–45% of plant energy  |
| Body Shop                            | Welding, metal stamping, robots              | 20–30%                  |
| Assembly Shop                        | Conveyors, torque tools, lighting            | 15–20%                  |
| Casting Shop                         | Die-casting of aluminum components           | 10–15%                  |
| Battery Shop                         | Cell/module assembly, conditioning           | 5–10%                   |
| HVAC & Utilities Zone                | Central climate control, compressed air      | 5–10%                   |
| (optional) Testing & Inspection Area | End-of-line dynamometer tests                | 3–5%                    |

### KPI

| **KPI**                       | **Formula**                                              | **Unit**    | **Description**                                |
| ----------------------------- | -------------------------------------------------------- | ----------- | ---------------------------------------------- |
| Energy per Vehicle            | Total energy consumed (kWh) ÷ Vehicles produced          | kWh/vehicle | Core measure of production energy efficiency.  |
| CO₂ per Vehicle               | Total CO₂ emitted (kg) ÷ Vehicles produced               | kg/vehicle  | Carbon intensity per output unit.              |
| Zone Energy Share             | (Energy of zone ÷ Total energy) × 100                    | %           | Helps identify energy-dominant shops.          |
| Energy Intensity (Plant-wide) | Total energy (kWh) ÷ Total floor area (m²)               | kWh/m²      | Standard facility benchmark.                   |
| Renewable Energy Share        | (Renewable energy used ÷ Total energy) × 100             | %           | Indicates green energy adoption.               |
| Idle Energy %                 | (Energy used during non-production hours ÷ Total energy) | %           | Quantifies energy wasted during downtime.      |
| Compressed Air Efficiency     | Actual flow (m³/min) ÷ Rated flow                        | Ratio       | Detects air leaks and compressor inefficiency. |
| HVAC Energy per Area          | HVAC energy ÷ Conditioned area                           | kWh/m²      | Monitors climate-control performance.          |
| Water Consumption per Vehicle | Total water (liters) ÷ Vehicles produced                 | L/vehicle   | Paint and cleaning operations.                 |

### ⚡ Zone-Specific Operational Metrics

### 1. Paint Shop

- **Metrics:**
  - `energy_kwh_paint`
  - `oven_temperature_c`
  - `booth_airflow_m3h`
  - `paint_usage_liters`
  - `water_recycle_ratio`
- **KPIs:**
  - Energy per car painted
  - Oven idle energy %
  - CO₂ per m² body area painted

---

### 2. Body Shop

- **Metrics:**
  - `robot_runtime_hours`
  - `compressed_air_m3`
  - `spot_welds_count`
  - `energy_per_weld_kwh`
- **KPIs:**
  - Energy per weld
  - CO₂ per weld sequence

---

### 3. Assembly Shop

- **Metrics:**
  - `conveyor_runtime_hours`
  - `tool_energy_kwh`
  - `lighting_energy_kwh`
- **KPIs:**
  - Energy per assembled vehicle
  - Idle tool energy %

---

### 4. Casting Shop

- **Metrics:**
  - `furnace_energy_kwh`
  - `molten_temp_c`
  - `cooling_water_liters`
- **KPIs:**
  - Energy per kg aluminum cast
  - Furnace efficiency

---

### 5. Battery Shop

- **Metrics:**
  - `cell_formation_energy_kwh`
  - `cleanroom_hvac_energy_kwh`
- **KPIs:**
  - Energy per kWh battery produced
  - CO₂ per pack

