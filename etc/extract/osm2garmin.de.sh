cat << EOF
Map data (c) OpenStreetMap contributors, https://www.openstreetmap.org
Map style (c) by OpenStreetMap.org, BBBike.org, openfietsmap.nl
Extracts created by BBBike, http://BBBike.org
$BBBIKE_EXTRACT_GARMIN_VERSION by http://www.mkgmap.org.uk


Please read the OSM wiki how to install the maps on your GPS device:

  https://wiki.openstreetmap.org/wiki/OSM_Map_On_Garmin#Installing_the_map_onto_your_GPS
  https://wiki.openstreetmap.org/wiki/OSM_Map_On_Garmin/Download


Diese Garmin Karte wurde erzeugt am: $date
Garmin Kartenstil: $mkgmap_map_style
GPS Rechteck Koordinaten (lng,lat): $BBBIKE_EXTRACT_COORDS
Script URL: $BBBIKE_EXTRACT_URL
Name des Gebietes: $city


Spenden sind willkommen! Du kannst uns via PayPal, Flattr oder Bankueberweisung
unterstuetzen: http://www.bbbike.org/community.de.html

Danke, Wolfram Schneider

--
http://www.BBBike.org - Dein Fahrrad-Routenplaner
EOF
