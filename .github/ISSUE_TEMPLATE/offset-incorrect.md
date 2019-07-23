---
name: Offset Incorrect
about: How to report which XDF and Parameter Offset to correct
title: 'XDF XXXX: Parameter Offset Incorrect'
labels: bug
assignees: ''

---

**XDF Version**
XDF XXXX

**Parameter to Correct ie K_LA_FMIN**
Paramter: XXXX

**Parameter Type: Delete those that do not apply**
Scalar
Table
Function

**XML Data to replace in source**
For example:
Data between <*XDFTABLE* uniqueid="0x*XX*" vislevel="*X*" flags="*X*x*X*"> <*XDFTable*>
Data between <*XDFCONSTANT* uniqueid="0x*XX*" vislevel="*X*" flags="*X*x*X*"> <*XDFCONSTANT*>
Data between <*XDFFUNCTION* uniqueid="0x*XX*" vislevel="*X*" flags="*X*x*X*"> <*XDFFUNCTION*>
