from datetime import datetime

def build_html_from_observations(observations):
    headers = ['From','Species', 'Distance', 'How Many', 'Date', 'Location', 'Comments', 'Photos', 'eBird Link']
    rows = [observation.values() for observation in observations]

    # Create the HTML for the table headers
    headers_html = ''.join(f'<th>{header}</th>' for header in headers)

    # Create the HTML for the table rows
    rows_html = ''.join(f'<tr>{" ".join(f"<td>{cell}</td>" for cell in row)}</tr>' for row in rows)

    # Combine the headers and rows into a complete HTML table
    table_html = f'''
    <table>
      <tr>
        {headers_html}
      </tr>
      {rows_html}
    </table>
    '''
    return table_html

def build_markdown_from_observations(observations):
    markdown = ''

    for entry in observations:
        date = datetime.fromisoformat(entry['obsDt']).strftime('%m/%d')
        markdown += f'[{date} {entry["species"]} 🔗]({entry["ebird_link"]})\n📍{entry["locName"]}\n\n'

    return markdown