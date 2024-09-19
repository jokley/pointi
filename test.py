# import json

# # Open and read the JSON file
# with open('AL7AL051_Result.json', 'r') as file:
#     data = json.load(file)

# # Print the content of the JSON file
# print(data)

# # Access individual fields
# print("Name:", data["name"])
# print("Age:", data["age"])
# print("City:", data["city"])
# print("Skills:", ", ".join(data["skills"]))

import json
import re

# Open and read the raw JSON file as text
with open('AL7AL051_Result.json', 'r') as file:
    content = file.read()

# Define a regex pattern to match missing values (e.g., `"key": ,`)
# It looks for a key followed by a colon and a comma, indicating a missing value
pattern = re.compile(r'\"(\w+)\":\s*,') 

# Replace the missing values with `null`
# The pattern will match keys without values and replace them with `"key": null`
fixed_content = pattern.sub(r'"\1": null,', content)

# Optionally, print the fixed content for debugging
print("Fixed JSON content:\n", fixed_content)

# Load the fixed JSON content
data = json.loads(fixed_content)

# Print the final data
print("Parsed JSON Data:\n", data)

# Optionally, save the fixed content back to a file
with open('fixed_data.json', 'w') as file:
    file.write(fixed_content)

