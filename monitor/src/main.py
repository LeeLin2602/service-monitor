import os
import yaml
import sqlite3
from datetime import datetime, timedelta
import subprocess
import threading
import queue
import time
import mail
import config


def read_yaml(path):
    data = {}
    with open(path) as config:
        conf = yaml.safe_load(config)
        for unit in conf:
            if unit in data:
                print("conflict service:", unit)
            data[unit] = conf[unit]
    return data

def list_services(directory):
    services = {}
    for root, dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            if path.endswith(".yaml") or path.endswith(".yml"):
                services.update(read_yaml(path))
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

def update_fail_db(service, result):
    global mail_service, service_fail_log, contact_groups

    print(service['service'], ":", result)
    
    if service_fail_log[service['service']] != result[0]:
        subject = f"{service['service']} status changed!"
        status_mapping = {-1: "pending",
                          0: "healthy", 
                          1: "unknown", 
                          2: "warning",
                          3: "danger",
                          4: "dead"}
        body = f"From {status_mapping[service_fail_log[service['service']]]} " + \
               f"To {status_mapping[result[0]]}, with message: {result[1]}."
        for group in service['notify']:
            recepients = contact_groups[group]
            for recepient in recepients['members']:
                mail_service.send_mail(recepient, subject, body)
    
    service_fail_log[service['service']] = result[0]

mail_service = mail.MailService(config.SMTP_SERVER, config.SMTP_PORT, config.SMTP_USER, config.SMTP_PASS, config.SMTP_FROM)
service_queue = queue.Queue()
service_fail_log = {}
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_status (
        service VARCHAR(256) PRIMARY KEY,
        polltime DATETIME,
        waiting INTEGER
    );
""")

contact_groups = read_yaml("/etc/monitoring/notify_group.yaml")
services = list_services("/etc/monitoring/configs")

for service in services:
    service_fail_log[service] = -1
    services[service]['service'] = service
    service = services[service]
    cursor.execute("INSERT INTO service_status (service, polltime, waiting) VALUES (?, ?, ?)", (service['service'], datetime.now(), 0))
conn.commit()

while True:
    check_services(services, cursor, service_queue)
    while not service_queue.empty():
        service = services[service_queue.get()]
        result = run_subprocess(service)
        update_fail_db(service, result)
    time.sleep(1)
