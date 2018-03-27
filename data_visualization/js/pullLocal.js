//Globals

//Data structure for holding dorm values (JSON stored as a string)
var valStructure= '{"beard" : [],"emerson-dorm" : [],"chapin" : [],"clark" : [],"mcintire" : [],"young" : [],"meadows-east" : [], "meadows-west" : [], "meadows-north" : [],"metcalf" : [],"kilham" : [],"larcom" : [], "stanton": [], "cragin" : [],"everett" : [], "gebbie": [], "keefe": []}';
//xml file names (without .xml extension)
var xmlNames= ["meadows-ew-1st-floor", "meadows-north-1st-floor", "stanton-cragin-everett", "clark-mcintire-young", "larcom", "metcalf", "kilham", "gebbie-keefe", "meadows-ew-2nd-floor", "meadows-ew-3rd-floor", "meadows-ew-4th-floor", "meadows-north-2nd-floor", "meadows-north-3rd-floor", "meadows-north-4th-floor", "beard", "emerson-dorm", "chapin", "everett-heights"];
var ewMeadowsDorms=["meadows-ew-2nd-floor", "meadows-ew-3rd-floor"];//These dorms have to be handled differently
var nMeadowsDorms=["meadows-north-2nd-floor", "meadows-north-3rd-floor", "meadows-north-4th-floor"];//These dorms have to be handled differently

var allVals=JSON.parse(valStructure);//Holds all the available data
var userVals=JSON.parse(valStructure);//Holds the data the user wants to view

var numHours=994;//Total number of hours in the full data set 

var avgKWh=JSON.parse(valStructure);//Holds values for heat map which displays average kwh over the period chosen by the user

var labelDelim = "hour";//By default the delimeter for data is hours

$( document ).ready(function() {
    
    for (var i = 0; i <xmlNames.length; i++) {
        //path to local xml files containing dorm data ex beard would be ./xmlFiles/beard.xml
        var name= xmlNames[i];
        var extension= ".xml"; 
        var egaugeURL= "./xmlFiles"
        var slash="/";
        var tempPath= egaugeURL.concat(slash,name,extension);

        storeVals(tempPath,name);//get and process data   
    }
    var startDate = new Date(2016, 03, 03);//Data defaults to one month before last date data is available (month off by 1 as date obj starts month at 0)
    var endDate = new Date(2016, 04, 03);//Last date data is available
    //Have to wait for data to be fetched, read in, and placed into data structure
    setTimeout(function() {
        getValRange("hour",startDate,endDate)
    },2000);
    setTimeout(avgKWH,2000);

});

