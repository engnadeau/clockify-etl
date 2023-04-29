# Clockify ETL

Clockify-ETL is a repository that contains an ETL pipeline and orchestration for collecting, parsing, and transforming Clockify timesheets for clients and consulting. It's a valuable tool for streamlining the process of time tracking and data management, making it easier and more efficient to manage consulting projects.

## Architecture

- Month range
- Fetch data from Clockify
- Merge data into monthly dataframes
- Split dataframes by clients and projects
- Dump dataframes to CSV
- Upload to google drive
