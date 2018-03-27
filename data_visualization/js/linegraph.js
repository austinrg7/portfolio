//Globals 
var linePage = true;//True if on consumption graph false otherwise
var indexPage = false;//True if on heat map false otherwise
//list of dorm names for use in this data vis
var allDorms=["beard","chapin", "clark", "cragin","emerson-dorm","everett","gebbie","keefe","kilham","larcom","meadows-east", "meadows-north","meadows-west","metcalf","mcintire","stanton","young"];
var origVals=[];//Array to hold values as they were before scaling for use in tooltip

$(document).ready(function() {
    //Wait 4 seconds for data to be processed. This page requires a lot of processesing
    setTimeout(makeGraph, 4000);
});

/*
    Extends the String class with a function to capitalize the first letter of a string
*/
String.prototype.capFirstLetter = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
/*
    Deleted the individual consumptions graphs so changed data can be displayed
*/
function deleteSVGs() {
    $(".containers").remove();
}
/*
    Input: Data set to be scaled and interpolated, the minimum of the data set, and the maximum of the data set
    Output: None, but the data inputed is updated to be scaled and interpolated
*/
function scaleNinterp(data,min,max) {
    
    //D3 interpolation function.  Scales data set with range [0,1] to [2,40]
    var interp = d3.interpolateNumber(2, 40);

    for (i=0; i<data.length;i++){
          //Scale data so range is 0,1
          data[i]=(data[i] - min)/(max - min); 
          //Interpolate data so range is 2,40
          data[i]= interp(data[i]);
    }
    
}
/*
    Input: Data set to be scaled and interpolated, the minimum of the data set, and the maximum of the data set
    Output: None, but draws the consumption graphs in the gridstack divs and removes the loading gif
*/
function makeGraph() {
    $("#loadingGif").remove();
    $("#cContainer").css('display','block');

    var options = {
      cellHeight: 40,
      verticalMargin: 11,
    };

   
    $('.grid-stack').gridstack(options);
    //init gridstack
    var grid = $('.grid-stack').data('gridstack');

    //arrays to hold the max and min of each dorm 
    var maxs=[];
    var mins=[];

    //find the max and min of each dorm val
    for (i=0; i<allDorms.length;i++){
       //make a static copy of dorm data before scaling for use in tooltip
        origVals.push(userVals[allDorms[i]].slice(0));
        var vals = userVals[allDorms[i]];
        var max = d3.max(d3.values(vals));
        var min = d3.min(d3.values(vals));

        maxs[i]=max;
        mins[i]=min;
    }

    //find the max and min of all the dorms
    var supermax= Math.max.apply(null, maxs);
    var supermin= Math.min.apply(null, mins);

    //Colors to use for each dorms consumptions bars
    var colorA=["#ff5500", "#B27FB2", "#C8A780", "#FFC0CB", "#106271", "#ff66cc", "#99cc00", "#fff68f", "#7ecdd2", "#ffa500",
    "#800000", "#008000", "#ff7f50", "#ff4444", "#a0db8e", "#cc6633", "#999966", "#9999ff"];
    
    //Dimensions of the name rectangle in each gridstack div
    var height=40;
    var length=190;
    //Set basic tooltip attributes. invisible until user scrolls over a bar 
    var tooltip = d3.select("body").append("div")
                    .attr("class", "tooltip")
                    .style("opacity", 0);

    //Draw the graphs inside each gridstack div
    for (n=0; n<allDorms.length; n++){
        //grab a dorms data
        var data = userVals[allDorms[n]]; 
        //scale and interpolate the data
        scaleNinterp(data,supermin,supermax);
        //find the gridstack elements
        var x=document.getElementsByClassName("grid-stack-item-content ui-draggable-handle");
        //svg container for consumption graphs
        var svgContainer = d3.select(x[n]).append("svg")
                             .attr("width", 700)
                             .attr("height", 75)
                             .attr("class", "containers");
        //Set width of each consumption graph dynamically so they take up the entire width
        var width=500/data.length;
        //find all the svg containers
        var y = document.getElementsByClassName("containers");

        //add a g element to the svgs
        var bar = d3.select(y[n])
                    .append("g");

        //Dorm name rectangle
        bar.append("rect")
           .attr("width", length)
           .attr("height", height)
           .attr("fill", "#6495ED")
           .attr("stroke","black");

        //Dorm name must text
        bar.append("text")
           .attr("dy", height/2)
           .attr("dx", length/2)
           .attr("fill", "black")
           .attr("text-anchor", "middle")
           .attr("font-weight", "bold")
           .text(allDorms[n].capFirstLetter());

        //The rest of the the bar where the consumoptions graphs will go
        bar.append("rect")
           .attr("x",length)
           .attr("y",0)
           .attr("width",503)
           .attr("height", height)
           .attr("fill", "#E0ffff")
           .attr("stroke", "black");

        //add in the consumption graphs
        for (j = 0; j < data.length; j++) { 
            
            bar.append("rect")
               .attr("x",j*width+length+.5)
               .attr("height", data[j])
               .attr("y",(height-data[j])/2+1) //y= 1 at max centers other recs
               .attr("width",width+2)
               .attr("fill", colorA[n])
               .attr("rx",3)
               .attr("ry",3)
               .attr("id", origVals[n][j])              
               /*
               This function displays the tooltip with the appropriate data when the user mouses over data point
               */
               .on("mouseover", function() {
                  
                  tooltip.transition()
                         .duration(200)
                         .style("opacity", 1);
                  
                  tooltip.html("Average power consumed at this moment: " + (this.id*1).toFixed(2)+ " kW/h" + "<br/>" +
                  "Cost of power at this time " + (this.id*.14).toFixed(3) +" dollars" + "<br/>" +
                  "C0" + "<sub> 2 </sub>" + " generated by this power " + (this.id*.6379).toFixed(2) + "pounds")
                         .style("left", (d3.event.pageX + 5) + "px")
                         .style("top", (d3.event.pageY - 28) + "px");
               })
               /*
               This function hides the tooltip when the user mouses away from data point
               */
               .on("mouseout", function(d) {
                   tooltip.transition()
                          .duration(200)
                          .style("opacity", 0);
               });
        } 
        //grid stack property set so that the gridstack divs are not resizeable
        grid.resizable('.grid-stack-item', false);
    }
}