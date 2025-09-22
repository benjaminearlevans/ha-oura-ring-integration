# Data flow pipeline
Oura API → Polling Service → MQTT Broker → Home Assistant → Automations
                  ↓
            Local Database (InfluxDB)
                  ↓
            Trend Analysis (AI Inference)


# Data Flow Pipeline
custom_components/oura_ring/
├── __init__.py          # Integration setup
├── manifest.json        # Component metadata
├── config_flow.py       # UI configuration
├── const.py            # Constants
├── coordinator.py      # Data update coordinator
├── sensor.py           # Sensor entities
├── binary_sensor.py    # Binary sensors
└── services.yaml       # Custom services

# Key Services
oura_ring.refresh_data      # Force API update
oura_ring.get_sleep_insight # AI-generated insight
oura_ring.set_wellness_mode # Manual override mode
oura_ring.export_trends     # Export data for analysis

# MQTT TOPIC STRUCTURE
anima/wellness/oura/sleep/score
anima/wellness/oura/sleep/stages/deep
anima/wellness/oura/sleep/stages/rem
anima/wellness/oura/sleep/hrv/average
anima/wellness/oura/readiness/score
anima/wellness/oura/readiness/temperature
anima/wellness/oura/activity/steps
anima/wellness/oura/activity/calories
anima/wellness/oura/realtime/heart_rate
anima/wellness/oura/trends/weekly