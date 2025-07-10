import fastf1
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime, timezone
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fast F1 Data API",
    description="Get F1 standings and race info quickly using multiple free APIs",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastf1.Cache.enable_cache('cache')  # Enable cache for FastF1, change path as needed

# Pydantic models
class Driver(BaseModel):
    position: int
    driver_name: str
    abbreviation: str
    team: str
    points: float

class Team(BaseModel):
    position: int
    team_name: str
    points: float

class NextRace(BaseModel):
    race_name: str
    location: str
    country: str
    date: str
    time_left: str

class FastestLap(BaseModel):
    driver_name: str
    abbreviation: str
    team: str
    lap_time: str
    race_name: str
    date: str
    sector_times: List[float]  # Added sector times for chart

class F1Data(BaseModel):
    top_drivers: List[Driver]
    top_teams: List[Team]
    next_race: NextRace

class DashboardData(BaseModel):
    top_drivers: List[Driver]
    top_teams: List[Team]
    next_race: NextRace
    fastest_lap: FastestLap

# F1 Points System
POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

# Driver number to name mapping for OpenF1
DRIVER_INFO = {
    1:  { "name": "Max Verstappen",     "abbr": "VER", "team": "Red Bull Racing" },
    22: { "name": "Yuki Tsunoda",       "abbr": "TSU", "team": "Red Bull Racing" },

    16: { "name": "Charles Leclerc",    "abbr": "LEC", "team": "Ferrari" },
    44: { "name": "Lewis Hamilton",     "abbr": "HAM", "team": "Ferrari" },

    63: { "name": "George Russell",     "abbr": "RUS", "team": "Mercedes" },
    12: { "name": "Kimi Antonelli",     "abbr": "ANT", "team": "Mercedes" },

    4:  { "name": "Lando Norris",       "abbr": "NOR", "team": "McLaren" },
    81: { "name": "Oscar Piastri",      "abbr": "PIA", "team": "McLaren" },

    14: { "name": "Fernando Alonso",    "abbr": "ALO", "team": "Aston Martin" },
    18: { "name": "Lance Stroll",       "abbr": "STR", "team": "Aston Martin" },

    10: { "name": "Pierre Gasly",       "abbr": "GAS", "team": "Alpine" },
    43: { "name": "Franco Colapinto",   "abbr": "COL", "team": "Alpine" },

    31: { "name": "Esteban Ocon",       "abbr": "OCO", "team": "Haas" },
    87: { "name": "Oliver Bearman",     "abbr": "BEA", "team": "Haas" },

    27: { "name": "Niko Hulkenberg",    "abbr": "HUL", "team": "Kick Sauber" },
    5:  { "name": "Gabriel Bortoleto",  "abbr": "BOR", "team": "Kick Sauber" },

    23: { "name": "Alexander Albon",    "abbr": "ALB", "team": "Williams" },
    2:  { "name": "Logan Sargeant",     "abbr": "SAR", "team": "Williams" },
    55: { "name": "Carlos Sainz",       "abbr": "SAI", "team": "Williams" },

    30: { "name": "Liam Lawson",        "abbr": "LAW", "team": "Racing Bulls" },
    6:  { "name": "Isack Hadjar",       "abbr": "HAD", "team": "Racing Bulls" }
}

def calculate_time_left(race_datetime: str) -> str:
    """Calculate time left until race"""
    try:
        # Handle multiple datetime formats
        if 'T' in race_datetime:
            if race_datetime.endswith('Z'):
                race_dt = datetime.fromisoformat(race_datetime.replace('Z', '+00:00'))
            else:
                race_dt = datetime.fromisoformat(race_datetime)
        else:
            race_dt = datetime.fromisoformat(f"{race_datetime}T00:00:00+00:00")
        
        if race_dt.tzinfo is None:
            race_dt = race_dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        time_left = race_dt - now
        
        if time_left.total_seconds() < 0:
            return "Race completed"
        
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    except Exception as e:
        logger.error(f"Error calculating time left: {e}")
        return "Unknown"

async def fetch_from_f1api_dev(endpoint: str) -> Optional[Dict[Any, Any]]:
    """Fetch data from f1api.dev"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://live.f1api.dev/{endpoint}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error fetching from f1api.dev: {e}")
    return None

async def fetch_from_openf1(endpoint: str) -> Optional[List[Dict[Any, Any]]]:
    """Fetch data from OpenF1 API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://api.openf1.org/v1/{endpoint}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error fetching from OpenF1: {e}")
    return None

