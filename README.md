# Oura Ring Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A comprehensive Home Assistant integration for the Oura Ring API v2 that provides complete access to all biometric data, enables advanced automations, and delivers a seamless user experience.

## Features

### 🔗 **Complete API Coverage**
- **Sleep Data**: Sleep score, stages (REM, Deep, Light), efficiency, HRV, respiratory rate
- **Readiness Data**: Readiness score, temperature deviation, HRV balance, recovery metrics
- **Activity Data**: Steps, calories, MET minutes, activity levels, workout detection
- **Heart Rate**: Resting HR, average HR, heart rate variability
- **Stress & Recovery**: Daily stress scores, recovery recommendations
- **SpO2**: Blood oxygen saturation levels
- **Workouts & Sessions**: Exercise tracking, meditation sessions

### 🏠 **85+ Home Assistant Entities**
- **40+ Sensors**: All biometric data with proper units and device classes
- **11 Binary Sensors**: In bed, sleeping, recovery needed, high stress, etc.
- **15 Switches**: Toggle automation features and wellness protocols
- **15 Number Inputs**: Configure thresholds and targets
- **15 Action Buttons**: Trigger recovery protocols and generate insights
- **5 Select Entities**: Control wellness phases and automation modes

### 🤖 **Advanced Automation Features**
- **Wellness Phase Detection**: Automatic recovery/maintenance/challenge/peak phase calculation
- **Circadian Optimization**: Sleep schedule analysis and recommendations
- **Recovery Protocols**: Multi-level recovery automation (light/moderate/intensive)
- **Stress Response**: Automatic stress detection and mitigation protocols
- **Activity Motivation**: Inactivity alerts and movement encouragement
- **Nap Intelligence**: Optimal nap timing based on sleep debt

### 🔄 **Real-time & Integration**
- **Webhook Support**: Instant updates when new data is available
- **MQTT Bridge**: Publish data to MQTT for ecosystem integration
- **AI Insights**: Integration with Home Assistant's conversation agent
- **Data Export**: CSV, JSON, and InfluxDB export capabilities

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/benjaminearlevans/ha_oura_ring_integration`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Oura Ring" in the integration list and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the files to your `custom_components/oura_full/` directory
3. Restart Home Assistant
4. Go to Settings → Integrations → Add Integration
5. Search for "Oura Ring" and follow the setup process

## Configuration

### Authentication Options

#### Personal Access Token (Recommended for personal use)
1. Go to [Oura Cloud](https://cloud.ouraring.com/personal-access-tokens)
2. Generate a new Personal Access Token
3. Copy the token and use it during integration setup

#### OAuth2 (Recommended for shared/production use)
1. Create an OAuth2 application at [Oura Developer Portal](https://cloud.ouraring.com/oauth/applications)
2. Use the Client ID and Client Secret during integration setup
3. Complete the OAuth2 authorization flow

### Integration Setup

1. Go to Settings → Integrations → Add Integration
2. Search for "Oura Ring"
3. Choose your authentication method (PAT or OAuth2)
4. Enter your credentials
5. Configure optional features:
   - AI Insights (requires conversation integration)
   - MQTT Bridge (requires MQTT integration)
   - Webhooks (requires external URL)
   - Polling interval (5-120 minutes)

## Usage Examples

### Basic Automation Examples

#### Morning Routine Based on Sleep Quality
```yaml
automation:
  - alias: "Good Sleep Morning Routine"
    trigger:
      - platform: numeric_state
        entity_id: sensor.oura_sleep_score
        above: 80
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness_pct: 100
          color_temp: 250
      - service: media_player.play_media
        target:
          entity_id: media_player.bedroom_speaker
        data:
          media_content_id: "energetic_playlist"
```

#### Recovery Protocol Trigger
```yaml
automation:
  - alias: "Auto Recovery Mode"
    trigger:
      - platform: numeric_state
        entity_id: sensor.oura_readiness_score
        below: 60
    action:
      - service: button.press
        target:
          entity_id: button.oura_trigger_recovery_moderate
      - service: switch.turn_on
        target:
          entity_id: switch.oura_recovery_protocol_enabled
```

### Advanced Automation Scenarios

#### Circadian Lighting
```yaml
automation:
  - alias: "Circadian Lighting"
    trigger:
      - platform: time_pattern
        minutes: "/30"
    condition:
      - condition: state
        entity_id: switch.oura_circadian_optimization
        state: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          color_temp: >
            {% set bedtime = states('sensor.oura_optimal_bedtime') %}
            {% set now = now().hour %}
            {% if now < 6 %}
              500
            {% elif now > 20 %}
              400
            {% else %}
              250
            {% endif %}
```

### MQTT Integration

The integration publishes data to MQTT topics following this structure:
```
anima/wellness/oura/
├── sleep/
│   ├── score
│   ├── duration
│   └── stages/
│       ├── deep
│       ├── rem
│       └── light
├── readiness/
│   ├── score
│   └── temperature
├── activity/
│   ├── steps
│   ├── calories
│   └── score
└── wellness/
    ├── phase
    └── recommendation
```

## Services

The integration provides several services for advanced automation:

### `oura_full.refresh_data`
Force refresh of Oura data from the API.

### `oura_full.get_wellness_insight`
Generate AI-powered wellness insights.

### `oura_full.trigger_recovery_protocol`
Activate recovery-focused automations.

### `oura_full.export_wellness_data`
Export data for external analysis.

## Troubleshooting

### Common Issues

#### Authentication Errors
- Verify your Personal Access Token is valid
- Check that OAuth2 credentials are correct
- Ensure your Oura account has data available

#### Rate Limiting
- The integration respects Oura's 5000 requests/day limit
- Increase polling interval if you hit rate limits
- Use webhooks for real-time updates instead of frequent polling

#### Missing Data
- Some data types require specific Oura Ring generations
- Ensure your ring is synced with the Oura mobile app
- Check that data is available in the Oura mobile app first

### Debug Logging

Enable debug logging by adding this to your `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.oura_full: debug
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

### Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run tests: `pytest`
4. Run linting: `flake8` and `black`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Oura](https://ouraring.com/) for providing the comprehensive health API
- [Home Assistant](https://www.home-assistant.io/) community for the excellent platform
- All contributors who help improve this integration

## Support

- 🐛 [Report bugs][issues]
- 💡 [Request features][issues]
- 💬 [Community discussions][discussions]
- 📖 [Documentation][wiki]

---

**Disclaimer**: This integration is not officially affiliated with Oura Health Ltd. Oura Ring is a trademark of Oura Health Ltd.

[releases-shield]: https://img.shields.io/github/release/benjaminearlevans/ha_oura_ring_integration.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/benjaminearlevans/ha_oura_ring_integration.svg?style=for-the-badge
[commits]: https://github.com/benjaminearlevans/ha_oura_ring_integration/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/benjaminearlevans/ha_oura_ring_integration.svg?style=for-the-badge
[releases]: https://github.com/benjaminearlevans/ha_oura_ring_integration/releases
[issues]: https://github.com/benjaminearlevans/ha_oura_ring_integration/issues
[discussions]: https://github.com/benjaminearlevans/ha_oura_ring_integration/discussions
[wiki]: https://github.com/benjaminearlevans/ha_oura_ring_integration/wiki
