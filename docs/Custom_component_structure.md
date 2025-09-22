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