import os
import yaml
import sqlite3
from datetime import datetime, timedelta
import subprocess
import threading
import queue
import time


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

def run_subprocess(service):
    global conn
    cursor = conn.cursor()
    command = service['command']
    env = service['parameters']
    env_str = {k: str(v) for k, v in env.items()}

    process = subprocess.Popen(os.path.join('/usr/lib/monitoring/utils/', command),
                               env=env_str,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)

    stdout, stderr = process.communicate()

    new_polltime = datetime.now() + timedelta(seconds=service['interval'])
    cursor.execute("UPDATE service_status SET polltime = ?, waiting = 0 WHERE service = ?",
               (new_polltime, service['service']))

    conn.commit()
    return (process.returncode, f"{stderr}:{stdout}")

def check_services(services, cursor, service_queue):
    now = datetime.now()
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute("SELECT service FROM service_status WHERE polltime <= ? AND waiting = 0", (now,))
    services = cursor.fetchall()
    cursor.execute("UPDATE service_status SET waiting = 1 WHERE polltime <= ?", (now,))
    cursor.execute("COMMIT;")

    for service in services:
        service_queue.put(service[0])


service_queue = queue.Queue()
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_status (
        service VARCHAR(256) PRIMARY KEY,
        polltime DATETIME,
        waiting INTEGER
    );
""")


services = list_services("/etc/monitoring/configs")

for service in services:
    services[service]['service'] = service
    service = services[service]
    cursor.execute("INSERT INTO service_status (service, polltime, waiting) VALUES (?, ?, ?)", (service['service'], datetime.now(), 0))

conn.commit()

while True:
    check_services(services, cursor, service_queue)
    while not service_queue.empty():
        service = services[service_queue.get()]
        
        print(service['service'], run_subprocess(service))
    
    time.sleep(1)
