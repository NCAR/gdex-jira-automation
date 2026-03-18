import yaml
import logging

def load_config_files(config_files: list = None) -> dict:
    configs = {}
    for file_path in config_files:
        try:
            with open(file_path, "r") as f:
                load_file = yaml.safe_load(f)
                configs.update(load_file)
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {file_path}. Error: {e}")
        except PermissionError as e:
            logging.error(f"Permission error while accessing config file {file_path}. Error: {e}")
        except yaml.YAMLError as e:
            logging.error(f"YAML error while parsing config file {file_path}. Error: {e}")
        except IsADirectoryError as e:
            logging.error(f"The path {file_path} is a directory, not a file. Error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while loading config file {file_path}. Error: {e}")
    return(configs)