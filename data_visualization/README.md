# Data Visualizations for the Web
1. Heat Map
	+ Visualizes energy use as a heat map visualization scheme
	+ Uses leaflet.js to add geoJSON features around each dorm which are colored based on the heat map scale.
2. Consumption Graph
	+ Visualizes energy use at discrete times in the data window with a series of connected bars with height scaled to represent the data value.
	+ Extends the typical implementation of a D3.js bar graph and incorporates another library, gridstack.js, to add extra, meaningful user interaction.
3. Lexos
	+ Visualizes the results of clustering by the K-means algorithm on chunks of text to visually study a corpus in almost any language.
	+ Uses D3.js voronoi function to build a Voronoi tessellation, a visually stunning and intellectually valuable representation of data.