async def calculate_standings_from_results() -> tuple[List[Driver], List[Team]]:
    """Calculate championship standings from race results using OpenF1"""
    try:
        current_year = datetime.now().year
        
        # Get all race sessions from current year
        sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year}")
        
        if not sessions:
            logger.warning("No race sessions found, using previous year")
            sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year-1}")
        
        if not sessions:
            return await get_fallback_standings()
        
        # Calculate points for each driver and team
        driver_points = {}
        team_points = {}
        
        for session in sessions:
            session_key = session['session_key']
            
            # Get race results (positions) for this session
            positions = await fetch_from_openf1(f"position?session_key={session_key}")
            
            if not positions:
                continue
            
            # Get final positions (last position update for each driver)
            final_positions = {}
            for pos in positions:
                driver_number = pos['driver_number']
                if driver_number not in final_positions or pos['date'] > final_positions[driver_number]['date']:
                    final_positions[driver_number] = pos
            
            # Award points based on final positions
            for driver_number, pos_data in final_positions.items():
                position = pos_data['position']
                driver_info = DRIVER_INFO.get(driver_number, {
                    "name": f"Driver {driver_number}",
                    "abbr": f"D{driver_number}",
                    "team": "Unknown"
                })
                
                points = POINTS_SYSTEM.get(position, 0)
                
                # Add to driver points
                driver_key = (driver_number, driver_info['name'])
                if driver_key not in driver_points:
                    driver_points[driver_key] = {
                        'points': 0,
                        'info': driver_info
                    }
                driver_points[driver_key]['points'] += points
                
                # Add to team points
                team_name = driver_info['team']
                if team_name not in team_points:
                    team_points[team_name] = 0
                team_points[team_name] += points
        
        # Sort and create driver standings
        sorted_drivers = sorted(driver_points.items(), key=lambda x: x[1]['points'], reverse=True)
        top_drivers = []
        
        for i, ((driver_number, driver_name), data) in enumerate(sorted_drivers[:10]):
            top_drivers.append(Driver(
                position=i + 1,
                driver_name=data['info']['name'],
                abbreviation=data['info']['abbr'],
                team=data['info']['team'],
                points=float(data['points'])
            ))
        
        # Sort and create team standings
        sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)
        top_teams = []
        
        for i, (team_name, points) in enumerate(sorted_teams[:10]):
            top_teams.append(Team(
                position=i + 1,
                team_name=team_name,
                points=float(points)
            ))
        
        return top_drivers, top_teams
        
    except Exception as e:
        logger.error(f"Error calculating standings: {e}")
        return await get_fallback_standings()

async def get_fallback_standings() -> tuple[List[Driver], List[Team]]:
    """Fallback standings when calculations fail"""
    drivers = [
        Driver(position=1, driver_name="Max Verstappen", abbreviation="VER", team="Red Bull Racing", points=393.0),
        Driver(position=2, driver_name="Lando Norris", abbreviation="NOR", team="McLaren", points=331.0),
        Driver(position=3, driver_name="Charles Leclerc", abbreviation="LEC", team="Ferrari", points=307.0),
    ]
    
    teams = [
        Team(position=1, team_name="Red Bull Racing", points=860.0),
        Team(position=2, team_name="McLaren", points=608.0),
        Team(position=3, team_name="Ferrari", points=584.0),
    ]
    
    return drivers, teams

async def fetch_driver_standings():
    """Fetch driver standings from multiple sources"""
    # Try f1api.dev first
    current_year = datetime.now().year
    data = await fetch_from_f1api_dev(f"{current_year}/standings/drivers")
    
    if data and 'standings' in data:
        try:
            standings = data['standings']
            top_drivers = []
            
            for i, driver in enumerate(standings[:10]):
                top_drivers.append(Driver(
                    position=i + 1,
                    driver_name=driver.get('driver_name', driver.get('name', 'Unknown')),
                    abbreviation=driver.get('abbreviation', driver.get('code', 'UNK')),
                    team=driver.get('team', driver.get('constructor', 'Unknown')),
                    points=float(driver.get('points', 0))
                ))
            
            return top_drivers
        except Exception as e:
            logger.error(f"Error processing f1api.dev data: {e}")
    
    # Fallback to calculated standings
    logger.info("Using calculated standings from race results")
    drivers, _ = await calculate_standings_from_results()
    return drivers

