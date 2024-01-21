import os
import yaml

def list_services(directory):
    services = {}
    for root, dirs, files in os.walk(directory):
        for name in files:
            with open(os.path.join(root, name)) as config:
                conf = yaml.safe_load(config)
                for service in conf:
                    if service in services:
                        print("conflict service:", service)
                    services[service] = conf[service]
    return services

print(list_services("/etc/monitoring/configs"))
