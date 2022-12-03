# Micro Rain Radar 2 (MRR-2) datalogger (MRR_2_datalogger)

Provides a reliable and simple datalogger for the MRR-2.

### Dependencies
- pyserial


### Install
`git clone git@github.com:ackermannluis/MRR_2_datalogger.git`

To install in your home directory, use:

`python setup.py install --user`

### Linux
you will need to run (on terminal) the following command to allow python access 
to the serial port
`sudo usermod -a -G tty YOUR_USER_NAME

### Use
- just run on the terminal by navegating to the source folder and running:
`python MRR_2_datalogger_main.py`
