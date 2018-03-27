//globals
var map; //map object. used by leaflet to create map layer 
var geojson;//geojson object. used by leaflet to create geoJSON layer
var legend;//used by leaflet to create the legend

$(document).ready(function() {

	//Map layer centered on wheaton campus with zoom level 17
	map = L.map('map', {zoomControl: false}).setView([41.966975161113574,-71.18357218801937], 17); 
	//Open street map for the map tile layer
	L.tileLayer('http://{s}.tiles.mapbox.com/v3/austinrg7.jl4274hk/{z}/{x}/{y}.png', {
		attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
		maxZoom: 20
	}).addTo(map);
	//Position zoom control
	new L.control.zoom({
		position: 'topright'
	}).addTo(map);
    //Wait a bit for data to be processed before doing the following 
	setTimeout(resetEachDorm, 2000);
	setTimeout(continueLeaflet, 3000);

});
/*
	Input/Ouput:none,but
	clears the old geojson layer
	creates a new geojson layer with updated data 
*/
function redrawMap() {
	geojson.clearLayers();
	geojson.addData(dormData);
}
/*
	Input/Ouput:none,but
	clears the old legend layer
	creates a new legend layer with updated data 
*/
function resetScales() {
	$("#legendDiv").remove();//Remove old legend
	legend.onAdd(map);
	legend.addTo(map);//Add new one
}
/*
	Input/Ouput:none,but
	handles the dynamic dorm data functionality which is displayed on the top left corner of the map
	when hovering over a dorm
*/
function continueLeaflet() {
	// control that shows state info on hover
	var info = L.control({position: 'topleft'});
	//create div to hold the info of the dorm user is hovering over and uodate that div with appropraite info
	info.onAdd = function (map) {
	  this._div = L.DomUtil.create('div', 'info');
	  this.update();
	  return this._div;
	};
	//Put the appropriate info in the div
	info.update = function (props) {
		var perWhat;
		if (labelDelim == "hour")
			perWhat = " per hour";
		else if (labelDelim == "day")
			perWhat = " per day";
		else if (labelDelim == "week")
			perWhat = " per week";

		props ? checkDorm(props) : 'Hover over a dorm'; //If true show dorm values else show instructions to show data
		this._div.innerHTML = '<h6>Wheaton Residential Power Use</h6>' +  (props ?
		'<b>' + props.value + '</b><br />' + props.power + ' kW/h' + '<br />$' + props.cost + perWhat +"<br /><i>Avg. values between selected dates</i>"
		: 'Hover over a dorm');
	};
	//add it to the map
	info.addTo(map);

	/*
		Input: props which is an object with dorm data 
		Ouput: i receives an interger value if hovering over an object on the map with properties else it's undefined 
	*/
	function checkDorm(props) {
		var i = _.indexOf(_.keys(avgKWh), props.name);
	}
	/*
		Input: a data value,d, and a string, "dorm" if for dorm color and "label" if for legend color 
		Ouput: the color for the dorm or the legend
	*/
	function getColor(d, forWhat) {
		//Functions for hour,day,week function identically except the vals in the ifs are different
		if (labelDelim == "hour") {
			if (forWhat == "label") {
				//d vales for legend 
				return d > 1000 ? '#FF0000' :
					   d > 500  ? '#FF4322' :
					   d > 200  ? '#FFD744' :
					   d > 100  ? '#FFAC66' :
					   d > 50   ? '#FFD089' :
					   d > 20   ? '#FFEBAB' :
					   d > 10   ? '#FFFACD' :
								  '#FDFFF0';
			}
			else {
				//dorm color based on data 
				return d > 10 ? '#FF0000' :
					   d > 5  ? '#FF4322' :
					   d > 2  ? '#FFD744' :
					   d > 1  ? '#FFAC66' :
					   d > .5   ? '#FFD089' :
					   d > .2   ? '#FFEBAB' :
					   d > .1   ? '#FFFACD' :
								  '#FDFFF0';
			}
		}

		else if (labelDelim == "day") {
			if (forWhat == "label") {
				return d > 1000 ? '#FF0000' :
					   d > 500  ? '#FF4322' :
					   d > 200  ? '#FFD744' :
					   d > 100  ? '#FFAC66' :
					   d > 50   ? '#FFD089' :
					   d > 20   ? '#FFEBAB' :
					   d > 10   ? '#FFFACD' :
								  '#FDFFF0';
			}
			else {
				return d > 500 ? '#FF0000' :
					   d > 300  ? '#FF4322' :
					   d > 200  ? '#FFD744' :
					   d > 100  ? '#FFAC66' :
					   d > 50   ? '#FFD089' :
					   d > 20   ? '#FFEBAB' :
					   d > 10   ? '#FFFACD' :
								  '#FDFFF0';
			}
		}

		else {
			if (forWhat == "label") {
				return d > 1000 ? '#FF0000' :
					   d > 500  ? '#FF4322' :
					   d > 200  ? '#FFD744' :
					   d > 100  ? '#FFAC66' :
					   d > 50   ? '#FFD089' :
					   d > 20   ? '#FFEBAB' :
					   d > 10   ? '#FFFACD' :
								  '#FDFFF0';
			}

			else {
				return d > 2900 ? '#FF0000' :
					   d > 2000  ? '#FF4322' :
					   d > 1500  ? '#FFD744' :
					   d > 1000  ? '#FFAC66' :
					   d > 500   ? '#FFD089' :
					   d > 300   ? '#FFEBAB' :
					   d > 100   ? '#FFFACD' :
								  '#FDFFF0';
			}
		}
	}
	/*
		Input: a geojson feature (coordinates that roughtly outline each dorm) that needs to be filled with the proper color
		Output: the css necessary to properly style the input geojson feature 
	*/
	function style(feature) {
	  //all outlines have same style excpet for fill color which is determined based on dorm's kwh value 
	  return {
		weight: 2,
		opacity: 1,
		color: 'white',
		dashArray: '3',
		fillOpacity: 0.7,
		fillColor: getColor(feature.properties.power, "dorm") 
	  };
	}

	/*
		Input: a geojson object the user has placed the cursor over 
		Output: none, but changes the outline around the dorm the cursor is over from white to dark gray to emphasize 
				that is the dorm for which data is being displayed 
	*/
	function highlightFeature(e) {
	  var layer = e.target;

	  layer.setStyle({
		weight: 5,
		color: '#666',
		dashArray: '',
		fillOpacity: 0.7
	  });

	  if (!L.Browser.ie && !L.Browser.opera) {
		  layer.bringToFront();
	  }

	  info.update(layer.feature.properties);
	}
	/*
		Input: a geojson object the user has moved the cursor away from
		Output: none, but changes the outline around the dorm the cursor is over back to white 
	*/
	function resetHighlight(e) {
	  geojson.resetStyle(e.target);
	  info.update();
	}

	function onEachFeature(feature, layer) {
	  layer.on({
		mouseover: highlightFeature,
		mouseout: resetHighlight
	  });
	}

	//Add the properly colored regions around the corresponding dorm
	geojson = L.geoJson(dormData, {
	  style: style,
	  onEachFeature: onEachFeature
	}).addTo(map);

	//Create the layer for the legend in the bottom right
	legend = L.control({position: 'bottomright'});

	/*
		Input: the map layer
		Output: div containing the properly labeled legend
	*/
	legend.onAdd = function (map) {
		//Legend labels
		var valsHour = [0, .1, .2, .5, 1, 2, 5, 10];
		var valsDay = [0, 10, 20, 50, 100, 200, 300, 500];
		var valsWeek = [0, 100, 300, 500, 1000, 1500, 2000, 2900];
		var valsToUse = [];

		//Logic to properly assign legend labels
		switch (labelDelim) {
			case "hour": valsToUse = valsHour;
					break;
			case "day": valsToUse = valsDay;
					break;
			case "week": valsToUse = valsWeek;
					break;
			default: valsToUse = valsHour;
					break;
		}
		//legend div created static info assigned
		var div = L.DomUtil.create('div', 'info legend'),
		                      vals = valsToUse,
		                      grades = [0, 10, 20, 50, 100, 200, 500, 1000],
		                      labels = [],
		                      from, to;
		//Get dynamic vqls required for legend div
		for (var i = 0; i < grades.length; i++) {
			
			from = grades[i];
			to = grades[i + 1];
			var labelFrom = vals[i];
			var labelTo = vals[i + 1];

			labels.push(
			  '<i style="background:' + getColor(from + 1, "label") + '"></i> ' +
			  labelFrom + (labelTo ? '&ndash;' + labelTo : '+'));
		}
		//give the div an id
		div.id = "legendDiv";
		//join the label and a break to complete the legend div
		div.innerHTML = labels.join('<br>');
		return div;
	};
	//add the legend to the map layer
	legend.addTo(map);
}