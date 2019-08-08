**Collaborators Wanted!!**

If you would like to contribute, comment [here](https://github.com/saildot4k/MSS54-XDFs/issues/6) and I will invite you to the repository as a collaborator. If you find an issue, please fix for all versions. It would be great to make this a living project once again.


# MSS54-XDFs
MSS54 and MSS54HP XDFs to be used with [TunerPro](http://www.tunerpro.net/)

Use [BMW FLASH](http://bimmersoftware.com/bmwflash) or [MSS Flasher](http://www.msstuning.com/mssflasher.html) to download and upload your .bins to your MSS54/HP.

[ECUWorx MSS5X Binary Tool](http://www.ecuworx.co.uk/uploads/MSS52_54_Binary_Modificaton_Tool_V1.5.3D.exe) and [ChipFile Browser](https://sourceforge.net/projects/chipfilebrowser/) are more great tools that will modify a small amount of parameters, but also will inform you which version of the DME you have. IE: 21132300**1801**J424

The link below to m3forum is vital to the usage of these tunerpro files:

[M3 Forum Comprehensive MSS54/HP Coding](http://www.m3forum.net/m3forum/forumdisplay.php?f=109)

PLEASE READ the [DIY DME Modification.pdf](https://github.com/saildot4k/MSS54-XDFs/raw/master/DIY%20DME%20Modification.pdf) which explains finding your version and which cables and modifications are necessary.

**To Download**: Github only supports downloading the whole repository:
[Click Here for download](https://github.com/saildot4k/MSS54-XDFs/archive/master.zip)

**YouTube Tutorial**:

[MSS54 ECU Tutorial Part 1: Tools and Reading/Writing to your ECU](https://youtu.be/jihFbGqWqjg)

[MSS54 ECU Tutorial Part 2: Swap Coding](https://youtu.be/SqrSyWNfMe8)

**General disclaimer:**
WARNING: These definition files are created as the result of the extremely complex and time consuming process of reverse-engineering the factory ECU. Because of this complexity, it is necessary to make certain assumptions and, therefore, it is impossible to always deal in absolutes in regards to representations made by these definitions. In addition, due to this complexity and the numerous variations among different ECUs, it is also impossible to guarantee that the definitions will not contain errors or other bugs. What this all means is that there is the potential for bugs, errors and misrepresentations which can result in damage to your motor, your ECU as well the possibility of causing your vehicle to behave unexpectedly on the road, increasing the risk of death or injury. Modifications to your vehicle's ECU may also be in violation of local, state and federal laws. By using these definition files, either directly or indirectly, you agree to assume 100% of all risk and creators of and contributors to these definitions shall not be held responsible for any damages or injuries you receive. This product is for advanced users only. There are no safeguards in place when tuning with TunerPro or any of these tools. As such, the potential for serious damage and injury still exists, even if the user does not experience any bugs or errors. As always, use at your own risk.  These definitions are created for FREE without any sort of guarantee. The developers cannot be held liable for any damage or injury incurred as a result of these definitions. USE AT YOUR OWN RISK.

 Tips:

 - the most basic items are on lvl 1 with English best guess translations
 - the most advanced are on lvl 5
 - level 10 has the same items as 1-5 but with BMW titles

**EWS Delete not included in XDFs.**
To delete, use your hex editor of choice and search for: 64 00 5A 00 00
Change the second byte to a non 00 value IE:             64 FF 5A 00 00
The BYTE to change is located at 0x60 for MSS54 and 0x8A for MSS54HP

```  
In the description of each item you will find some information about the validity of the search results.

NearbyBlockMatch: 20   % This means that there are 20/20 nearby items that moved together in a block.  This means that it is very likely that this item is correct
Matched Length: 7      % This is the length of the search that resulted in the find of this address
MatchRatio: 1.00       % Ratio of data value matches to a2l data - 1.00 means all data matches a2l
HasDuplicate?: No      % This tells you weather another item was found to be at this address as well. - only one can be correct.
BlockFound: 0          % 1: This variable was found using block tactics 0: found using search tactics only.

Example:
K_LA_FMIN  309C
HW:519 Version:211322001701J424
Created by find routine V0.35
BMWFlash/Galleto File Orientation [Slave Master]
Matched Length: 7  MatchRatio: 1.00
BlockFound: 0 NearbyBlockMatch: 20 Var: 830 HasDuplicate?: No
Units- "-"  
Function: Lambda  SizeChange: 0
```

```
K - constants, ie bit switches, flags, etc
KL - Kennlinnie - dataline, for example the linearization curves for sensors
KF - Kennfeld - Map table
The format usually sticks to type_datacontent_axis_axis so KF_TI_N_RF is map:injection:rpm:relative filling
  ```

| **Abbreviation** | **Function (German)** | **Function (Common English)** |
| --- | --- | --- |
| AR | ANTIRUCKELFUNKTION | Anti-bucking |
| AQ | AQUER | aquer |
| AUSS | Aussetzerkennung | Misfire code/detection |
| BA | BA | ?? |
| BZ | Betriebszustaende | Operating states |
| CAN | CAN_Schnittstelle | CAN bus interface/control |
| CAN | CAN_Schnittstelle-Slave | CAN bus interface/control slave |
| DA | D/A_Konfiguration | Digital/Analog conversion/configuration |
| DKBA | DKBA | Contains Alpha-N map |
| DWF | Drehzahlwarnfeld | Speed warning field |
| DSV | Druckspeicherventil | Accumulator valve |
| DYN | Dynamik | dynamics |
| EDK | EDK | Throttle Body |
| EDISI | EDK_Soll_Ist | EDK actual |
| EGAS | EGAS | Electronic Throttle system |
| ?? | Eigendiagnose | self-diagnosis |
| TI | Einspritzung | injection |
| ELU | Elektroluefter | electric fan |
| FGR | FGR | Cruise Control |
| FR | FUELLUNGSREGLER | Combustion controller (adapt values) |
| ?? | Fehlerfilter Kontrolle | error filter |
| VDIAG | Fz_Geschwindigkeit | Vehicle speed |
| GANG | Gangerkennung | Gear Recognition/Detection |
| KATH | Katheiz_Funktion | Catalytic heater function |
| KATS | Katschutz | Catalytic protection |
| KKOS | Klimaanlage | air conditioning |
| KM | Klopfen | knock |
| EKP | Kraftstoffpumpe | Fuel pump |
| LLR | LEERLAUFREGLER | Idle control |
| ?? | Lambda | lambda |
| ?? | Lambda-OBD | Lambda OBD |
| ?? | Lambdadiagnose | lambda diagnosis |
| ?? | Lamdasondenheizung | Lambda probe heating |
| HFM | Lasterfassung | load detection |
| LU | Laufunruhe | rough running |
| LL | LeerLaufSYNChornisation | Idle synchronization |
| LFR | Leerlaufregelung | Idle speed control |
| LLS | Leerlaufsteller | Idle adjuster |
| ?? | Messwerte | Observations |
| MD | Momentenmanager | Moment Manager |
| NO_FUNCTION | NO_FUNCTION | Miscellaneous |
| OEK | OEK | ?? |
| TOG | Oelniveaugeber | Oil level sensor/readings |
| PDR | PDR | varies with time (?) |
| ?? | Relativer_Oeffnungsquerschnitt | relative opening cross |
| SA_WE | SA_WE | Temperature functions |
| SSP | Saugstrahlpumpe | eductor |
| SWE | Schlechtweg-Erkennung | rough road detection |
| SLS, SLP, SLV | Sekundaerluftsystem | Secondary air system |
| SERVO | Servotronic | Servotronic adjustable steering ratio system (non-M3) |
| SK | Sicherheitskonzept | Security concept |
| START | Startrelais | Starter relay |
| ?? | System_Kontrolle | System control |
| TW | TPU_Synchronisation | TPU synchronization |
| TE, TEA | Tankentlueftung | Tank vent or Evaporator canister purge control |
| LDP | Tankleckdiagnose | Tank leak diagnosis |
| EVAN, AVAN | Vanos | EVAN: Intake Vanos, AVAN: Exhaust Vanos |
| ?? | Versionskontrolle | version control |
| TZ | Zuendung | ignition |
| SMG | smg | smg |
