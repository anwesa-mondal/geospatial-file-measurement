import fiona


if "KML" not in fiona.supported_drivers:
    fiona.drvsupport.supported_drivers["KML"] = "rw"
if "LIBKML" not in fiona.supported_drivers:
    fiona.drvsupport.supported_drivers["LIBKML"] = "rw"
