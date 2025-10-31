import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
 
# Simulation setup
start_date = datetime(2025, 10, 27, 0, 0)
hours = 168  # one week
shifts = ["SHIFT-A", "SHIFT-B", "SHIFT-C"]
 
zones = {
    "ZONE-PAINT-SHOP": {"base_energy": (2000, 4000), "uses_air": True, "uses_water": True},
    "ZONE-BODY-SHOP": {"base_energy": (1000, 2500), "uses_air": True, "uses_water": False},
    "ZONE-ASSEMBLY": {"base_energy": (800, 1800), "uses_air": True, "uses_water": False},
    "ZONE-CASTING": {"base_energy": (1500, 3000), "uses_air": False, "uses_water": True},
    "ZONE-BATTERY": {"base_energy": (700, 1500), "uses_air": False, "uses_water": False},
    "ZONE-HVAC-UTILITIES": {"base_energy": (500, 1000), "uses_air": False, "uses_water": False}
}
 
records = []
 
for hour in range(hours):
    timestamp = start_date + timedelta(hours=hour)
    shift = shifts[(hour // 8) % 3]
 
    for zone, zdata in zones.items():
        # Random energy consumption
        energy = random.uniform(*zdata["base_energy"])
        
        # Production pattern: day shifts have production, night less
        if shift == "SHIFT-C":
            production = random.randint(0, 10)
        else:
            production = random.randint(15, 30)
        
        # Paint ovens sometimes run idle at night
        if zone == "ZONE-PAINT-SHOP" and shift == "SHIFT-C" and random.random() < 0.4:
            energy *= 1.3  # inefficiency spike
            production = 0
        
        # CO2 emission
        co2 = energy * 0.82
        
        # Compressed air
        air = random.uniform(500, 2000) if zdata["uses_air"] else 0
        if production == 0:
            air *= random.uniform(0.5, 1.0)
        
        # Water usage
        water = random.uniform(200, 800) if zdata["uses_water"] else 0
        
        # Temperature logic
        temperature = random.uniform(18, 28)
        if zone == "ZONE-PAINT-SHOP":
            temperature = random.uniform(60, 180)  # oven
        elif zone == "ZONE-CASTING":
            temperature = random.uniform(100, 300)
        
        # Efficiency score (higher = better)
        baseline_energy_per_unit = 1200
        actual_energy_per_unit = energy / (production if production > 0 else 1)
        efficiency = round(min(1.0, baseline_energy_per_unit / actual_energy_per_unit), 2)
        
        status = "OPERATIONAL" if production > 0 else "STANDBY"
        
        records.append([
            timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            zone,
            round(energy, 2),
            round(co2, 2),
            production,
            round(air, 2),
            round(water, 2),
            round(temperature, 1),
            shift,
            efficiency,
            status
        ])
 
# Create DataFrame
cols = ["timestamp", "zone_id", "energy_kwh", "co2_kg", "production_units",
        "compressed_air_m3", "water_liters", "temperature_c", "shift",
        "efficiency_score", "status"]
 
df = pd.DataFrame(records, columns=cols)
 
# Compute zone energy share
total_energy = df["energy_kwh"].sum()
zone_share = df.groupby("zone_id")["energy_kwh"].sum() / total_energy * 100
df["zone_energy_share_%"] = df["zone_id"].map(zone_share.round(2))
 
# Save to CSV
df.to_csv("automotive_energy_data.csv", index=False)
 
print("✅ Synthetic dataset generated: automotive_energy_data.csv")
print(df.head(10))
 