async def fetch_constructor_standings():
    """Fetch constructor standings from multiple sources"""
    # Try f1api.dev first
    current_year = datetime.now().year
    data = await fetch_from_f1api_dev(f"{current_year}/standings/teams")
    
    if data and 'standings' in data:
        try:
            standings = data['standings']
            top_teams = []
            
            for i, team in enumerate(standings[:10]):
                top_teams.append(Team(
                    position=i + 1,
                    team_name=team.get('team_name', team.get('name', 'Unknown')),
                    points=float(team.get('points', 0))
                ))
            
            return top_teams
        except Exception as e:
            logger.error(f"Error processing f1api.dev teams data: {e}")
    
    # Fallback to calculated standings
    logger.info("Using calculated team standings from race results")
    _, teams = await calculate_standings_from_results()
    return teams

async def fetch_next_race():
    """Fetch next race information - FIXED VERSION"""
    current_year = datetime.now().year
    now = datetime.now(timezone.utc)
    
    # Try f1api.dev first
    data = await fetch_from_f1api_dev(f"{current_year}")
    
    if data and 'races' in data:
        try:
            races = data['races']
            
            # Find the next upcoming race
            upcoming_races = []
            for race in races:
                race_date = race.get('date', '')
                if race_date:
                    try:
                        # Handle different date formats
                        if 'T' in race_date:
                            race_dt = datetime.fromisoformat(race_date.replace('Z', '+00:00'))
                        else:
                            race_dt = datetime.fromisoformat(f"{race_date}T15:00:00+00:00")  # Default race time
                        
                        if race_dt > now:
                            upcoming_races.append((race, race_dt))
                    except Exception as e:
                        logger.error(f"Error parsing race date {race_date}: {e}")
                        continue
            
            if upcoming_races:
                # Sort by date and get the next race
                upcoming_races.sort(key=lambda x: x[1])
                next_race, race_dt = upcoming_races[0]
                
                return NextRace(
                    race_name=next_race.get('race_name', next_race.get('name', 'Unknown')),
                    location=next_race.get('location', next_race.get('circuit', 'Unknown')),
                    country=next_race.get('country', 'Unknown'),
                    date=race_dt.strftime('%Y-%m-%d %H:%M UTC'),
                    time_left=calculate_time_left(race_dt.isoformat())
                )
        except Exception as e:
            logger.error(f"Error processing race data: {e}")
    
    # Fallback to OpenF1 meetings
    try:
        meetings = await fetch_from_openf1(f"meetings?year={current_year}")
        
        if meetings:
            upcoming_meetings = []
            for meeting in meetings:
                meeting_date = meeting.get('date_start', '')
                if meeting_date:
                    try:
                        meeting_dt = datetime.fromisoformat(meeting_date.replace('Z', '+00:00'))
                        if meeting_dt > now:
                            upcoming_meetings.append((meeting, meeting_dt))
                    except Exception as e:
                        logger.error(f"Error parsing meeting date {meeting_date}: {e}")
                        continue
            
            if upcoming_meetings:
                # Sort by date and get the next meeting
                upcoming_meetings.sort(key=lambda x: x[1])
                next_meeting, meeting_dt = upcoming_meetings[0]
                
                return NextRace(
                    race_name=next_meeting.get('meeting_name', 'Unknown'),
                    location=next_meeting.get('location', 'Unknown'),
                    country=next_meeting.get('country_name', 'Unknown'),
                    date=meeting_dt.strftime('%Y-%m-%d %H:%M UTC'),
                    time_left=calculate_time_left(meeting_dt.isoformat())
                )
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
    
    # Final fallback with next year's first race
    try:
        next_year = current_year + 1
        next_year_data = await fetch_from_f1api_dev(f"{next_year}")
        
        if next_year_data and 'races' in next_year_data:
            first_race = next_year_data['races'][0]
            race_date = first_race.get('date', f"{next_year}-03-01T15:00:00Z")
            
            return NextRace(
                race_name=first_race.get('race_name', f"{next_year} Season Opener"),
                location=first_race.get('location', 'TBD'),
                country=first_race.get('country', 'TBD'),
                date=race_date.replace('T', ' ').replace('Z', ' UTC'),
                time_left=calculate_time_left(race_date)
            )
    except Exception as e:
        logger.error(f"Error fetching next year races: {e}")
    
    # Absolute fallback
    return NextRace(
        race_name="Season Break",
        location="Checking for upcoming races...",
        country="Unknown",
        date="TBD",
        time_left="Season break"
    )

