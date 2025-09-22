🎯 AUTOMATION SCENARIOS
1. Circadian Lighting Optimization
yaml- Monitors temperature deviation and readiness
- Adjusts color temperature based on circadian phase
- Dims lights progressively as optimal bedtime approaches
- Activates "sunset simulation" 2 hours before suggested bedtime
- Morning lights adapt to sleep debt (gentler wake if poor recovery)
2. Sleep Sanctuary Mode
yamlTRIGGERS:
- Oura detects in-bed status
- Heart rate dropping below daytime average

ACTIONS:
- Lock all smart locks
- Arm security system (sleep mode)
- Reduce HVAC to optimal sleep temperature (based on Oura trends)
- Activate white noise at personalized volume
- Block all non-emergency notifications
- Dim pathway lights to 5% red
3. Recovery-Based Morning Routine
yamlIF readiness_score < 60:
  - Delay alarm by 30 minutes (if calendar permits)
  - Start gentle wake sequence (15 min gradual)
  - Warm floor heating in bathroom
  - Prepare recovery playlist
  - Suggest light stretching routine on display
  - Brew adaptogenic tea instead of coffee

IF readiness_score > 85:
  - Normal alarm time
  - Energetic wake lighting
  - Start workout playlist
  - Display HIIT workout suggestion
  - Pre-heat home gym equipment

4. Stress Response System
yaml WHEN stress_score elevated for 30+ minutes:
  - Shift lighting to calming blues/greens
  - Lower ambient temperature by 2°F
  - Start diffuser with lavender
  - Queue breathing exercise on displays
  - Reduce background music tempo
  - Send gentle reminder to take a break
  - Prepare meditation space (dim lights, activate sound dampening)
5. Activity Motivation
yamlIF inactive_time > 90 minutes AND readiness > 70:
  - Flash desk light gently
  - Raise standing desk (if motorized)
  - Display movement reminder on screens
  - Queue energizing music
  - Slightly increase room temperature
  - Open blinds for natural light exposure
6. Temperature Regulation
yaml- Track skin temperature trends
- Pre-adjust room temperature before detected fever
- Activate humidifier if temperature elevated
- Suggest hydration reminders
- Prepare "sick day" scene if sustained elevation
7. Workout Optimization
yaml

PRE-WORKOUT (based on readiness):
  High Readiness: 
    - Energetic lighting (5000K)
    - High-tempo playlist
    - Pre-cool gym space
    - Display PR targets
  
  Low Readiness:
    - Moderate lighting (3500K)
    - Recovery-focused playlist
    - Maintain neutral temperature
    - Suggest mobility work

POST-WORKOUT:
  - Monitor heart rate recovery
  - Adjust cooling based on exertion
  - Queue recovery protocols
  - Prepare protein shake reminder
8. Nap Intelligence
yamlIF sleep_debt > 60min AND time between 1-4pm:
  - Suggest 20-minute power nap
  - Darken room to 20%
  - Set optimal nap temperature
  - Play brown noise
  - Auto-wake with gradual light