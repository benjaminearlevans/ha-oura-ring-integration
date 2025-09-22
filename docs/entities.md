

# sleep entitities
sensor.oura_sleep_score                  # 0-100 score
sensor.oura_sleep_efficiency             # Percentage
sensor.oura_total_sleep_duration         # Minutes
sensor.oura_deep_sleep_duration          # Minutes
sensor.oura_rem_sleep_duration           # Minutes
sensor.oura_light_sleep_duration         # Minutes
sensor.oura_awake_time                   # Minutes
sensor.oura_sleep_latency                # Time to fall asleep
sensor.oura_bedtime_start                # Timestamp
sensor.oura_bedtime_end                  # Timestamp
sensor.oura_lowest_heart_rate            # BPM during sleep
sensor.oura_average_hrv                  # ms
sensor.oura_respiratory_rate             # Breaths/min
binary_sensor.oura_in_bed               # On/Off
binary_sensor.oura_sleeping             # On/Off

# activity entities
sensor.oura_activity_score               # 0-100 score
sensor.oura_steps                        # Steps
sensor.oura_total_calories               # Calories
sensor.oura_active_calories              # Calories
sensor.oura_met_minutes                  # Minutes
sensor.oura_inactive_time                # Minutes
sensor.oura_low_activity_time            # Minutes
sensor.oura_medium_activity_time         # Minutes
sensor.oura_high_activity_time           # Minutes
sensor.oura_non_wear_time                # Minutes
binary_sensor.oura_walking              # On/Off
binary_sensor.oura_running               # On/Off
binary_sensor.oura_cycling              # On/Off
binary_sensor.oura_swimming             # On/Off
binary_sensor.oura_exercising           # On/Off
binary_sensor.oura_sedentary            # On/Off

# Readiness & Recovery Entities
sensor.oura_readiness_score              # 0-100 score
sensor.oura_temperature_deviation        # °C from baseline
sensor.oura_temperature_trend            # Trending up/down
sensor.oura_hrv_balance                  # HRV trend score
sensor.oura_recovery_index               # Recovery score
sensor.oura_activity_balance             # Activity equilibrium
sensor.oura_sleep_balance                # Sleep debt/surplus
sensor.oura_resting_heart_rate          # Daily RHR
select.oura_readiness_level             # Low/Medium/High/Optimal

# Activity & Movement Entities
sensor.oura_daily_steps                  # Step count
sensor.oura_total_calories               # kcal burned
sensor.oura_active_calories              # Activity kcal
sensor.oura_met_minutes                  # Metabolic equivalent minutes
sensor.oura_inactive_time                # Minutes
sensor.oura_low_activity_time           # Minutes
sensor.oura_medium_activity_time        # Minutes
sensor.oura_high_activity_time          # Minutes
sensor.oura_activity_score              # 0-100 score
binary_sensor.oura_activity_goal_met    # On/Off

# Physiological Entities
sensor.oura_current_heart_rate          # Live BPM (when available)
sensor.oura_daily_average_hrv           # ms
sensor.oura_spo2_average                # Blood oxygen %
sensor.oura_skin_temperature            # °C
sensor.oura_stress_score                # Daily stress level
sensor.oura_stress_high_periods         # Count of high stress
sensor.oura_daytime_stress_load        # Accumulated stress

# Workout & Session Entities
sensor.oura_workout_today               # Count
sensor.oura_last_workout_type          # Type string
sensor.oura_last_workout_intensity     # Low/Medium/High
sensor.oura_meditation_minutes         # Daily total
binary_sensor.oura_workout_active      # Currently exercising

# Trend & Insight Entities
sensor.oura_sleep_trend_7d             # 7-day average
sensor.oura_readiness_trend_7d         # 7-day average
sensor.oura_activity_trend_7d          # 7-day average
sensor.oura_optimal_bedtime            # Suggested time
sensor.oura_recovery_time_needed       # Hours
input_select.oura_wellness_phase       # Recovery/Maintenance/Challenge

#