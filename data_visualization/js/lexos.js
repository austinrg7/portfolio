var path;
var voronoi;
var objStructure= '{"vertices" : [],"otherPoints" : [],"textData" : [],"colors" : []}';
var genObj=JSON.parse(objStructure);
var provObj=JSON.parse(objStructure);
var mineObj=JSON.parse(objStructure);

$( document ).ready(function() {

    genObj['vertices'] = genabVals['vertices'];
    genObj['otherPoints']= genabVals['otherPoints'];
    genObj['textData']= genabVals['textData'];
    scaleNinterp(genObj['vertices'],genObj['otherPoints'],genabVals['extrema'],genObj['textData']);
    genObj['vertices'].unshift([-500,-500]);
    genObj['colors']= genabVals['colors'];

    provObj['vertices'] = provVals['vertices'];
    provObj['otherPoints']= provVals['otherPoints'];
    provObj['textData']= provVals['textData'];
    scaleNinterp(provObj['vertices'],provObj['otherPoints'],provVals['extrema'],provObj['textData']);
    provObj['vertices'].unshift([-500,-500]);
    provObj['colors']= provVals['colors'];

    mineObj['vertices'] = mineVals['vertices'];
    mineObj['otherPoints']= mineVals['otherPoints'];
    mineObj['textData']= mineVals['textData'];
    scaleNinterp(mineObj['vertices'],mineObj['otherPoints'],mineVals['extrema'],mineObj['textData']);
    mineObj['vertices'].unshift([-500,-500]);
    mineObj['colors']= mineVals['colors'];

    genab=true;
    prov=false;
    mine=false;
    $("#explaination").replaceWith(genabDesc);
    makeTessalation();
});

function scaleNinterp(setA,setB,extrema,obj) {

    var interp = d3.interpolateNumber(20, 555);

    var extremaX=extrema[0];
    var extremaY=extrema[1];

    var max,min;

    for (i=0; i<setA.length;i++){
        for (j=0; j<2;j++){
            max=(j%2 ? extremaY[0]: extremaX[0]);
            min=(j%2 ? extremaY[1]: extremaX[1]); 
            setA[i][j]=(setA[i][j] - min)/(max - min); 
            setA[i][j]= interp(setA[i][j]);
        }
    }

    for (i=0; i<setB.length;i++){
        for (j=0; j<2;j++){
            max=(j%2 ? extremaY[0]: extremaX[0]);
            min=(j%2 ? extremaY[1]: extremaX[1]); 
            setB[i][j]=(setB[i][j] - min)/(max - min); 
            setB[i][j]= interp(setB[i][j]);
            obj[i]['coords'].push(setB[i][j]);
        }
    }
}

function makeTessalation(){

    if(genab){
        vertices = genObj['vertices'];
        otherPoints= genObj['otherPoints'];
        textData= genObj['textData'];
        colors= genObj['colors'];
        
    }
    else if(prov){
        vertices = provObj['vertices'];
        otherPoints= provObj['otherPoints'];
        textData= provObj['textData'];
        colors= provObj['colors'];
       
    }   

    else if(mine){
        vertices = mineObj['vertices'];
        otherPoints= mineObj['otherPoints'];
        textData= mineObj['textData'];
        colors= mineObj['colors'];
        
    }

    else{
        console.log("WTF?!?!?!")
    }

    //Find the points that are also centroids
    var copyIndexes=[];
    var copy;

    //Checks for edge case where a data point is also a centroid. (ex 3 data points close together at x~~100 and one data point far away at x~~1000) 
    for (var j=1;j<vertices.length;j++){
        for (var k=0;k<otherPoints.length;k++){
            if (vertices[j][0]== otherPoints[k][0] && vertices[j][1]== otherPoints[k][1]){
              copyIndexes.push(j);
            }       
        }
     }
    
    voronoi = d3.geom.voronoi()
        .clipExtent([[0, 0], [575, 575]]);

    var svg = d3.select("svg");

    path = svg.append("g").selectAll("path");

    //Add centroids 
    svg.selectAll("circle")
        .data(vertices.slice(1))
      .enter().append("circle")
        .attr("transform", function(d) { return "translate(" + d + ")"; })
        .attr("r", function(d,i){return ((copyIndexes.indexOf(i+1)!=-1) ? 5.0: 3.0);}) //If the centroid is the only point in the cell make it the same size as a point
        .attr("id", function(d,i){return ((copyIndexes.indexOf(i+1)!=-1) ? 'points':'centroids');}) //If the centroid is the only point in the cell pretend it's a point
        .style('fill', function(d,i){return ((copyIndexes.indexOf(i+1)!=-1) ? '#F00':'#000');}); //If the centroid is the only point in the cell style it as a point

    //Add other points
    svg.selectAll("circle")
        .data(otherPoints,function(d){return d;})
      .enter().append("circle")
        .attr("transform", function(d) { return "translate(" + d + ")"; })
        .attr("r", 5.0)
        .attr("id", "points")
        .style('fill','#F00');

    svg.selectAll("text")
        .data(textData)
      .enter().append("text")
        .attr("x", function(d) { return ((d.coords[0]<550) ? d.coords[0]:(d.coords[0]-60)); })
        .attr("y", function(d) { return d.coords[1]; })
        .attr("fill", function(d) { return ((d.coords[0]<550) ? 'black':'rgba(0,0,0,0.9)'); })
        .text(function (d) { return d.title; })
        .attr("font-family", "sans-serif")
        .attr("font-size", "14px");
       
    redraw();
}

function redraw() {
    path = path
           .data(voronoi(vertices), polygon);

    path.exit().remove();

    path.enter().append("path")
                .style("fill",function(d,i){return colors[i-1]})//i-1 because i starts at 1 here 
                .style("opacity",0.8)
                .attr("d", polygon);

    path.order();
}

function polygon(d) {
    return "M" + d.join("L") + "Z";
}

function forward(){

    if(genab){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(provDesc);
        genab=false;
        prov=true;
        mine=false;
        
        d3.select("svg").selectAll("*").remove();

        makeTessalation();
    }

    else if(prov){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(mineDesc);
        genab=false;
        prov=false;
        mine=true;
        
        d3.select("svg").selectAll("*").remove();

        makeTessalation();
    }

    else if(mine){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(genabDesc);
        genab=true;
        prov=false;
        mine=false;
       
        d3.select("svg").selectAll("*").remove();

        makeTessalation();
    }

    else{
        console.log("Duh fuck?!?!!")
    }


}

function back(){

    if(genab){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(mineDesc);

        genab=false;
        prov=false;
        mine=true;
           
        d3.select("svg").selectAll("*").remove();

        makeTessalation();
    }

    else if(prov){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(genabDesc);
        genab=true;
        prov=false;
        mine=false;

        d3.select("svg").selectAll("*").remove();
        
        makeTessalation();
    }

    else if(mine){
        $("#exTitle").remove();
        $("#explaination").remove();
        $("#explain").html(provDesc);
        genab=false;
        prov=true;
        mine=false;

        d3.select("svg").selectAll("*").remove();

        makeTessalation();
    }

    else{
        console.log("Duh fuck?!?!!")
    }
}