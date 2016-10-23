mail2gcode
==

This is a python3 script that checks a mailbox for a format specific message, downloads it's attachments, processes the attachments, and replies to the sender with a zip file containing the generated code files. It expects to receive Gerber (RS-274X) files directly as attachments.

* **AUTHOR**: Enrique Condes
* **MAIL**: <enrique@shapeoko.com>

##Requirements:

This project requires that pcb2gcode is installed within the system. You can obtain it here: https://github.com/pcb2gcode/pcb2gcode

Before first usage, configFile.py **must be modified.**

##Development

(10/23/16) Add a location to put the downloaded attachments.
(10/23/16) Filter input files by regular expressions.
(10/18/16) Fix bug where the location of pcb2gcode could not be established if running through Cron
(10/17/16) Initial deployment

##Current status

Currently the pcb2gcode parameters are hard-coded within the code according to the ones we use. Probably you will want to modify them according to your specific needs. In a future release, they will be parsed from the body of the incoming mail.

Regular expressions have been implemented to allow easier customization of the input files names and extensions.

##Future features

- Support for zipped files as input.
- Parse pcb2gcode parameters from message body.
- Create and import pcb2gcode default settings file.
