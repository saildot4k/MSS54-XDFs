To convert your MSS54HP to a "CSL Clone" without the H-Bridge to run the intake flap, flash the included Full Binary in this folder, then the 0401 partial. You may use the 0401 CSL XDFs to modify the "tune".

The "Paffy" full binary is the original modified version which allowed the HP to run the CSL software. However reading error codes is broken. The "Terra" full binary fixes this. Both have stock CSL "tunes". Note: this means you may have to fix some tables for non-CSL cams, which you can copy from other partials.

Notes from Terra as seen [here](https://nam3forum.com/forums/forum/special-interests/coding-tuning/26354-fix-for-error-code-reading-on-mssflasher-csl-tune). Quoted:

The CSL binaries Paffy has on the MSSFlasher website do not have all the changes necessary to play 100% nice with the non-CSL bootloader. It mostly works, but notably the ability to read error codes is broken

Flash only the program - leave your tune as is (the tune built into the file above is just a standard CSL tune). IE: Flash full binary, then flash your tune, the partial, back. REMEMBER, ALWAYS BACKUP YOUR TUNE AND FULL BINARY!

Read off your tune and change 0xE002 from 00 to 01, then flash that tune back to your car.

That program also has the changes to trigger the alternator light over the CAN-bus. To enable that, you'd set 0x5968 to 01 05 0A and enable "GENERATOR_UEBER_CAN" in your instrument cluster. If you already have the direct wiring done, then you could leave it alone and things will function like they did before.
