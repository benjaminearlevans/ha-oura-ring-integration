
# Oura Ring Home Assistant Integration

## 1. Product Requirements Document (PRD)

### 1.1 Purpose & Goals

**Purpose:**  
Build a Home Assistant integration ("Oura Ring") that connects to the Oura Ring API v2, pulls all relevant health, readiness, activity, sleep, and other metrics available via the API, and exposes them as entities in Home Assistant.

**Goals:**

- Support Oura API v2 endpoints including sleep, readiness, activity, bedtime, user info, tags, workouts, heart rate, etc.
- Use modern Home Assistant best practices.
- Provide dashboard / Lovelace UI suggestions.
- Support both Personal Access Token (PAT) and OAuth2.
- Robust error handling, rate limiting compliance.
- Usable by non-developers; configuration via UI.

### 1.2 Scope

**Included:**

- Fetching daily summaries and granular data.
- Exposing entities and attributes.
- Configuration flows and dashboards.

**Excluded:**

- Real-time streaming.
- Webhook support.
- Highly custom visualizations.

### 1.3 Stakeholders

- **Primary user:** HA users with Oura Ring.
- **Secondary users:** Automation authors, health dashboards.
- **Developer / Maintainer:** You or assigned developer.

### 1.4 Success Metrics

- 90% of Oura v2 metrics implemented.
- Stable entities and dashboards.
- Minimal auth/token/rate limit issues.
- Good community feedback.

## 2. API Specifications & Key Oura API v2 Elements

### 2.1 Authentication

- **PAT**: Easy setup.
- **OAuth2**: Futureproof, multi-user.

### 2.2 Rate Limiting & Error Handling

- Handle HTTP 429, 401, etc.
- Respect documented limits.

### 2.3 Key Endpoints

| Endpoint | Summary | Metrics |
|----------|---------|---------|
| User Info | Profile | age, height, sex, etc. |
| Daily Sleep | Summary | total sleep, score, stages |
| Sleep Periods | Segments | granular data |
| Daily Readiness | Recovery | readiness score, RHR |
| Daily Activity | Fitness | steps, calories |
| Tags, Workouts | Labeled events | time, type |
| Heart Rate | HR | RHR, trends |

### 2.4 Request Parameters

- Date ranges, pagination.

## 3. User Stories

| Role | Want | Why |
|------|------|-----|
| User | Connect Oura | Automate based on health |
| HA user | View sleep score | Understand sleep |
| Automation user | Trigger on readiness | Take rest |
| Developer | Handle errors | Keep integration stable |

## 4. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | PAT auth | High |
| FR-2 | OAuth2 | Medium |
| FR-3 to FR-9 | Fetch endpoints | High |
| FR-10 | Entities & attributes | High |
| FR-11 | Scheduled updates | High |
| FR-12 | Dashboard samples | Medium |
| FR-13 | Token refresh | High |

## 5. Non-Functional Requirements

- Performance
- Security
- Reliability
- Maintainability
- Extensibility

## 6. Entities, Helpers, Attributes Design

### 6.1 Entity Types

- SensorEntity
- BinarySensorEntity
- DeviceInfo

### 6.2 Core Entities & Attributes

- `sensor.oura_sleep_total_hours`
- `sensor.oura_sleep_score`
- `sensor.oura_readiness_score`
- `sensor.oura_activity_steps`
- `sensor.oura_user_age`
- Attributes include: latency, HRV, REM duration, etc.

### 6.3 Helpers / Options

- Input helpers for thresholds
- Options for enabled metrics
- Configurable fetch interval

### 6.4 Proposed Names

`sensor.oura_<metric>` format (e.g., `oura_sleep_deep_hours`)

### 6.5 Dashboards

- Trend cards using ApexCharts, mini-graph-card

## 7. API-to-Entity Mapping

| Endpoint | Field | Entity | Unit |
|----------|-------|--------|------|
| User | age | `sensor.oura_user_age` | years |
| Sleep | duration | `sensor.oura_sleep_total` | hours |
| Sleep | score | `sensor.oura_sleep_score` | points |
| Readiness | score | `sensor.oura_readiness_score` | points |
| Activity | steps | `sensor.oura_activity_steps` | steps |
| Activity | calories | `sensor.oura_activity_active_calories` | kcal |

## 8. Design Notes

- Use DataUpdateCoordinator
- Config Entry + Options Flow
- Secure token storage
- Localization support

## 9. Project Plan

| Milestone | Tasks |
|-----------|-------|
| M1 | PAT + user info |
| M2 | Sleep, Readiness, Activity |
| M3 | Tags, HR, Workouts |
| M4 | Options, helpers |
| M5 | OAuth2, error handling |
| M6 | Dashboards |
| M7 | Docs, packaging |

## 10. Sample User Flows

- PAT entry via UI
- OAuth2 flow
- Sensor visualization
- Automation on score threshold

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| API changes | Versioned abstraction |
| Rate limits | Interval config |
| Token expiry | UI re-auth |
| Data overload | Limit history pull |
