//Globals
var indexPage = true;//Boolean. True if on the index (heat map) page false otherwise
var linePage = false;//Boolean. True ig on the consumption graph false otherwise

/*
Input/Output: none, but
Resets the leaflet map to be centered on the center of campus and to the default zoom level
*/
function resetMap() {
	map.setView([41.966975161113574,-71.18357218801937], 17);
}