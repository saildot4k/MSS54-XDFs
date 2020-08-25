Reference the [Aux Fan Speeds Wiki here](https://github.com/saildot4k/MSS54-XDFs/wiki/Aux-Fan-Speeds)

If you use the E30 AC Pressure switch, then zero out the Aux Fan Speed tables for AC. If using the E46 AC Pressure Sensor, best to leave the values as stock. 

The AC digital turn signal routes through the K-Line via the E46 instrument cluster and CLimate Control, which creates a challenge as you most likely will have neither in your swap (especially the E46 Climate Control). GPertsons board added this functionality back via a [MBED LPC1768 Board](https://os.mbed.com/platforms/mbed-LPC1768/), custom coding and a custom PCB with TE MQS connector to the MBED board. I recommend a group gets together and has someone reverese engineer a solution that does not copy GPetersons board, unless you are able to buy his solution.
