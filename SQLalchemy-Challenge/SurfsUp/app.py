# Import the dependencies.

import numpy as np
import pandas as pd
import datetime as dt
import re

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables

Base.prepare(autoload_with=engine)
# Save references to each table

Station = Base.classes.station
Measurement = Base.classes.measurement
# Create our session (link) from Python to the DB

session = Session(engine)
#################################################
# Flask Setup
#################################################


app = Flask(__name__)

#################################################
# Flask Routes
#################################################




def home():
    return (
        f"Welcome to the Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt; (YYYY-MM-DD)<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; (YYYY-MM-DD)"
    )

# Step 4: Define the precipitation route
@app.route('/api/v1.0/precipitation')
def precipitation():
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query for the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    # Create a dictionary from the query results
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

# Step 5: Define the stations route
@app.route('/api/v1.0/stations')
def stations():
    # Query for all stations
    stations_list = session.query(Station.station).all()
    
    # Convert to a list
    stations = [station[0] for station in stations_list]

    return jsonify(stations)

# Step 6: Define the temperature observations route
@app.route('/api/v1.0/tobs')
def tobs():
    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]

    # Query the temperature observations for the last year
    last_year_tobs = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= (dt.datetime.now() - dt.timedelta(days=365))).all()

    # Convert to a list
    temperature_list = [{"date": date, "temperature": tobs} for date, tobs in last_year_tobs]

    return jsonify(temperature_list)

# Step 7: Define the TMIN, TAVG, TMAX route
@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def stats(start, end=None):
    # Calculate temperature stats
    if end:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()
    else:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    # Create a dictionary for the results
    temps = []
    for min_temp, avg_temp, max_temp in results:
        temps.append({
            "TMIN": min_temp,
            "TAVG": avg_temp,
            "TMAX": max_temp
        })

    return jsonify(temps)

# Step 8: Run the app
if __name__ == '__main__':
    app.run(debug=True)