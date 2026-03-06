# NBA Stats Web Scraper

A Python script that scrapes table data from the NBA statistics website and displays it in the terminal. The script can also optionally save the scraped tables as **CSV** and **TXT** files for later analysis.

## Features

- Scrapes tables from the NBA stats webpage
- Automatically detects and formats tables
- Displays a preview of table data in the terminal
- Option to save tables as:
  - CSV files (for data analysis)
  - TXT files (formatted preview)
- Automatically creates an `output` directory
- Works in both interactive and non-interactive environments
- Uses **pandas** for structured table extraction
- Falls back to **BeautifulSoup** parsing if pandas cannot detect tables

## Technologies Used

- Python
- requests
- BeautifulSoup4
- pandas
- HTML parsing

## Installation

Clone the repository:

```bash
git clone https://github.com/Elites100/nba-stats-scraper.git
cd nba-stats-scraper
```

## Usage

Run the script:

```python webScrap.py```

The program will:

- Fetch the NBA stats webpage

- Detect tables on the page

- Display a preview of each table

Ask if you want to save tables to files

Example save options:

```
 Save mode? (a=all / n=none / p=ask per table)
```
Output

If saving is enabled, files will be stored in:

```/output```

Example files:

```table_1_player_stats_20260306_120000.csv
table_1_player_stats_20260306_120000.txt
```

### Notes

- Some NBA stats data is loaded dynamically using JavaScript, so not all tables may be available through basic HTML scraping.

- In those cases, using the NBA Stats API or Selenium may provide more complete data.

### Future Improvements

- Support for JavaScript-rendered content (Selenium)

- Direct integration with the NBA stats API

- Automatic dataset cleaning

- Visualization of stats
