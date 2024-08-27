url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

# Load the data
import requests
import json

response = requests.get(url)
data = response.json()

keys_wanted = ["input_cost_per_token", "output_cost_per_token", "max_tokens", "max_input_tokens", "max_output_tokens"]

del data["sample_spec"]
# Extract the keys we want
for model_entry in data:
    for key in list(data[model_entry].keys()):
        if key not in keys_wanted:
            del data[model_entry][key]

# save the data
with open("model_costs.json", "w") as f:
    json.dump(data, f)
