#!/usr/bin/env python
# Copyright 2022
# author: Luis Ackermann <ackermann.luis@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import glob
import time
import os
import ftplib
import serial
from threading import Thread

# ################################################  USER VARIABLES  #################################################
# first port name to try
port_ = '/dev/ttyUSB0'
height_resolution = '150'

# place an empty file named __findmeMRR__ inside this directory in the folder where you want the files to be saved
output_path_base = '/media/pi/'

# define file prefix
file_prefix = 'MRR_E_'

# if enabled, the data will be also sent to the specified ftp on the start of a new day
enable_ftp_export = False
ftp_hostname = ''
ftp_username = ''
ftp_password = ''
ftp_path     = '/'

# enable this to print status reports to terminal instead of the log file
debug_ = False

# ################################################  USER VARIABLES  #################################################


def ftp_put_file(local_filename, remote_path,
                 host_name=None, user_name=None, password_=None):
    from pathlib import Path
    try:
        local_file_path = Path(local_filename)

        ftp = ftplib.FTP(host=host_name, user=user_name, passwd=password_)
        ftp.cwd(remote_path)

        with open(local_filename, 'rb') as local_file:
            ftp.storbinary(f'STOR {local_file_path.name}', local_file)

        ftp.quit()
    except:
        try:
            ftp.quit()
        except:
            pass
def ftp_get_file(remote_filename, local_path,
                 host_name=None, user_name=None, password_=None):
    from pathlib import Path
    remote_file_path = Path(remote_filename)

    ftp = ftplib.FTP(host=host_name, user=user_name, passwd=password_)

    with open(local_path + remote_file_path.name, 'wb') as local_file:
        ftp.retrbinary(f'RETR {remote_filename}', local_file.write)

    ftp.quit()
def list_files_recursive(path_, filter_str=None):
    # create list of raw spectra files
    file_list = []
    # r=root, d=directories, f = files
    if filter_str is None:
        for r, d, f in os.walk(path_):
            for file in f:
                filename_ = os.path.join(r, file)
                file_list.append(filename_.replace('\\','/'))
    else:
        for r, d, f in os.walk(path_):
            for file in f:
                if filter_str in file:
                    filename_ = os.path.join(r, file)
                    file_list.append(filename_.replace('\\', '/'))
    return sorted(file_list)
def log_status(text_):
    if debug_:
        print(text_)
    else:
        status_log_filename = output_path + 'status_log.txt'
        if os.path.isfile(status_log_filename):
            with open(status_log_filename, 'a') as file_:
                file_.write(str(text_) + '\n')
        else:
            with open(status_log_filename, 'w') as file_:
                file_.write(str(text_) + '\n')
def list_available_serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/ttyUSB[A-Za-z]*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


time.sleep(10)
output_path = list_files_recursive(output_path_base, '__findmeMRR__')[0][:-13] + file_prefix


com_ports_list = list_available_serial_ports()
error_encountered = False
current_try_port_index = 0
last_date = time.strftime('%Y%m%d', time.localtime())

while True:
    try:
        interface = serial.Serial(port=port_,
                                  baudrate=57600,
                                  parity=serial.PARITY_NONE,
                                  bytesize=serial.EIGHTBITS,
                                  stopbits=serial.STOPBITS_ONE,
                                  )
        log_status('initialized connection')

        # flush full telegram
        txt = 'SN'.encode()
        time_reading_start = time.time()
        while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
            if time.time() > time_reading_start + 60:
                raise ValueError('hang while reading telegram, restarting connection')
            ibuffer = interface.read()
            txt += ibuffer
        log_status('buffer cleaned')

        # set height resolution
        heights_meters_dict={
            '10':b'10\x0326',
            '25':b'25\x0320',
            '30':b'30\x0324',
            '35':b'35\x0321',
            '40':b'40\x0323',
            '50':b'50\x0322',
            '100':b'100\x0316',
            '150':b'150\x0313',
            '200':b'200\x0315',
            '250':b'250\x0310',
            '300':b'300\x0314',
            '400':b'400\x0313',
            '500':b'500\x0312',
            '1000':b'1000\x0326',
        }
        set_height_resolution_command = b'\x02\x48\x53\x3d' + heights_meters_dict[height_resolution] + b'\x0a'
        interface.write(set_height_resolution_command)
        log_status('height resolution set to ' + height_resolution + ' meters')

        # flush full telegram
        txt = 'SN'.encode()
        time_reading_start = time.time()
        while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
            if time.time() > time_reading_start + 60:
                raise ValueError('hang while reading telegram, restarting connection')
            ibuffer = interface.read()
            txt += ibuffer
        log_status('buffer cleaned')

        log_status('-' * 40)
        log_status('starting acquisition loop')


        while True:

            # read full telegram
            txt = 'SN'.encode()
            time_reading_start = time.time()
            while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
                if time.time() > time_reading_start + 60:
                    raise ValueError('hang while reading telegram, restarting connection')
                ibuffer = interface.read()
                txt += ibuffer
            time_ = time.localtime()
            date_ = time.strftime('%Y%m%d', time_)
            txt = txt.decode()
            txt_lines = txt.split('\n')
            txt_lines_clean = []
            for line_ in txt_lines:
                txt_lines_clean.append(line_[1:-4])
            txt_lines_clean[0] = 'MRR ' + time.strftime('%y%m%d%H%M%S', time_) + ' UTC ' + txt_lines_clean[0][3:]
            txt_lines_clean = txt_lines_clean[:-1]

            if len(txt_lines_clean) == 67:

                if os.path.isfile(output_path + date_ + '.raw'):
                    with open(output_path + date_ + '.raw', 'a') as file_:
                        for line_ in txt_lines_clean:
                            file_.write(line_)
                            file_.write('\n')
                else:
                    with open(output_path + date_ + '.raw', 'w') as file_:
                        for line_ in txt_lines_clean:
                            file_.write(line_)
                            file_.write('\n')
                    
                    if os.path.isfile(output_path + last_date + '.raw'):
                        last_date = time.strftime('%Y%m%d', time.localtime())

                        if enable_ftp_export:
                            ftp_thread = Thread(target=ftp_put_file,
                                                args=[output_path + last_date + '.csv',
                                                      ftp_path, ftp_hostname, ftp_username, ftp_password])
                            ftp_thread.run()

                log_status(time.strftime('%Y-%m-%d_%H:%M:%S', time_) + ' logged MRR data to file')
            else:
                log_status('skipping time stamp as telegram was received incomplete')

            time.sleep(3)
            error_encountered = False

    except BaseException as error_msg:
        try:

            if error_encountered:
                while True:
                    log_status('searching available ports')
                    com_ports_list = list_available_serial_ports()
                    if len(com_ports_list) > 0:
                        if current_try_port_index >= len(com_ports_list) - 1:
                            current_try_port_index = 0
                        else:
                            current_try_port_index += 1
                        port_ = com_ports_list[current_try_port_index]
                        break
                    else:
                        time.sleep(3)

            error_encountered = True
            line_number = sys.exc_info()[-1].tb_lineno
            log_status('error in line {0}, error message:\n{1}'.format(line_number, error_msg))

            log_status('trying to close the connection to open it again (reset it)')
            time.sleep(5)
            interface.close()
            time.sleep(5)
            log_status('successfully closed!')
        except:
            pass




