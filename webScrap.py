import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import csv
from datetime import datetime
import sys

# output directory (created once)
OUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)


def ask_yes_no(prompt, default=False):
    """Ask user a yes/no question. Returns True for yes, False for no.

    If running non-interactively (stdin is not a TTY), returns default.
    """
    if not sys.stdin or not sys.stdin.isatty():
        print(f"Non-interactive mode: defaulting to {'Yes' if default else 'No'} for: {prompt}")
        return default

    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()
        if choice in ('y', 'yes'):
            return True
        if choice in ('n', 'no'):
            return False
        print("Please respond with 'y' or 'n'.")


url = 'https://www.nba.com/stats'
headers = {
    'User-Agent': 'Mozilla/5.0'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')


def format_table(table, max_rows=10, max_width=30):
    """Return a list of formatted lines for the given BeautifulSoup table.

    - Extracts header cells (th) as column names; if none, uses first row as header.
    - Truncates long cells to max_width and pads columns for alignment.
    - Limits printed rows to max_rows and shows a "... (N more rows)" line if truncated.
    """
    # Find header cells
    headers = [th.get_text(' ', strip=True) for th in table.find_all('th')]

    rows = []
    for tr in table.find_all('tr'):
        # Skip header-only rows already captured
        # Use a space separator so adjacent inline elements don't get concatenated
        cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td'])]
        if cells:
            rows.append(cells)

    # If no <th>, promote first row to header
    if not headers and rows:
        headers = rows[0]
        rows = rows[1:]

    # Build columns and compute widths
    cols = max(len(headers), max((len(r) for r in rows), default=0))
    columns = [headers[i] if i < len(headers) else '' for i in range(cols)]

    # Normalize row lengths
    norm_rows = []
    for r in rows:
        row = [r[i] if i < len(r) else '' for i in range(cols)]
        norm_rows.append(row)

    # Compute column widths
    col_widths = [0] * cols
    for i in range(cols):
        values = [columns[i]] + [row[i] for row in norm_rows]
        width = max((len(v) for v in values), default=0)
        width = min(width, max_width)
        col_widths[i] = width

    def truncate(text, w):
        return text if len(text) <= w else text[:w-3] + '...'

    # Format header
    lines = []
    if any(columns):
        header_line = ' | '.join(truncate(columns[i], col_widths[i]).ljust(col_widths[i]) for i in range(cols))
        sep_line = '-+-'.join('-' * col_widths[i] for i in range(cols))
        lines.append(header_line)
        lines.append(sep_line)

    # Format rows (limited)
    total_rows = len(norm_rows)
    shown_rows = norm_rows[:max_rows]
    for row in shown_rows:
        line = ' | '.join(truncate(row[i], col_widths[i]).ljust(col_widths[i]) for i in range(cols))
        lines.append(line)

    if total_rows > max_rows:
        lines.append(f'... ({total_rows - max_rows} more rows)')

    return lines

colors = ['\033[91m',  # Red
          '\033[92m',  # Green
          '\033[93m',  # Yellow
          '\033[94m',  # Blue
          '\033[95m',  # Magenta
          '\033[96m']  # Cyan

RESET = '\033[0m'


# Try using pandas first (cleaner HTML table parsing). Pandas uses lxml/html5lib under the hood.
try:
    dfs = pd.read_html(response.text)
except Exception:
    dfs = []

if dfs:
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 30)
    # Ask once how user wants to save files: all / none / per-table
    def ask_save_mode():
        if not sys.stdin or not sys.stdin.isatty():
            print("Non-interactive mode: defaulting to 'none' for saving files.")
            return 'none'
        while True:
            choice = input("Save mode? (a=all / n=none / p=ask per table) [p]: ").strip().lower()
            if choice == 'a':
                return 'all'
            if choice == 'n':
                return 'none'
            if choice == 'p' or choice == '':
                return 'per'
            print("Please enter 'a', 'n', or 'p'.")

    save_mode = ask_save_mode()
    for idx, df in enumerate(dfs, start=1):
        # Try to find a title for the same table index in the soup
        title = None
        try:
            table_tag = soup.find_all('table')[idx - 1]
            caption = table_tag.find('caption')
            title = caption.get_text(' ', strip=True) if caption else None
            if not title:
                prev = table_tag.find_previous(['h1', 'h2', 'h3', 'h4'])
                if prev:
                    title = prev.get_text(strip=True)
        except Exception:
            pass

        print(f'Table {idx}' + (f": {title}" if title else ''))
        # show a limited number of rows and format as a pretty string
        preview = df.head(10).to_string(index=False)
        print(preview)

        # prepare safe filenames
        safe_title = ''.join(c for c in (title or f'table_{idx}') if c.isalnum() or c in ' _-').strip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join(OUT_DIR, f'table_{idx}_{safe_title}_{timestamp}.csv')
        txt_path = os.path.join(OUT_DIR, f'table_{idx}_{safe_title}_{timestamp}.txt')

        do_save = False
        if save_mode == 'all':
            do_save = True
        elif save_mode == 'none':
            do_save = False
        else:
            do_save = ask_yes_no(f"Save table {idx} to files? (CSV & TXT)", default=False)

        if do_save:
            try:
                df.to_csv(csv_path, index=False)
            except Exception as e:
                print(f'Could not write CSV for table {idx}: {e}')

            try:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(preview)
            except Exception as e:
                print(f'Could not write TXT for table {idx}: {e}')

            print(f'Wrote: {csv_path}\n       {txt_path}')
        else:
            print(f'Skipped writing files for table {idx}.')

        print('\n' + ('=' * 80) + '\n')

