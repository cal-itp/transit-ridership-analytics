"""
Date and time wrangling.
Working with fiscal years, holidays, etc.
"""
import calendar
import pandas as pd
from datetime import date, timedelta, datetime
from pandas.tseries.holiday import USFederalHolidayCalendar

# get holidays
cal = USFederalHolidayCalendar()
holidays = cal.holidays(start='2020-01-01', end='2025-12-31')

def get_fiscal_year_range(fiscal_year: int, start_month: int):
    # given fiscal year and start month, return the start and end date of the fiscal year
    
    start_year = fiscal_year - 1 if start_month != 1 else fiscal_year
    start_date = date(start_year, start_month, 1)
    
    # compute end date
    if start_month == 1:
        end_date = date(fiscal_year, 12, 31)
    else:
        end_month = (start_month-1)
        next_month = date(fiscal_year, start_month, 1)
        end_date = next_month - timedelta(days=1)
    
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        

def get_day_type(date):

	if date in holidays:
		return "holiday"
	elif date.weekday() < 5:
		return "weekday"
	else:
		return "weekend"

def calculate_time_overlap(
    t1_start: datetime, 
    t1_end: datetime, 
    t2_start: datetime, 
    t2_end:datetime,
) -> float:
    """
    Be able to find the overlap (in days) between 
    ridership_start/end and GTFS schedule feed_key's service_date_start/end.
    """
    overlap_timedelta = max(
        timedelta(0), 
        min(t1_end, t2_end) - max(t1_start, t2_start)
    )

    overlap_days = overlap_timedelta.total_seconds() / (3_600 * 24)
    return overlap_days