/*
Input: String of file path to the xml file with the appropriate dorm's data, string dorm name  
Output: If sucess-None, but allVals is updated to contain the dorm's data 
        If fail- console.log("Didn't work");
Running locally requires chrome in development mode running with flags 
        --allow-file-access-from-files --disable-web-security
Reason: Cross origin requests are only supported for protocol schemes: http, data, chrome, chrome-extension, https.send
*/
function storeVals(path,dorm){

    var temp=[];//temporary array used to hold data as it is read in and proper values are calculated

    //ajax request to open the xml files contiang the data asynchronously (explaining the various set timeouts)
    $.ajax({
    url: path, 
    dataType: 'xml',
    async: true,
    success: function(data){

        var xml = $('group',data);
        xml.find("c").each(function() { //data values all have a <c> xml tag
           temp.push(1*($(this).text())); //multiply the string by 1 to convert to a number
        });
    
        /*
            This data required pre-processing. The readings came directly from newly installed smart electricity gauges
            and as such the data values are not stored the same in every dorm xml file. Even with the preprocessing
            it's clear from the data that some meters (Clark for example which shares a structure with 2 other dorms)
            are not able to be represented 100% accurately. The available data can still be visualized in the same manner
            as all other dorms, but again is likely not 100% accurate.  

            Things that get summed: dorm and computer panel, panel 1 and panel 2
            Dorms with things to sum: emerson, larcom, meadows ew 1st floor, meadows north 1st floor, stanton
            Dorms to separate: ymc, cragin-everett-stanton, gebbie-keefe  
            Kilham: Sum column 0,1,2,4,6,8 in each row skip rest
            Meadows-ew-4th: sum column 0 and 1 in each row skip rest
            Meadows-ew dorms 2-4 and everett heights need to wait for something before adding to the data
        */
       
        //Handle each of the dorms as described above
        if (dorm == "clark-mcintire-young"){
            for (var i = 0; i <= (numHours *3) +2; i++) {
                if (i%3==0){
                    allVals["clark"].push(temp[i]);
                }
                else if (i%3==1){
                    allVals["mcintire"].push(temp[i]);
                }
                else {
                    allVals["young"].push(temp[i]);
                }
            }
        }

        else if (dorm == "stanton-cragin-everett"){
            var counter=0;
            for (var i = 0; i <= (numHours*4)+2; i++) {
                if (i%4==0){
                    allVals["stanton"].push(temp[i]);
                }
                else if (i%4==1){
                    allVals["stanton"][counter]+=temp[i];
                    counter++;
                }
                else if (i%4==2){
                    allVals["cragin"].push(temp[i]);
                }
                else {
                    allVals["everett"].push(temp[i]);
                }
            }
        }

        else if (dorm == "meadows-ew-1st-floor"){
            for (var i = 0; i <= (numHours*4); i+=4) {
               allVals["meadows-east"].push(temp[i]+temp[i+3]);
               allVals["meadows-west"].push(temp[i+1]+temp[i+2]);
            }
        }

        else if(ewMeadowsDorms.indexOf(dorm) > -1){ 
            var counter=0;
            for (var i = 0; i <= (numHours*2); i+=2) {
                if(isNaN(allVals["meadows-west"][0]))
                    setTimeout(function() {
                    processEW(temp,counter,i)
                },200);
                else
                    processEW(temp,counter,i);
               
                counter++;
            }

        }

        else if(dorm == "meadows-ew-4th-floor"){ 
            var counter=0;
            for (var i = 0; i <= (numHours*14); i+=14) {
                if(isNaN(allVals["meadows-west"][0]))
                setTimeout(function() {
                    processEW(temp,counter,i)
                },200);
                else
                    processEW(temp,counter,i);
               
                counter++;
            }

        }
        
        else if (dorm == "meadows-north-1st-floor"){
            for (var i = 0; i <= (numHours*2); i+=2) {
               allVals["meadows-north"].push(temp[i]+temp[i+1]);
            }
        }

        else if (dorm == "emerson-dorm"){
            for (var i = 0; i <= (numHours*2); i+=2) {
               allVals["emerson-dorm"].push(temp[i]+temp[i+1]);
            }
        }

        else if (dorm == "larcom"){
            for (var i = 0; i <= (numHours*2); i+=2) {
               allVals["larcom"].push(temp[i]+temp[i+1]);
            }
        }

        else if (dorm == "kilham"){

            for (var i = 0; i <= (numHours*10); i+=10) {
               allVals["kilham"].push(temp[i]+temp[i+1]+temp[i+2]+temp[i+4]+temp[i+6]+temp[i+8]);
            }                    


        }

        else if (dorm == "gebbie-keefe"){
            
            for (var i = 0; i <= (numHours*2)+1; i++) {
                if (i%2==0){
                    allVals["gebbie"].push(-1*(temp[i]));
                }
                else {
                    allVals["keefe"].push(-1*(temp[i]));
                }
            }

        }
        
        else if(nMeadowsDorms.indexOf(dorm) > -1){

            for (var i = 0; i <= numHours; i++) {
                   allVals["meadows-north"][i]+=temp[i];
            }

        }

        else if (dorm == "everett-heights"){
            
            if(isNaN(allVals["everett"][0]))
                setTimeout(function() {
                    processHeights(temp)
                },500);
            else
                processHeights(temp);
        }
        
        else{ 
            for (var i = 0; i <= numHours; i++) {
    
                allVals[dorm].push(temp[i]);

            }
        }       
    },
    error: function(data){//The file could not be opened for some reason. alert the user via the console
        console.log("Didn't work");
    }
    });

}
/*
    Input: The data values for everett heights
    Output: None, but the everett values are updated properly
    Everett heights must weight for everett to be processed. The are part of the same building
    but have separate meters.
*/
function processHeights(heightsVals){

    for (var i = 0; i <= numHours; i++) {
        allVals["everett"][i]+=heightsVals[i];
    }
}
/*
    Input: The data values from a meadows east an meadows west meter
    Output: None, but the meadows-east and meadws-west values are updated properly
    Meadows-east-2nd cannot be processed until meadows-east-1st
*/
function processEW(ewVals,counter,i){
    
    allVals["meadows-east"][counter]+=(ewVals[i]);
    allVals["meadows-west"][counter]+=(ewVals[i+1]);
}
/*
    Input: string delimeter to change data to, date object for start date, date object for end date
    Output: none, but userVals is updated to containing the dat the user wants to see 
*/
function getValRange(delim,start,end){

    clearUserVals();//Clear out any old values
    var firstVal = 1462306500; //Time of most recent data value
    var lastVal = firstVal- (3600*numHours); //Currently have 995 rows of data which is 994 hours of data. 3600s in an hr

    var posStart, posEnd;//Positions in array from allVals for new start and new end for userVals array
    //Find how many hours after the first data value we have the user start date is.  That is the first postion in array to read from
    posStart=parseInt((start.getTime()/1000-lastVal)/3600);
    //Find how many hours before the last data value we have the user end date is.  1000-posEnd is the last position in array to read
    posEnd= parseInt((firstVal-end.getTime()/1000)/3600);

    //Hours uses all data rows within date range
    if (delim=='hour'){
        //Copy all vals in date range
        for (var i = 0; i < _.size(userVals); i++) {
            var name= _.keys(userVals)[i];
            var counter = 0;
            for (var j = posStart; j <= numHours-posEnd; j++) {
                    userVals[name][counter] = (allVals[name][j]);
                    counter++;
            }
        }
        //convert to kwh
        toKWH();
    }
    //Usage over day is (row0+n)-(row23+n) (hour 23 - hour 0= kwh for whole day) 
    else if (delim=='day'){
        for (var i = 0; i < _.size(userVals); i++) {
            
            var counter=0;
            var name= _.keys(userVals)[i];

            for (var j = posStart; j < numHours-posEnd; j++) {
                //24 hrs in a day so we want every 24th value
                if(counter%24==0)
                    userVals[name].push(allVals[name][j]);   
                counter++;
            }
        }
        toKWH();
    }
    //Usage over day is (row0+n)-(row167+n) (hour 167 - hour 0= kwh for whole week) 
    else if (delim=='week'){
        for (var i = 0; i < _.size(userVals); i++) {
            
            var counter=0;
            var name= _.keys(userVals)[i];

            for (var j = posStart; j < numHours-posEnd; j++) {
                //168 hours in a week so we want every 168 value
                if(counter%168==0)
                    userVals[name].push(allVals[name][j]);
                
                counter++;   
            }

        }
        toKWH();
    }
}
/*
Input/Output: none, but userVals is updated to contain kwh over period 
              instead of instantaneous readings measured in watt seconds
*/
function toKWH(){
    
    for (var i = 0; i <_.size(userVals); i++) {
        var last=userVals[_.keys(userVals)[i]].length -1;
        for (var j = 0; j < last; j++) {
            //3600000 watt seconds to kwh
            userVals[_.keys(userVals)[i]][j]=((userVals[_.keys(userVals)[i]][j]-userVals[_.keys(userVals)[i]][j+1])/3600000)
        }
        //Remove last value as it is not a kwh usage val
        userVals[_.keys(userVals)[i]].splice(last,1);
    }
}
/*
Input/Output: none, but avgKWh is updated to contain average kwh over period 
              instead of individual/summed kwh over the period
*/
function avgKWH() {
    
    for (var i = 0; i < _.size(userVals); i++) {
        var last = userVals[_.keys(userVals)[i]].length -1;
        var sum = 0;
        for (var j = 0; j < last; j++) {
            sum += userVals[_.keys(userVals)[i]][j];
        }
        avgKWh[_.keys(avgKWh)[i]][0] = sum/(last+1);
    }

    //if on index page data has to be further processed by resetEachDorm 
    if (indexPage)
        resetEachDorm();
}
/*
Input/Output: none, but power and cost vals get rounded to 2 decimal places
*/
function resetEachDorm() {
    for (var i = 0; i < Object.keys(dormData["features"]).length; i++) {
        var dormName = dormData["features"][i].properties.name;
        var j = _.indexOf(_.keys(avgKWh), dormData["features"][i].properties.name);
        dormData["features"][i].properties.power = avgKWh[_.keys(avgKWh)[j]][0].toFixed(2);
        dormData["features"][i].properties.cost = (dormData["features"][i].properties.power*.14).toFixed(2);
    }
}
/*
Input/Output: none, but all userVals are "cleared" (array length changed to 0)
*/
function clearUserVals() {
    for (var i = 0; i < _.size(userVals); i++) {
        var name= _.keys(userVals)[i];
        userVals[name].length = 0;
    }
}
/*
Input: none
Output: console.log(allVals). Used for debugging 
*/
function echoData(){
    console.log(allVals);
}