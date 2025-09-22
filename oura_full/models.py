"""Data models for Oura API responses."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReadinessLevel(Enum):
    """Readiness level classifications."""
    OPTIMAL = "optimal"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActivityIntensity(Enum):
    """Activity intensity levels."""
    REST = "rest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SleepQuality(Enum):
    """Sleep quality classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class WellnessPhase(Enum):
    """Wellness phase classifications."""
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"
    CHALLENGE = "challenge"
    PEAK = "peak"


@dataclass
class SleepData:
    """Sleep period data model."""
    
    id: str
    day: str
    score: Optional[int] = None
    total_duration: Optional[int] = None
    efficiency: Optional[int] = None
    latency: Optional[int] = None
    rem_duration: Optional[int] = None
    deep_duration: Optional[int] = None
    light_duration: Optional[int] = None
    awake_duration: Optional[int] = None
    average_hrv: Optional[float] = None
    lowest_heart_rate: Optional[int] = None
    respiratory_rate: Optional[float] = None
    temperature_deviation: Optional[float] = None
    bedtime_start: Optional[datetime] = None
    bedtime_end: Optional[datetime] = None
    time_in_bed: Optional[int] = None
    restless_periods: Optional[int] = None
    
    # Granular data
    heart_rate_5min: List[Optional[int]] = field(default_factory=list)
    hrv_5min: List[Optional[float]] = field(default_factory=list)
    movement_30sec: str = ""
    sleep_phase_5min: str = ""
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "SleepData":
        """Create SleepData from API response."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            score=data.get("score"),
            total_duration=data.get("contributors", {}).get("total_sleep"),
            efficiency=data.get("contributors", {}).get("efficiency"),
            latency=data.get("contributors", {}).get("latency"),
            rem_duration=data.get("contributors", {}).get("rem_sleep"),
            deep_duration=data.get("contributors", {}).get("deep_sleep"),
            light_duration=data.get("contributors", {}).get("light_sleep"),
            awake_duration=data.get("awake_time"),
            average_hrv=data.get("average_hrv"),
            lowest_heart_rate=data.get("lowest_heart_rate"),
            respiratory_rate=data.get("average_breath"),
            temperature_deviation=data.get("temperature_deviation"),
            bedtime_start=cls._parse_datetime(data.get("bedtime_start")),
            bedtime_end=cls._parse_datetime(data.get("bedtime_end")),
            time_in_bed=data.get("time_in_bed"),
            restless_periods=data.get("restless_periods"),
        )
    
    @property
    def hours_slept(self) -> float:
        """Convert total duration to hours."""
        return (self.total_duration or 0) / 3600
    
    @property
    def sleep_quality(self) -> str:
        """Determine sleep quality based on score."""
        if not self.score:
            return SleepQuality.FAIR.value
        if self.score >= 85:
            return SleepQuality.EXCELLENT.value
        elif self.score >= 70:
            return SleepQuality.GOOD.value
        elif self.score >= 60:
            return SleepQuality.FAIR.value
        return SleepQuality.POOR.value
    
    def add_period_details(self, period_data: Dict[str, Any]) -> None:
        """Add detailed period data to sleep data."""
        if "heart_rate" in period_data:
            hr_data = period_data["heart_rate"]
            self.heart_rate_5min = hr_data.get("items", [])
        
        if "hrv" in period_data:
            hrv_data = period_data["hrv"]
            self.hrv_5min = hrv_data.get("items", [])
        
        if "movement_30_sec" in period_data:
            self.movement_30sec = period_data["movement_30_sec"]
        
        if "sleep_phase_5_min" in period_data:
            self.sleep_phase_5min = period_data["sleep_phase_5_min"]
    
    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime from API response."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


@dataclass
class ReadinessData:
    """Daily readiness data model."""
    
    id: str
    day: str
    score: Optional[int] = None
    temperature_deviation: Optional[float] = None
    temperature_trend: Optional[float] = None
    contributors: Dict[str, Optional[int]] = field(default_factory=dict)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ReadinessData":
        """Create ReadinessData from API response."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            score=data.get("score"),
            temperature_deviation=data.get("temperature_deviation"),
            temperature_trend=data.get("temperature_trend_deviation"),
            contributors=data.get("contributors", {}),
        )
    
    @property
    def readiness_level(self) -> ReadinessLevel:
        """Determine readiness level."""
        if not self.score:
            return ReadinessLevel.MEDIUM
        if self.score >= 85:
            return ReadinessLevel.OPTIMAL
        elif self.score >= 70:
            return ReadinessLevel.HIGH
        elif self.score >= 60:
            return ReadinessLevel.MEDIUM
        return ReadinessLevel.LOW
    
    @property
    def recovery_recommendation(self) -> str:
        """Generate recovery recommendation."""
        level = self.readiness_level
        if level == ReadinessLevel.OPTIMAL:
            return "Ready for challenging activities"
        elif level == ReadinessLevel.HIGH:
            return "Good day for normal activities"
        elif level == ReadinessLevel.MEDIUM:
            return "Consider lighter activities"
        return "Prioritize rest and recovery"