async def fetch_fastest_lap():
    """Fetch fastest lap with sector times from the most recent completed race"""
    try:
        current_year = datetime.now().year

        # Get race sessions for the current year
        sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year}")
        if not sessions:
            # Fallback to previous year if no races found
            sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year - 1}")
        if not sessions:
            return get_fallback_fastest_lap()

        # Filter sessions that have already ended
        now = datetime.now(timezone.utc)
        past_races = [
            s for s in sessions
            if 'date_end' in s and datetime.fromisoformat(s['date_end'].replace('Z', '+00:00')) < now
        ]

        if not past_races:
            return get_fallback_fastest_lap()

        # Get the most recent completed race
        latest_session = max(past_races, key=lambda s: s['date_end'])
        session_key = latest_session['session_key']

        # Fetch laps only for that session
        laps = await fetch_from_openf1(f"laps?session_key={session_key}")
        if not laps:
            return get_fallback_fastest_lap()

        # Filter laps with valid lap_duration
        valid_laps = [lap for lap in laps if lap.get('lap_duration') and lap['lap_duration'] > 0]
        if not valid_laps:
            return get_fallback_fastest_lap()

        # Get the fastest lap
        fastest_lap = min(valid_laps, key=lambda x: x['lap_duration'])
        driver_number = fastest_lap['driver_number']

        driver_info = DRIVER_INFO.get(driver_number, {
            "name": f"Driver {driver_number}",
            "abbr": f"D{driver_number}",
            "team": "Unknown"
        })

        # Format lap time
        duration = fastest_lap['lap_duration']
        minutes = int(duration // 60)
        seconds = duration % 60
        lap_time = f"{minutes}:{seconds:06.3f}"

        # Try to get sector times for this specific lap
        sector_times = await get_sector_times(session_key, driver_number, fastest_lap.get('lap_number', 1))

        return FastestLap(
            driver_name=driver_info["name"],
            abbreviation=driver_info["abbr"],
            team=driver_info["team"],
            lap_time=lap_time,
            race_name=latest_session.get('meeting_name', 'Unknown'),
            date=latest_session.get('date_start', '')[:10],
            sector_times=sector_times
        )

    except Exception as e:
        logger.error(f"Error fetching latest fastest lap: {e}")
        return get_fallback_fastest_lap()

async def fetch_fastest_laps():
    """Fetch fastest lap for top 10 different drivers from the most recent completed race"""
    try:
        current_year = datetime.now().year

        # Get sessions
        sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year}")
        if not sessions:
            sessions = await fetch_from_openf1(f"sessions?session_type=Race&year={current_year - 1}")
        if not sessions:
            return [get_fallback_fastest_lap()]

        now = datetime.now(timezone.utc)
        past_races = [
            s for s in sessions
            if 'date_end' in s and datetime.fromisoformat(s['date_end'].replace('Z', '+00:00')) < now
        ]
        if not past_races:
            return [get_fallback_fastest_lap()]

        latest_session = max(past_races, key=lambda s: s['date_end'])
        session_key = latest_session['session_key']

        # Fetch all laps
        laps = await fetch_from_openf1(f"laps?session_key={session_key}")
        if not laps:
            return [get_fallback_fastest_lap()]

        # Group laps by driver and get their best lap
        driver_best_laps = {}
        for lap in laps:
            if lap.get('lap_duration') and lap['lap_duration'] > 0:
                dnum = lap['driver_number']
                if dnum not in driver_best_laps or lap['lap_duration'] < driver_best_laps[dnum]['lap_duration']:
                    driver_best_laps[dnum] = lap

        # Get fastest lap of each driver, sort, then take top 10
        top_laps = sorted(driver_best_laps.values(), key=lambda x: x['lap_duration'])[:10]

        results = []
        for lap in top_laps:
            driver_number = lap['driver_number']
            lap_number = lap.get('lap_number', 1)

            driver_info = DRIVER_INFO.get(driver_number, {
                "name": f"Driver {driver_number}",
                "abbr": f"D{driver_number}",
                "team": "Unknown"
            })

            duration = lap['lap_duration']
            minutes = int(duration // 60)
            seconds = duration % 60
            lap_time = f"{minutes}:{seconds:06.3f}"

            sector_times = await get_sector_times(session_key, driver_number, lap_number)

            results.append(FastestLap(
                driver_name=driver_info["name"],
                abbreviation=driver_info["abbr"],
                team=driver_info["team"],
                lap_time=lap_time,
                race_name=latest_session.get('meeting_name', 'Unknown'),
                date=latest_session.get('date_start', '')[:10],
                sector_times=sector_times
            ))

        return results

    except Exception as e:
        logger.error(f"Error fetching top 10 fastest laps: {e}")
        return [get_fallback_fastest_lap()]

def get_fallback_fastest_lap():
    """Fallback fastest lap data with sector times"""
    return FastestLap(
        driver_name="Max Verstappen",
        abbreviation="VER",
        team="Red Bull Racing",
        lap_time="1:20.554",
        race_name="Abu Dhabi Grand Prix",
        date="2024-12-08",
        sector_times=[25.5, 35.2, 19.854]  # Realistic sector breakdown
    )

@app.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get all dashboard data including fastest lap"""
    try:
        # Fetch all data concurrently for maximum speed
        drivers_task = fetch_driver_standings()
        teams_task = fetch_constructor_standings()
        race_task = fetch_next_race()
        fastest_lap_task = fetch_fastest_lap()
        
        top_drivers, top_teams, next_race, fastest_lap = await asyncio.gather(
            drivers_task, teams_task, race_task, fastest_lap_task
        )
        
        return DashboardData(
            top_drivers=top_drivers,
            top_teams=top_teams,
            next_race=next_race,
            fastest_lap=fastest_lap
        )
        
    except Exception as e:
        logger.error(f"Error processing dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing dashboard data: {str(e)}")

@app.get("/fastest-lap", response_model=FastestLap)
async def get_fastest_lap():
    """Get fastest lap from the most recent race"""
    return await fetch_fastest_lap()

@app.get("/f1-data", response_model=F1Data)
async def get_f1_data():
    """Get top 3 drivers, top 3 teams, and next race information"""
    try:
        # Fetch all data concurrently for speed
        drivers_task = fetch_driver_standings()
        teams_task = fetch_constructor_standings()
        race_task = fetch_next_race()
        
        top_drivers, top_teams, next_race = await asyncio.gather(
            drivers_task, teams_task, race_task
        )
        
        return F1Data(
            top_drivers=top_drivers,
            top_teams=top_teams,
            next_race=next_race
        )
        
    except Exception as e:
        logger.error(f"Error processing F1 data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing F1 data: {str(e)}")

@app.get("/drivers", response_model=List[Driver])
async def get_top_drivers():
    """Get only the top 3 drivers"""
    return await fetch_driver_standings()

@app.get("/teams", response_model=List[Team])
async def get_top_teams():
    """Get only the top 3 teams"""
    return await fetch_constructor_standings()

@app.get("/next-race", response_model=NextRace)
async def get_next_race():
    """Get only the next race information"""
    return await fetch_next_race()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Fast F1 Data API v3.0",
        "description": "Lightning fast F1 standings and race info using multiple free APIs with dynamic calculation fallbacks",
        "features": [
            "Multiple API sources (f1api.dev, OpenF1)",
            "Dynamic championship calculation from race results",
            "Real-time fastest lap data with sector times",
            "Intelligent fallback mechanisms",
            "100% free data sources"
        ],
        "data_sources": {
            "primary": "f1api.dev (free F1 API)",
            "secondary": "OpenF1 (real-time race data)",
            "calculation": "Championship points calculated from race results when APIs unavailable"
        },
        "endpoints": {
            "/dashboard": "Get all dashboard data (drivers, teams, next race, fastest lap)",
            "/f1-data": "Get basic F1 data (drivers, teams, next race)",
            "/drivers": "Get top 3 drivers",
            "/teams": "Get top 3 teams", 
            "/next-race": "Get next race information",
            "/fastest-lap": "Get fastest lap from most recent race with sector times"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)