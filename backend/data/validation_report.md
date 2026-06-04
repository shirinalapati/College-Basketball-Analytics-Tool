# DevelopmentIQ validation report

## 1. Team stats vs Sports Reference cache

- **illinois**: OK (ORtg 108.0, TOV% 14.1%, ORB% 14.7%, DRB% 37.1%)
- **purdue**: OK (ORtg 108.0, TOV% 14.9%, ORB% 14.4%, DRB% 37.3%)
- **duke**: OK (ORtg 108.0, TOV% 18.5%, ORB% 13.9%, DRB% 38.0%)
- **houston**: OK (ORtg 108.0, TOV% 13.4%, ORB% 15.5%, DRB% 36.0%)
- **kentucky**: OK (ORtg 108.0, TOV% 18.0%, ORB% 14.1%, DRB% 37.8%)
- **uconn**: OK (ORtg 108.0, TOV% 18.5%, ORB% 14.6%, DRB% 37.1%)
- **auburn**: OK (ORtg 108.0, TOV% 17.0%, ORB% 16.2%, DRB% 35.3%)
- **gonzaga**: OK (ORtg 108.0, TOV% 15.2%, ORB% 13.5%, DRB% 38.5%)
- **alabama**: OK (ORtg 108.0, TOV% 14.8%, ORB% 13.8%, DRB% 38.1%)
- **michigan_state**: OK (ORtg 108.0, TOV% 19.9%, ORB% 14.1%, DRB% 37.7%)

**Summary:** 10/10 teams match SR cache exactly.

## 2. Team need ranking direction

- **High turnover rate → higher ball_security need**: r=1.00 [OK]
- **Low defensive rebound % → higher defensive_rebounding need**: r=-1.00 [OK]
- **Low offensive rebound % → higher offensive_rebounding need**: r=-1.00 [OK]
- **High foul rate → higher foul_discipline need**: r=1.00 [OK]
- **Low assist rate → higher playmaking need**: r=-1.00 [OK]

## 3. Top priority by position (pool-wide)

### Guards (n=510)
- ball_security: 129
- shooting: 128
- playmaking: 126
- offensive_rebounding: 41
- rim_pressure: 36

### Wings (n=349)
- shooting: 112
- playmaking: 56
- ball_security: 37
- foul_discipline: 36
- rim_pressure: 35

### Bigs (n=59)
- shooting: 22
- defensive_activity: 9
- foul_discipline: 9
- free_throw: 8
- offensive_rebounding: 4

### Spot checks
- **Milan Momcilovic** (F, iowa_state): top=defensive_rebounding, shooting opp=0.0
- **JT Toppin** (F, texas_tech): top=playmaking, shooting opp=13.25

**Guards with top priority = offensive_rebounding:** 41 / 510

## 4. Roster sanity (Kentucky)

- Kentucky rotation (7): Andrija Jelavic, Brandon Garrison, Kam Williams, Malachi Moreno, Otega Oweh, Trent Noah, Zoom Diallo
- Denzel Aberdeen: **florida** (florida_denzel_aberdeen)