@dataclass
class ActivityData:
    """Daily activity data model."""
    
    id: str
    day: str
    score: Optional[int] = None
    steps: Optional[int] = None
    total_calories: Optional[int] = None
    active_calories: Optional[int] = None
    met_minutes: Dict[str, int] = field(default_factory=dict)
    inactive_time: Optional[int] = None
    low_activity_time: Optional[int] = None
    medium_activity_time: Optional[int] = None
    high_activity_time: Optional[int] = None
    non_wear_time: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ActivityData":
        """Create ActivityData from API response."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            score=data.get("score"),
            steps=data.get("steps"),
            total_calories=data.get("total_calories"),
            active_calories=data.get("active_calories"),
            met_minutes=data.get("met", {}),
            inactive_time=data.get("sedentary_time"),
            low_activity_time=data.get("low_activity_time"),
            medium_activity_time=data.get("medium_activity_time"),
            high_activity_time=data.get("high_activity_time"),
            non_wear_time=data.get("non_wear_time"),
        )
    
    @property
    def activity_level(self) -> ActivityIntensity:
        """Determine predominant activity level."""
        times = {
            ActivityIntensity.REST: self.inactive_time or 0,
            ActivityIntensity.LOW: self.low_activity_time or 0,
            ActivityIntensity.MEDIUM: self.medium_activity_time or 0,
            ActivityIntensity.HIGH: self.high_activity_time or 0,
        }
        return max(times, key=times.get)
    
    @property
    def active_hours(self) -> float:
        """Calculate total active hours."""
        total_active = (
            (self.low_activity_time or 0) +
            (self.medium_activity_time or 0) +
            (self.high_activity_time or 0)
        )
        return total_active / 3600


@dataclass
class HeartRateData:
    """Heart rate data model."""
    
    day: str
    average: Optional[float] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    resting: Optional[int] = None
    samples: List[int] = field(default_factory=list)
    
    @property
    def variability(self) -> float:
        """Calculate heart rate variability."""
        if len(self.samples) < 2:
            return 0
        
        mean = sum(self.samples) / len(self.samples)
        variance = sum((x - mean) ** 2 for x in self.samples) / len(self.samples)
        return variance ** 0.5


@dataclass
class StressData:
    """Daily stress data model."""
    
    id: str
    day: str
    score: Optional[int] = None
    high_periods: Optional[int] = None
    recovery_periods: Optional[int] = None
    daytime_stress_load: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "StressData":
        """Create StressData from API response."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            score=data.get("day_summary", {}).get("score"),
            high_periods=data.get("day_summary", {}).get("stress_high"),
            recovery_periods=data.get("day_summary", {}).get("recovery_high"),
            daytime_stress_load=data.get("day_summary", {}).get("daytime_stress_load"),
        )
    
    @property
    def stress_level(self) -> str:
        """Determine stress level."""
        if not self.score:
            return "unknown"
        if self.score < 30:
            return "low"
        elif self.score < 60:
            return "moderate"
        return "high"


@dataclass
class WorkoutData:
    """Workout data model."""
    
    id: str
    day: str
    activity: Optional[str] = None
    calories: Optional[int] = None
    distance: Optional[float] = None
    duration: Optional[int] = None
    intensity: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "WorkoutData":
        """Create WorkoutData from API response."""
        return cls(
            id=data.get("id", ""),
            day=data.get("day", ""),
            activity=data.get("activity"),
            calories=data.get("calories"),
            distance=data.get("distance"),
            duration=data.get("duration"),
            intensity=data.get("intensity"),
            start_datetime=cls._parse_datetime(data.get("start_datetime")),
            end_datetime=cls._parse_datetime(data.get("end_datetime")),
        )
    
    @property
    def duration_hours(self) -> float:
        """Convert duration to hours."""
        return (self.duration or 0) / 3600
    
    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime from API response."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


@dataclass
class CircadianData:
    """Circadian alignment data model."""
    
    aligned: bool = False
    score: int = 0
    optimal_bedtime: str = "22:00"
    optimal_wake: str = "06:00"
    bedtime_consistency: int = 0
    wake_consistency: int = 0
    
    @property
    def alignment_quality(self) -> str:
        """Determine alignment quality."""
        if self.score >= 80:
            return "excellent"
        elif self.score >= 60:
            return "good"
        elif self.score >= 40:
            return "fair"
        return "poor"


@dataclass
class WellnessData:
    """Overall wellness data model."""
    
    phase: WellnessPhase
    sleep_score: Optional[int] = None
    readiness_score: Optional[int] = None
    activity_score: Optional[int] = None
    stress_score: Optional[int] = None
    circadian_score: Optional[int] = None
    
    @property
    def overall_score(self) -> int:
        """Calculate overall wellness score."""
        scores = [
            self.sleep_score,
            self.readiness_score,
            self.activity_score,
            100 - (self.stress_score or 0),  # Invert stress score
            self.circadian_score,
        ]
        valid_scores = [s for s in scores if s is not None]
        
        if not valid_scores:
            return 50
        
        return int(sum(valid_scores) / len(valid_scores))
    
    @property
    def primary_concern(self) -> str:
        """Identify primary wellness concern."""
        scores = {
            "sleep": self.sleep_score or 100,
            "readiness": self.readiness_score or 100,
            "activity": self.activity_score or 100,
            "stress": 100 - (self.stress_score or 0),
            "circadian": self.circadian_score or 100,
        }
        
        return min(scores, key=scores.get)