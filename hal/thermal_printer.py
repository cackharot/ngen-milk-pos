#!/usr/bin/env python 
#coding=utf-8

import serial, time

#===========================================================#
# RASPBERRY PI (tested with Raspbian Jan 2012):
# - Ensure that ttyAMA0 is not used for serial console access:
# edit /boot/cmdline.txt (remove all name-value pairs containing 
# ttyAMA0) and comment out last line in /etc/inittab.
# - Fix user permissions with "sudo usermod -a -G dialout pi"
# - Reboot
# - Ensure that the SERIALPORT setting is correct below
#
# BEAGLE BONE: 
# Mux settings (Ängström 2012.05, also work on ubuntu 12.04):
# echo 1 > /sys/kernel/debug/omap_mux/spi0_sclk
# echo 1 > /sys/kernel/debug/omap_mux/spi0_d0 
#===========================================================#

    
class ThermalPrinter(object):
    """ 
        
        Thermal printing library that controls the "micro panel thermal printer" sold in
        shops like Adafruit and Sparkfun (e.g. http://www.adafruit.com/products/597). 
        Mostly ported from Ladyada's Arduino library 
        (https://github.com/adafruit/Adafruit-Thermal-Printer-Library) to run on
        BeagleBone and Raspberry Pi.

        Currently handles printing image data and text, but the rest of the
        built-in functionality like underlining and barcodes are trivial
        to port to Python when needed.

        If on BeagleBone or similar device, remember to set the mux settings
        or change the UART you are using. See the beginning of this file for
        default setup.

        Thanks to Matt Richardson for the initial pointers on controlling the
        device via Python.

        @author: Lauri Kainulainen 

    """

    # default serial port for the Beagle Bone
    #SERIALPORT = '/dev/ttyO2'
    # this might work better on a Raspberry Pi
    SERIALPORT = '/dev/ttyAMA0'

    BAUDRATE = 19200
    TIMEOUT = 3

    # pixels with more color value (average for multiple channels) are counted as white
    # tweak this if your images appear too black or too white
    black_threshold = 48
    # pixels with less alpha than this are counted as white
    alpha_threshold = 127

    printer = None

    _ESC = chr(27)

    # These values (including printDensity and printBreaktime) are taken from 
    # lazyatom's Adafruit-Thermal-Library branch and seem to work nicely with bitmap 
    # images. Changes here can cause symptoms like images printing out as random text. 
    # Play freely, but remember the working values.
    # https://github.com/adafruit/Adafruit-Thermal-Printer-Library/blob/0cc508a9566240e5e5bac0fa28714722875cae69/Thermal.cpp
    
    # Set "max heating dots", "heating time", "heating interval"
    # n1 = 0-255 Max printing dots, Unit (8dots), Default: 7 (64 dots)
    # n2 = 3-255 Heating time, Unit (10us), Default: 80 (800us)
    # n3 = 0-255 Heating interval, Unit (10us), Default: 2 (20us)
    # The more max heating dots, the more peak current will cost
    # when printing, the faster printing speed. The max heating
    # dots is 8*(n1+1). The more heating time, the more density,
    # but the slower printing speed. If heating time is too short,
    # blank page may occur. The more heating interval, the more
    # clear, but the slower printing speed.
    
    def __init__(self, heatTime=80, heatInterval=2, heatingDots=7, serialport=SERIALPORT):
        self.printer = serial.Serial(serialport, self.BAUDRATE, timeout=self.TIMEOUT)
        self.printer.write(self._ESC) # ESC - command
        self.printer.write(chr(64)) # @   - initialize
        self.printer.write(self._ESC) # ESC - command
        self.printer.write(chr(55)) # 7   - print settings
        self.printer.write(chr(heatingDots))  # Heating dots (20=balance of darkness vs no jams) default = 20
        self.printer.write(chr(heatTime)) # heatTime Library default = 255 (max)
        self.printer.write(chr(heatInterval)) # Heat interval (500 uS = slower, but darker) default = 250

        # Description of print density from page 23 of the manual:
        # DC2 # n Set printing density
        # Decimal: 18 35 n
        # D4..D0 of n is used to set the printing density. Density is 50% + 5% * n(D4-D0) printing density.
        # D7..D5 of n is used to set the printing break time. Break time is n(D7-D5)*250us.
        printDensity = 15 # 120% (? can go higher, text is darker but fuzzy)
        printBreakTime = 15 # 500 uS
        self.printer.write(chr(18))
        self.printer.write(chr(35))
        self.printer.write(chr((printDensity << 4) | printBreakTime))

    def reset(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(64))

    def linefeed(self):
        self.printer.write(chr(10))

    def justify(self, align="L"):
        pos = 0
        if align == "L":
            pos = 0
        elif align == "C":
            pos = 1
        elif align == "R":
            pos = 2
        self.printer.write(self._ESC)
        self.printer.write(chr(97))
        self.printer.write(chr(pos))

    def bold_off(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(69))
        self.printer.write(chr(0))

    def bold_on(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(69))
        self.printer.write(chr(1))

    def font_b_off(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(33))
        self.printer.write(chr(0))

    def font_b_on(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(33))
        self.printer.write(chr(1))

    def underline_off(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(45))
        self.printer.write(chr(0))

    def underline_on(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(45))
        self.printer.write(chr(1))

    def inverse_off(self):
        self.printer.write(chr(29))
        self.printer.write(chr(66))
        self.printer.write(chr(0))

    def inverse_on(self):
        self.printer.write(chr(29))
        self.printer.write(chr(66))
        self.printer.write(chr(1))

    def upsidedown_off(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(123))
        self.printer.write(chr(0))

    def upsidedown_on(self):
        self.printer.write(self._ESC)
        self.printer.write(chr(123))
        self.printer.write(chr(1))
        
    def barcode_chr(self, msg):
        self.printer.write(chr(29)) # Leave
        self.printer.write(chr(72)) # Leave
        self.printer.write(msg)     # Print barcode # 1:Abovebarcode 2:Below 3:Both 0:Not printed
        
    def barcode_height(self, msg):
        self.printer.write(chr(29))  # Leave
        self.printer.write(chr(104)) # Leave
        self.printer.write(msg)      # Value 1-255 Default 50
        
    def barcode_height(self):
        self.printer.write(chr(29))  # Leave
        self.printer.write(chr(119)) # Leave
        self.printer.write(chr(2))   # Value 2,3 Default 2
        
    def barcode(self, msg):
        """ Please read http://www.adafruit.com/datasheets/A2-user%20manual.pdf
            for information on how to use barcodes. """
        # CODE SYSTEM, NUMBER OF CHARACTERS        
        # 65=UPC-A    11,12    #71=CODEBAR    >1
        # 66=UPC-E    11,12    #72=CODE93    >1
        # 67=EAN13    12,13    #73=CODE128    >1
        # 68=EAN8    7,8    #74=CODE11    >1
        # 69=CODE39    >1    #75=MSI        >1
        # 70=I25        >1 EVEN NUMBER           
        self.printer.write(chr(29))  # LEAVE
        self.printer.write(chr(107)) # LEAVE
        self.printer.write(chr(65))  # USE ABOVE CHART
        self.printer.write(chr(12))  # USE CHART NUMBER OF CHAR 
        self.printer.write(msg)
        
    def print_text(self, msg, chars_per_line=None):
        """ Print some text defined by msg. If chars_per_line is defined, 
            inserts newlines after the given amount. Use normal '\n' line breaks for 
            empty lines. """ 
        if chars_per_line == None:
            self.printer.write(msg)
        else:
            l = list(msg)
            le = len(msg)
            for i in xrange(chars_per_line + 1, le, chars_per_line + 1):
                l.insert(i, '\n')
            self.printer.write("".join(l))
            print "".join(l)

    def print_markup(self, markup):
        """ Print text with markup for styling.

        Keyword arguments:
        markup -- text with a left column of markup as follows:
        first character denotes style (n=normal, b=bold, u=underline, i=inverse, f=font B)
        second character denotes justification (l=left, c=centre, r=right)
        third character must be a space, followed by the text of the line.
        """
        lines = markup.splitlines(True)
        for l in lines:
            style = l[0]
            justification = l[1].upper()
            text = l[3:]

            if style == 'b':
                self.bold_on()
            elif style == 'u':
               self.underline_on()
            elif style == 'i':
               self.inverse_on()
            elif style == 'f':
                self.font_b_on()

            self.justify(justification)
            self.print_text(text)
            if justification != 'L':
                self.justify()

            if style == 'b':
                self.bold_off()
            elif style == 'u':
               self.underline_off()
            elif style == 'i':
               self.inverse_off()
            elif style == 'f':
                self.font_b_off()