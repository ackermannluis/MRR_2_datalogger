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

import os
import serial
import time
import sys

output_path = 'C:/_temp/MRR_DATA/MRR_'
port_ = 'COM20'
height_resolution = '50'

while True:
    try:
        interface = serial.Serial(port=port_,
                                  baudrate=57600,
                                  parity=serial.PARITY_NONE,
                                  bytesize=serial.EIGHTBITS,
                                  stopbits=serial.STOPBITS_ONE,
                                  )
        print('initialized connection')

        # flush full telegram
        txt = 'SN'.encode()
        counter_ = 0
        while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
            counter_ += 1
            if counter_ > 10000:
                raise ValueError('hang while reading telegram, restarting connection')
            ibuffer = interface.read()
            txt += ibuffer
        print('buffer cleaned')

        # set height resolution
        heights_meters_dict={
            '10':b'10\x0326',
            '25':b'25\x0320',
            '30':b'30\x0324',
            '35':b'35\x0321',
            '40':b'40\x0323',
            '50':b'50\x0322',
            '100':b'100\x0316',
            '250':b'250\x0310',
            '300':b'300\x0314',
            '400':b'400\x0313',
            '500':b'500\x0312',
            '1000':b'1000\x0326',
        }
        set_height_resolution_command = b'\x02\x48\x53\x3d' + heights_meters_dict[height_resolution] + b'\x0a'
        interface.write(set_height_resolution_command)
        print('height resolution set to', height_resolution, 'meters')

        # flush full telegram
        txt = 'SN'.encode()
        counter_ = 0
        while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
            counter_ += 1
            if counter_ > 10000:
                raise ValueError('hang while reading telegram, restarting connection')
            ibuffer = interface.read()
            txt += ibuffer
        print('buffer cleaned')

        print('-' * 40)
        print('starting acquisition loop')


        while True:

            # read full telegram
            txt = 'SN'.encode()
            while interface.inWaiting().bit_length() > 0 or txt.decode()[-1] != '\x04':
                counter_ += 1
                if counter_ > 10000:
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


                print(time.strftime('%Y-%m-%d_%H:%M:%S', time_), 'logged MRR data to file')
            else:
                print('skipping time stamp as telegram was received incomplete')

            time.sleep(3)

        # interface.close()
    except BaseException as error_msg:
        line_number = sys.exc_info()[-1].tb_lineno
        print('error in line {0}, error message:\n{1}'.format(line_number, error_msg))
        try:
            print('trying to close the connection to open it again (reset it)')
            interface.close()
            time.sleep(5)
            print('successfully closed!')
        except:
            pass




