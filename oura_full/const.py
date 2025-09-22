"""Constants for the Oura ring integration."""
from datetime import timedelta

# Integration domain
DOMAIN = "oura_full"

# API Configuration
API_BASE_URL = "https://api.ouraring.com"
API_TIMEOUT = 30
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 2

# Configuration keys
CONF_AUTH_TYPE = "auth_type"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_TOKEN = "token"
CONF_WEBHOOK_ID = "webhook_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_WEBHOOKS = "enable_webhooks"
CONF_ENABLE_AI_INSIGHTS = "enable_ai_insights"
CONF_ENABLE_MQTT_BRIDGE = "enable_mqtt_bridge"
CONF_MQTT_TOPIC_PREFIX = "mqtt_topic_prefix"

# Default values
DEFAULT_SCAN_INTERVAL = 15  # minutes
DEFAULT_NAME = "Oura Ring"
DEFAULT_MQTT_TOPIC = "anima/wellness/oura"

# Update intervals
MIN_UPDATE_INTERVAL = timedelta(minutes=5)
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)
MAX_UPDATE_INTERVAL = timedelta(hours=1)

# Service names
SERVICE_REFRESH_DATA = "refresh_data"
SERVICE_GET_WELLNESS_INSIGHT = "get_wellness_insight"
SERVICE_SET_WELLNESS_MODE = "set_wellness_mode"
SERVICE_EXPORT_DATA = "export_wellness_data"
SERVICE_TRIGGER_RECOVERY = "trigger_recovery_protocol"
SERVICE_CREATE_AUTOMATION = "create_automation"

# Webhook events
EVENT_WEBHOOK_DATA = f"{DOMAIN}_webhook_data"
EVENT_WELLNESS_MODE_CHANGED = f"{DOMAIN}_wellness_mode_changed"
EVENT_RECOVERY_PROTOCOL = f"{DOMAIN}_recovery_protocol"

# Data keys
DATA_COORDINATOR = "coordinator"
DATA_API_CLIENT = "api_client"
DATA_USER_INFO = "user_info"
DATA_SERVICES = "services"
DATA_WEBHOOK_HANDLER = "webhook_handler"
DATA_MQTT_BRIDGE = "mqtt_bridge"

# Entity platforms
PLATFORMS = [
    "sensor",
    "binary_sensor",
    "select",
    "switch",
    "number",
    "button",
]

# Wellness phases
WELLNESS_PHASES = [
    "recovery",
    "maintenance",
    "challenge",
    "peak",
]

# Activity intensities
ACTIVITY_INTENSITIES = [
    "rest",
    "low",
    "medium",
    "high",
]

# Readiness levels
READINESS_LEVELS = [
    "low",
    "medium",
    "high",
    "optimal",
]

# Export formats
EXPORT_FORMATS = [
    "csv",
    "json",
    "influxdb",
]

# Recovery protocol levels
RECOVERY_LEVELS = [
    "light",
    "moderate",
    "intensive",
]

# Recovery components
RECOVERY_COMPONENTS = [
    "lighting",
    "temperature",
    "notifications",
    "calendar_blocking",
    "meditation_prompts",
]

# Insight types
INSIGHT_TYPES = [
    "sleep_optimization",
    "recovery_plan",
    "activity_recommendation",
    "stress_management",
    "circadian_alignment",
]

# MQTT topics structure
MQTT_TOPICS = {
    "sleep": {
        "score": "sleep/score",
        "duration": "sleep/duration",
        "efficiency": "sleep/efficiency",
        "stages": {
            "deep": "sleep/stages/deep",
            "rem": "sleep/stages/rem",
            "light": "sleep/stages/light",
        },
        "hrv": "sleep/hrv",
    },
    "readiness": {
        "score": "readiness/score",
        "temperature": "readiness/temperature",
        "hrv_balance": "readiness/hrv_balance",
    },
    "activity": {
        "steps": "activity/steps",
        "calories": "activity/calories",
        "score": "activity/score",
    },
    "wellness": {
        "phase": "wellness/phase",
        "recommendation": "wellness/recommendation",
    },
    "realtime": {
        "heart_rate": "realtime/heart_rate",
        "stress": "realtime/stress",
    },
}

# Attribute keys
ATTR_AI_INSIGHT = "ai_insight"
ATTR_CONTRIBUTORS = "contributors"
ATTR_QUALITY = "quality"
ATTR_LEVEL = "level"
ATTR_RECOMMENDATION = "recommendation"
ATTR_BEDTIME_START = "bedtime_start"
ATTR_BEDTIME_END = "bedtime_end"
ATTR_DAY = "day"
ATTR_TREND = "trend"
ATTR_DIRECTION = "direction"
ATTR_CHANGE = "change"

# Icon mappings
ICONS = {
    "sleep": "mdi:sleep",
    "readiness": "mdi:heart-pulse",
    "activity": "mdi:run",
    "heart_rate": "mdi:pulse",
    "temperature": "mdi:thermometer",
    "stress": "mdi:emoticon-stressed-outline",
    "workout": "mdi:dumbbell",
    "meditation": "mdi:meditation",
    "recovery": "mdi:restore",
    "wellness": "mdi:state-machine",
}

# Unit conversions
SECONDS_TO_HOURS = 3600
SECONDS_TO_MINUTES = 60
MILLISECONDS_TO_SECONDS = 1000

# Thresholds
READINESS_LOW_THRESHOLD = 60
READINESS_MEDIUM_THRESHOLD = 70
READINESS_HIGH_THRESHOLD = 85

SLEEP_POOR_THRESHOLD = 60
SLEEP_FAIR_THRESHOLD = 70
SLEEP_GOOD_THRESHOLD = 85

ACTIVITY_LOW_THRESHOLD = 50
ACTIVITY_MEDIUM_THRESHOLD = 70
ACTIVITY_HIGH_THRESHOLD = 85

HRV_LOW_THRESHOLD = 20
HRV_MEDIUM_THRESHOLD = 50
HRV_HIGH_THRESHOLD = 100

TEMPERATURE_DEVIATION_HIGH = 0.5
TEMPERATURE_DEVIATION_LOW = -0.5

# Cache settings
CACHE_EXPIRY_MINUTES = 5
MAX_CACHE_SIZE = 100

# Rate limiting
RATE_LIMIT_THRESHOLD = 10
RATE_LIMIT_WINDOW = 60  # seconds

# Historical data
DEFAULT_LOOKBACK_DAYS = 7
MAX_LOOKBACK_DAYS = 30
TREND_CALCULATION_DAYS = 14

# AI insights
AI_INSIGHT_UPDATE_HOURS = 4
AI_CONTEXT_DAYS = 7

# File paths
DEFAULT_EXPORT_PATH = "/config/oura_exports"
DEFAULT_LOG_PATH = "/config/logs/oura_full"

# Validation
MIN_SCORE = 0
MAX_SCORE = 100
MIN_HEART_RATE = 30
MAX_HEART_RATE = 220
MIN_STEPS = 0
MAX_STEPS = 100000
MIN_CALORIES = 0
MAX_CALORIES = 10000

# Error messages
ERROR_AUTH_FAILED = "Authentication failed. Please check your token."
ERROR_RATE_LIMITED = "API rate limit exceeded. Please try again later."
ERROR_CONNECTION = "Unable to connect to Oura API."
ERROR_NO_DATA = "No data available for the requested period."
ERROR_INVALID_CONFIG = "Invalid configuration. Please check your settings."