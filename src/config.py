import yaml

# Load configurations from a YAML file
with open('./config.yaml', 'r') as file:
    config = yaml.safe_load(file)

configuration = config