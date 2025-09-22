# strings.json - UI Translations

```json
{
  "config": {
    "flow_title": "Oura Ring Integration",
    "step": {
      "user": {
        "title": "Choose Authentication Method",
        "description": "Select how you want to connect to your Oura Ring",
        "data": {
          "auth_type": "Authentication Type"
        },
        "data_description": {
          "auth_type": "Personal Access Token is simpler, OAuth2 is more secure and future-proof"
        }
      },
      "pat": {
        "title": "Personal Access Token",
        "description": "Enter your Oura personal access token. You can get one from {token_url}",
        "data": {
          "token": "Personal Access Token",
          "name": "Device Name"
        },
        "data_description": {
          "token": "Your Oura API personal access token",
          "name": "Name for this Oura Ring device in Home Assistant"
        }
      },
      "oauth2_init": {
        "title": "OAuth2 Configuration",
        "description": "Enter your OAuth2 application credentials",
        "data": {
          "client_id": "Client ID",
          "client_secret": "Client Secret"
        }
      },
      "features": {
        "title": "Configure Features",
        "description": "Set up integration features for {user_email} (Ring Gen {ring_generation})",
        "data": {
          "scan_interval": "Update Interval (minutes)",
          "enable_ai_insights": "Enable AI Insights",
          "enable_mqtt_bridge": "Enable MQTT Bridge",
          "enable_webhooks": "Enable Webhooks",
          "mqtt_topic_prefix": "MQTT Topic Prefix"
        },
        "data_description": {
          "scan_interval": "How often to fetch new data from Oura API",
          "enable_ai_insights": "Generate AI-powered wellness insights",
          "enable_mqtt_bridge": "Publish data to MQTT for ecosystem integration",
          "enable_webhooks": "Enable real-time updates via webhooks",
          "mqtt_topic_prefix": "Base topic for MQTT messages"
        }
      },
      "reauth_confirm": {
        "title": "Re-authenticate Oura",
        "description": "Your Oura token has expired for {user_email}. Please enter a new token.",
        "data": {
          "token": "New Personal Access Token"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid authentication - please check your token",
      "cannot_connect": "Failed to connect to Oura API",
      "unknown": "Unexpected error occurred",
      "already_configured": "This Oura account is already configured"
    },
    "abort": {
      "already_configured": "Device is already configured",
      "reauth_successful": "Re-authentication was successful",
      "oauth_error": "OAuth2 authentication failed"
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Oura Integration Options",
        "description": "Configure how the Oura integration works",
        "data": {
          "scan_interval": "Update Interval (minutes)",
          "enable_ai_insights": "Enable AI Insights",
          "enable_mqtt_bridge": "Enable MQTT Bridge",
          "enable_webhooks": "Enable Webhooks",
          "mqtt_topic_prefix": "MQTT Topic Prefix",
          "api_base_url": "API Base URL",
          "enable_debug_logging": "Enable Debug Logging",
          "data_retention_days": "Data Retention (days)"
        },
        "data_description": {
          "scan_interval": "How often to fetch new data from Oura API (5-60 minutes)",
          "enable_ai_insights": "Use AI to generate personalized wellness insights",
          "enable_mqtt_bridge": "Publish Oura data to MQTT for integration with other systems",
          "enable_webhooks": "Enable real-time data updates via webhooks (requires public URL)",
          "mqtt_topic_prefix": "Base MQTT topic for publishing data",
          "api_base_url": "Oura API endpoint (advanced users only)",
          "enable_debug_logging": "Enable detailed debug logging",
          "data_retention_days": "How many days of historical data to keep"
        }
      }
    }
  },
  "entity": {
    "sensor": {
      "sleep_score": {
        "name": "Sleep Score"
      },
      "sleep_total_hours": {
        "name": "Total Sleep"
      },
      "sleep_efficiency": {
        "name": "Sleep Efficiency"
      },
      "sleep_rem_hours": {
        "name": "REM Sleep"
      },
      "sleep_deep_hours": {
        "name": "Deep Sleep"
      },
      "readiness_score": {
        "name": "Readiness Score"
      },
      "activity_steps": {
        "name": "Steps"
      },
      "hrv_average": {
        "name": "Average HRV"
      },
      "temperature_deviation": {
        "name": "Temperature Deviation"
      },
      "wellness_phase": {
        "name": "Wellness Phase"
      },
      "optimal_bedtime": {
        "name": "Optimal Bedtime"
      }
    },
    "binary_sensor": {
      "in_bed": {
        "name": "In Bed"
      },
      "sleeping": {
        "name": "Sleeping"
      },
      "activity_goal_met": {
        "name": "Activity Goal Met"
      },
      "recovery_needed": {
        "name": "Recovery Needed"
      },
      "high_stress": {
        "name": "High Stress"
      }
    },
    "select": {
      "wellness_phase_override": {
        "name": "Wellness Phase Override",
        "state": {
          "auto": "Automatic",
          "recovery": "Recovery",
          "maintenance": "Maintenance",
          "challenge": "Challenge",
          "peak": "Peak Performance"
        }
      },
      "automation_mode": {
        "name": "Automation Mode",
        "state": {
          "disabled": "Disabled",
          "minimal": "Minimal",
          "balanced": "Balanced",
          "full": "Full"
        }
      }
    }
  },
  "services": {
    "refresh_data": {
      "name": "Refresh Data",
      "description": "Force refresh of Oura data from the API",
      "fields": {
        "include_historical": {
          "name": "Include Historical",
          "description": "Fetch historical data for the past 7 days"
        },
        "data_types": {
          "name": "Data Types",
          "description": "Specific data types to refresh (leave empty for all)"
        }
      }
    },
    "get_wellness_insight": {
      "name": "Get Wellness Insight",
      "description": "Generate AI-powered wellness insight",
      "fields": {
        "insight_type": {
          "name": "Insight Type",
          "description": "Type of insight to generate"
        },
        "context_days": {
          "name": "Context Days",
          "description": "Days of historical data to analyze"
        },
        "personalized": {
          "name": "Personalized",
          "description": "Include personalized recommendations"
        }
      }
    },
    "set_wellness_mode": {
      "name": "Set Wellness Mode",
      "description": "Override automatic wellness phase detection",
      "fields": {
        "mode": {
          "name": "Mode",
          "description": "Wellness mode to activate"
        },
        "duration_hours": {
          "name": "Duration",
          "description": "How long to maintain this mode"
        },
        "custom_settings": {
          "name": "Custom Settings",
          "description": "JSON configuration for custom mode"
        }
      }
    },
    "export_wellness_data": {
      "name": "Export Data",
      "description": "Export Oura data for analysis",
      "fields": {
        "format": {
          "name": "Format",
          "description": "Export file format"
        },
        "date_range": {
          "name": "Date Range",
          "description": "Days of data to export"
        },
        "data_types": {
          "name": "Data Types",
          "description": "Types of data to include"
        },
        "destination": {
          "name": "Destination",
          "description": "Where to save the export"
        }
      }
    },
    "trigger_recovery_protocol": {
      "name": "Trigger Recovery",
      "description": "Activate recovery-focused automations",
      "fields": {
        "protocol_level": {
          "name": "Protocol Level",
          "description": "Intensity of recovery protocol"
        },
        "components": {
          "name": "Components",
          "description": "Recovery components to activate"
        },
        "duration_hours": {
          "name": "Duration",
          "description": "How long to maintain recovery mode"
        }
      }
    }
  },
  "selector": {
    "auth_type": {
      "options": {
        "pat": "Personal Access Token",
        "oauth2": "OAuth2 (Recommended)"
      }
    },
    "insight_type": {
      "options": {
        "sleep_optimization": "Sleep Optimization",
        "recovery_plan": "Recovery Plan",
        "activity_recommendation": "Activity Recommendation",
        "stress_management": "Stress Management",
        "circadian_alignment": "Circadian Alignment"
      }
    },
    "wellness_mode": {
      "options": {
        "recovery": "Recovery",
        "maintenance": "Maintenance",
        "challenge": "Challenge",
        "peak": "Peak Performance",
        "custom": "Custom"
      }
    },
    "recovery_level": {
      "options": {
        "light": "Light Recovery",
        "moderate": "Moderate Recovery",
        "intensive": "Intensive Recovery"
      }
    }
  }
}
```
