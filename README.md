# MSS54-XDFs
MSS54 and MSS54HP XDFs to be used with TunerPro @ http://www.tunerpro.net/

Use http://bimmersoftware.com/bmwflash or http://www.msstuning.com/mssflasher.html to download and upload your .bins to your MSS54/HP.

The link below to m3forum is vital to the usage of these tunerpro files:

http://www.m3forum.net/m3forum/forumdisplay.php?f=109

Also please read the DIY DME Modification.pdf which explains finding your version and which cables and modifications are necessary.


General disclaimer:

WARNING: These definition files are created as the result of the extremely complex and time consuming process of reverse-engineering the factory ECU. Because of this complexity, it is necessary to make certain assumptions and, therefore, it is impossible to always deal in absolutes in regards to representations made by these definitions. In addition, due to this complexity and the numerous variations among different ECUs, it is also impossible to guarantee that the definitions will not contain errors or other bugs. What this all means is that there is the potential for bugs, errors and misrepresentations which can result in damage to your motor, your ECU as well the possibility of causing your vehicle to behave unexpectedly on the road, increasing the risk of death or injury. Modifications to your vehicle's ECU may also be in violation of local, state and federal laws. By using these definition files, either directly or indirectly, you agree to assume 100% of all risk and creators of and contributors to these definitions shall not be held responsible for any damages or injuries you receive. This product is for advanced users only. There are no safeguards in place when tuning with TunerPro or any of these tools. As such, the potential for serious damage and injury still exists, even if the user does not experience any bugs or errors. As always, use at your own risk.  These definitions are created for FREE without any sort of guarantee. The developers cannot be held liable for any damage or injury incurred as a result of these definitions. USE AT YOUR OWN RISK.

 Tips:

 - the most basic items are on lvl 1 with English best guess translations
 - the most advanced are on lvl 5 
 - level 10 has the same items as 1-5 but with BMW titles
  
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

'''
  K - constants, ie bit switches, flags, etc
  KL - Kennlinnie - dataline, for example the linearisation curves for sensors
  KF - Kennfeld - Map table
  The format usually sticks to type_datacontent_axis_axis so KF_TI_N_RF is map:injection:rpm:relative filling
 '''
