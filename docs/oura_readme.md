# Oura Ring Integration for Home Assistant

A comprehensive Home Assistant integration for the Oura Ring that provides complete access to all health metrics, AI-powered insights, and advanced automation capabilities.

## Features

### 📊 Complete Data Access
- **Sleep Metrics**: Score, stages (REM/Deep/Light), efficiency, HRV, heart rate, temperature
- **Readiness Data**: Score, temperature deviation, HRV balance, recovery metrics
- **Activity Tracking**: Steps, calories, intensity levels, workout detection
- **Physiological Data**: Heart rate, HRV, SpO2, stress levels, respiratory rate
- **Wellness Intelligence**: Circadian alignment, wellness phases, trend analysis

### 🤖 AI-Powered Features
- Personalized wellness insights
- Predictive readiness forecasting
- Sleep optimization recommendations
- Recovery protocol suggestions
- Activity recommendations based on readiness

### 🏠 Smart Home Automations
- Circadian lighting control
- Temperature optimization for sleep
- Recovery-based scene activation
- Stress response automations
- Activity reminders

### 🔧 Advanced Capabilities
- MQTT bridge for ecosystem integration
- Data export (CSV, JSON, InfluxDB)
- Webhook support for real-time updates
- Custom automation blueprints
- Multi-user support

## Installation

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the "+" button
4. Search for "Oura Ring"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the `oura_full` folder from this repository
2. Copy it to your `custom_components` directory:
   ```
   /config/custom_components/oura_full/
   ```
3. Restart Home Assistant

## Configuration

### Step 1: Get Your Oura Personal Access Token

1. Visit [Oura Cloud](https://cloud.ouraring.com/personal-access-tokens)
2. Click "Create New Personal Access Token"
3. Copy the generated token

### Step 2: Add Integration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Oura Ring"
4. Select authentication method (Personal Access Token recommended)
5. Enter your token
6. Configure features:
   - **Update Interval**: How often to fetch data (5-60 minutes)
   - **AI Insights**: Enable for personalized recommendations
   - **MQTT Bridge**: Enable for ecosystem integration
   - **Webhooks**: Enable for real-time updates

### Step 3: Configure Dashboard

Add the provided dashboard cards to your Lovelace UI:

```yaml
# Example dashboard card
type: custom:mushroom-template-card
entity: sensor.oura_readiness_score
primary: "Readiness: {{ states('sensor.oura_readiness_score') }}%"
secondary: "{{ state_attr('sensor.oura_readiness_score', 'recommendation') }}"
icon: mdi:heart-pulse
icon_color: >
  {% set score = states('sensor.oura_readiness_score') | int %}
  {% if score > 85 %} green
  {% elif score > 70 %} orange
  {% else %} red
  {% endif %}
```

## Entities

### Sensors
- `sensor.oura_sleep_score` - Overall sleep quality (0-100)
- `sensor.oura_sleep_total_hours` - Total sleep duration
- `sensor.oura_readiness_score` - Recovery readiness (0-100)
- `sensor.oura_activity_steps` - Daily step count
- `sensor.oura_hrv_average` - Heart rate variability
- `sensor.oura_wellness_phase` - Current wellness phase
- And many more...

### Binary Sensors
- `binary_sensor.oura_in_bed` - Currently in bed
- `binary_sensor.oura_sleeping` - Currently sleeping
- `binary_sensor.oura_recovery_needed` - Recovery recommended
- `binary_sensor.oura_high_stress` - Stress level elevated
- And more...

### Select Entities
- `select.oura_wellness_phase_override` - Manual wellness mode
- `select.oura_automation_mode` - Automation intensity
- `select.oura_notification_preference` - Alert settings

## Services

### `oura_full.refresh_data`
Force refresh data from Oura API.

```yaml
service: oura_full.refresh_data
data:
  include_historical: true
  data_types:
    - sleep
    - readiness
```

### `oura_full.get_wellness_insight`
Generate AI-powered wellness insights.

```yaml
service: oura_full.get_wellness_insight
data:
  insight_type: sleep_optimization
  context_days: 7
  personalized: true
```

### `oura_full.trigger_recovery_protocol`
Activate recovery-focused automations.

```yaml
service: oura_full.trigger_recovery_protocol
data:
  protocol_level: moderate
  components:
    - lighting
    - temperature
    - notifications
  duration_hours: 8
```

### `oura_full.export_wellness_data`
Export data for analysis.

```yaml
service: oura_full.export_wellness_data
data:
  format: csv
  date_range: 30
  destination: /config/exports/oura_data
```

## Automation Examples

### Sleep Detection
```yaml
automation:
  - alias: "Oura Sleep Mode"
    trigger:
      - platform: state
        entity_id: binary_sensor.oura_in_bed
        to: "on"
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.sleep_mode
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom
        data:
          temperature: 68
```

### Readiness-Based Morning Routine
```yaml
automation:
  - alias: "Adaptive Morning Routine"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.oura_readiness_score
        below: 70
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness_pct: 30
          transition: 900  # 15 minutes
      - service: notify.mobile
        data:
          message: "Low readiness detected. Take it easy today!"
```

### Circadian Lighting
```yaml
automation:
  - alias: "Circadian Rhythm Lighting"
    trigger:
      - platform: time_pattern
        minutes: "/10"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          kelvin: >
            {% set hour = now().hour %}
            {% if hour < 6 %} 2000
            {% elif hour < 12 %} 5500
            {% elif hour < 18 %} 6500
            {% elif hour < 21 %} 3500
            {% else %} 2200
            {% endif %}
```

## MQTT Integration

If MQTT bridge is enabled, data is published to:

```
anima/wellness/oura/sleep/score
anima/wellness/oura/readiness/score
anima/wellness/oura/activity/steps
anima/wellness/oura/wellness/phase
anima/wellness/oura/circadian/score
```

Subscribe to these topics in Node-RED or other MQTT clients for advanced automations.

## Troubleshooting

### Authentication Issues
- Ensure your Personal Access Token is valid
- Token expires after 2 years - regenerate if needed
- Check Oura API status at [status.ouraring.com](https://status.ouraring.com)

### No Data Appearing
- Wait for the first update interval to complete
- Check logs: Settings → System → Logs → Search "oura_full"
- Verify network connectivity to api.ouraring.com

### Rate Limiting
- Default update interval is 15 minutes to avoid rate limits
- Oura API allows 5000 requests per day
- Reduce update frequency if seeing rate limit errors

## Advanced Configuration

### Custom Wellness Phases
```yaml
service: oura_full.set_wellness_mode
data:
  mode: custom
  duration_hours: 48
  custom_settings: |
    {
      "sleep_target": 9,
      "activity_level": "low",
      "stress_management": true
    }
```

### InfluxDB Export
```yaml
# Configure InfluxDB first in configuration.yaml
influxdb:
  host: localhost
  database: homeassistant
  
# Then export Oura data
service: oura_full.export_wellness_data
data:
  format: influxdb
  date_range: 365
```

## Privacy & Security

- All data is processed locally
- Personal Access Tokens are encrypted
- MQTT messages can be configured with TLS
- No data is sent to third parties
- AI insights are generated locally (if configured)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ha-oura-full/issues)
- **Discussions**: [Home Assistant Community](https://community.home-assistant.io)
- **Documentation**: [Wiki](https://github.com/yourusername/ha-oura-full/wiki)

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Oura Health for their excellent API
- Home Assistant community for inspiration
- Contributors and testers

## Disclaimer

This is an unofficial integration and is not affiliated with Oura Health Ltd.
```
