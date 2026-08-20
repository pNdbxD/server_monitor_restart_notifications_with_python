import requests
import smtplib
import os
import paramiko
import linode_api4
import time
import schedule

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')


def restart_server_and_container():
    # restart linode server
    print('Rebooting the server...')
    client = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = client.load(linode_api4.Instance, 102532369)
    nginx_server.reboot()

    # restart the application
    while True:
        nginx_server = client.load(linode_api4.Instance, 102532369)
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break


def send_notification(email_msg):
    print("Sending an email...")

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        message = f"Subject: SITE DOWN\n\n{email_msg}"
        smtp.sendmail(
            EMAIL_ADDRESS,
            EMAIL_ADDRESS,
            message
        )

def restart_container():
    print('Restarting the application...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='139.162.62.254', username='root', key_filename='/Users/edgar/.ssh/id_DO')
    # stdin, stdout, stderr = ssh.exec_command('docker ps')
    stdin, stdout, stderr = ssh.exec_command('docker start f3c8b60c0411')
    print(stdout.readlines())
    stdin, stdout, stderr = ssh.exec_command('docker ps')
    print(stdout.readlines())
    ssh.close()


def monitor_application():
    try:
        response = requests.get('http://139-162-62-254.ip.linodeusercontent.com:8080/')
        print(f'Application returned {response.text=}')
        if response.status_code == 200:
            print('Application is running successfully!')
            msg = f'Application returned {response.status_code}'
            send_notification(msg)
            restart_container()
        else:
            print('Application Down. Fix it!')
            msg = f'Application returned {response.status_code}'
            send_notification(msg)
            restart_container()
    except Exception as ex:
        print(f'Connection error happened: {ex}')
        msg = 'Application not accessible at all'
        send_notification(msg)
        restart_server_and_container()

# monitor_application()
# send_notification('Application is running successfully!')
# restart_server_and_container()
schedule.every(5).minutes.do(monitor_application)

while True:
    schedule.run_pending()