# Fallback: use BeautifulSoup-based formatter if pandas couldn't find tables
else:
    tables = soup.find_all('table')
    if not tables:
        print('No <table> elements found. The site likely loads data via JavaScript; consider using the NBA stats API or Selenium.')
    else:
        skip_all = False
        save_all = False
        for idx, table in enumerate(tables[:9], start=1):
            if skip_all:
                print("Skipping remaining tables (user selected 'skip all').")
                break

            caption = table.find('caption')
            title = caption.get_text(strip=True) if caption else None
            if not title:
                prev = table.find_previous(['h1', 'h2', 'h3', 'h4'])
                if prev:
                    title = prev.get_text(strip=True)

            color = colors[(idx - 1) % len(colors)]
            print(f'Table {idx}' + (f": {color} {title} {RESET}" if title else ''))
            formatted = '\n'.join(format_table(table))
            print(formatted)

            safe_title = ''.join(c for c in (title or f'table_{idx}') if c.isalnum() or c in ' _-').strip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = os.path.join(OUT_DIR, f'table_{idx}_{safe_title}_{timestamp}.csv')
            txt_path = os.path.join(OUT_DIR, f'table_{idx}_{safe_title}_{timestamp}.txt')

            # Decide whether to save this table (support save_all and skip_all)
            do_save = False
            if save_all:
                do_save = True
            elif skip_all:
                do_save = False
            else:
                # Non-interactive: default to not saving
                if not sys.stdin or not sys.stdin.isatty():
                    print(f"Non-interactive mode: not saving table {idx}.")
                    do_save = False
                else:
                    while True:
                        try:
                            choice = input(f"Save table {idx} to files? (y/n/a=all/s=skip all): ").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            print("\nInput interrupted; skipping save for this table.")
                            do_save = False
                            break

                        if choice in ('y', 'yes'):
                            do_save = True
                            break
                        if choice in ('n', 'no', ''):
                            do_save = False
                            break
                        if choice in ('a', 'all'):
                            save_all = True
                            do_save = True
                            print("Saving this and all remaining tables.")
                            break
                        if choice in ('s', 'skip', 'skip all'):
                            skip_all = True
                            do_save = False
                            print("Skipping all remaining saves.")
                            break

                        print("Please type 'y', 'n', 'a' (all), or 's' (skip all).")

            if do_save:
                try:
                    rows = []
                    headers = [th.get_text(' ', strip=True) for th in table.find_all('th')]
                    if headers:
                        rows.append(headers)
                    for tr in table.find_all('tr'):
                        cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td'])]
                        if cells:
                            rows.append(cells)

                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        for r in rows:
                            writer.writerow(r)
                except Exception as e:
                    print(f'Could not write CSV for table {idx}: {e}')

                try:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(formatted)
                except Exception as e:
                    print(f'Could not write TXT for table {idx}: {e}')

                print(f'Wrote: {csv_path}\n       {txt_path}')
            else:
                print(f'Skipped writing files for table {idx}.')

            if skip_all:
                print('User selected skip all — exiting loop.')
                break

            print('\n' + ('=' * 80) + '\n')


        
        