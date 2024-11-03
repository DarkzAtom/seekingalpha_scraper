import pandas as pd

# Read the CSV file
df = pd.read_csv('authors_output.csv')  # Replace with your CSV filename

# Make the replacements
df['x_url'] = df['x_url'].replace('https://twitter.com/SeekingAlpha', '')
# df['x_handle'] = df['x_handle'].replace('SeekingAlpha', '')
df['linked_in_url'] = df['linked_in_url'].replace('https://www.linkedin.com/company/56547/', '')
# df['linked_in_id'] = df['linked_in_id'].replace('56547', '')

# Save the modified data back to CSV
df.to_csv('authors_output_refined.csv', index=False)

# Optional: Print first few rows to verify changes
print(df.head())