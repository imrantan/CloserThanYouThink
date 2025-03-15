import pandas as pd
import itertools

# Function to split call duration by hours
def split_call_by_hour(start_time, end_time, time_zone):
    time_range = pd.date_range(start=start_time, end=end_time, freq='h')
    split_minutes = []
    
    for i in range(len(time_range) - 1):
        start_interval = time_range[i]
        end_interval = time_range[i + 1]
        
        # Calculate the time spent in this hour interval
        start_in_this_hour = max(start_time, start_interval)
        end_in_this_hour = min(end_time, end_interval)
        
        # Calculate minutes spent in this interval
        minutes_in_this_hour = (end_in_this_hour - start_in_this_hour).total_seconds() / 60
        
        if minutes_in_this_hour > 0:
            split_minutes.append({
                'time_bucket': start_in_this_hour,
                'minutes': minutes_in_this_hour,
                'time_zone': time_zone
            })
    
    return split_minutes

# Function to re-shape the dataset

def transform_for_time_heatmap(df_combined):

    # List to store the split minutes for both SG and NZ
    sg_minutes = []
    nz_minutes = []

    # Iterate over each call to split into hourly buckets
    for _, row in df_combined.iterrows():
        # Split SG call duration by hour
        sg_minutes.extend(split_call_by_hour(row['Start_Datetime_SG'], row['End_Datetime_SG'], 'SG'))
        
        # Split NZ call duration by hour
        nz_minutes.extend(split_call_by_hour(row['Start_Datetime_NZ'], row['End_Datetime_NZ'], 'NZ'))

    # Convert to DataFrame
    sg_minutes_df = pd.DataFrame(sg_minutes)
    nz_minutes_df = pd.DataFrame(nz_minutes)

    # Adjust the weekday to start from Sunday (0=Sunday, 6=Saturday)
    sg_minutes_df['Weekday'] = (sg_minutes_df['time_bucket'].dt.dayofweek + 1) % 7
    nz_minutes_df['Weekday'] = (nz_minutes_df['time_bucket'].dt.dayofweek + 1) % 7

    # Add hour of the day
    sg_minutes_df['Hour'] = sg_minutes_df['time_bucket'].dt.hour
    nz_minutes_df['Hour'] = nz_minutes_df['time_bucket'].dt.hour

    # Aggregate by day of week and hour for SG
    sg_agg = sg_minutes_df.groupby(['Weekday', 'Hour']).agg({'minutes': 'sum'}).reset_index()
    # Rename the aggregated column
    sg_agg = sg_agg.rename(columns={'minutes': 'minutes_SG'})

    # Aggregate by day of week and hour for NZ
    nz_agg = nz_minutes_df.groupby(['Weekday', 'Hour']).agg({'minutes': 'sum'}).reset_index()
    # Rename the aggregated column
    nz_agg = nz_agg.rename(columns={'minutes': 'minutes_NZ'})

    # Define days of the week (Sunday=0, Saturday=6)
    days_of_week = [0, 1, 2, 3, 4, 5, 6]

    # Define hours of the day (0 to 23)
    hours_of_day = list(range(24))

    # Generate all combinations of days of the week and hours of the day
    week_combinations = list(itertools.product(days_of_week, hours_of_day))

    # Create a DataFrame from the combinations
    df_week_combinations = pd.DataFrame(week_combinations, columns=['Day_of_Week', 'Hour'])

    # # Optionally, if you want to show the day of the week as a string (e.g., Sunday, Monday, etc.)
    # df_week_combinations['Day_of_Week'] = df_week_combinations['Day_of_Week'].map({
    #     0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
    #     4: 'Thursday', 5: 'Friday', 6: 'Saturday'
    # })

    # Merge datasets
    df_week_combinations = pd.merge(left=df_week_combinations, 
                                    right=sg_agg,
                                    left_on=['Day_of_Week', 'Hour'],
                                    right_on=['Weekday', 'Hour'],
                                    how='left')

    df_week_combinations = df_week_combinations.drop(columns=['Weekday']) # drop unnecessary column

    df_week_combinations = pd.merge(left=df_week_combinations, 
                                    right=nz_agg,
                                    left_on=['Day_of_Week', 'Hour'],
                                    right_on=['Weekday', 'Hour'],
                                    how='left')

    df_week_combinations = df_week_combinations.drop(columns=['Weekday']) # drop unnecessary column

    return df_week_combinations

