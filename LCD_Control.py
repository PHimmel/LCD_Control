from pyfirmata import Arduino, util, STRING_DATA
import paramiko
import subprocess
import re
from time import sleep

board = Arduino('/dev/ttyUSB0')

hostname = 'rpi1'
username = 'pi'
password = 'pi32pi32'
port = 22

get_temp = 'vcgencmd measure_temp'
get_volts = 'vcgencmd measure_volts'
get_cpu = 'mpstat 1 2 | awk \'END{print 100-$NF"%"}\''
get_ram = 'free -m|grep \"Mem\"|awk \'{print $3/($4+$3) * 100}\''

def send_info_to_lcd(text):
    board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(text))


class Pi():
    def __init__(self, number):
        self.number = number
        self.command = None
        self.output = None
        
    def get_info(self, command):
        self.command = command
        
        if self.number == 1:
            self.ssh_rpi1()
            return self.output
            
        if self.number == 4:
            self.ssh_rpi4()
            return self.output

    def ssh_rpi1(self):
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.load_system_host_keys()
            ssh.connect(hostname, port, username, password)
            stdin, stdout, stderr = ssh.exec_command(self.command)
            self.output = str(stdout.readlines())

    def ssh_rpi4(self):
        execute = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE)
        out, err = execute.communicate()
        self.output = str(out)

def extract(data, close):
    match = re.search('\d.*{}'.format(close), data)
    return match.group(0)

def data_for_lcd(pi, ram, cpu, temp):
    pi_data_1 = 'pi{}: RAM= {}%'.format(pi.number, ram)
    pi_data_2 = 'CPU={}% {}'.format(cpu, temp)
    return pi_data_1, pi_data_2
    
def main():
    pi1 = Pi(1)
    pi4 = Pi(4)
    
    alternate = 0
    while True:
        if alternate % 2 == 0:
            pi = pi1
        else:
            pi = pi4

        temp = extract(pi.get_info(get_temp), 'C')
        cpu = extract(pi.get_info(get_cpu), '%')
        ram = extract(pi.get_info(get_ram), r'\\')

        pi_sent_1, pi_sent_2 = data_for_lcd(pi, ram, cpu, temp)
        
        send_info_to_lcd(pi_sent_1)
        sleep(5)
        send_info_to_lcd(pi_sent_2)
        
        alternate += 1
        sleep(5)
    
main()

