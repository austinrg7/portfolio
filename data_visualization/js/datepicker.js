// global so other files can access
var endYear;//year of end date
var endMonth;//month of end date
var endDay;//day of end date
var startYear;//year of start date
var startMonth;//month of start date
var startDay;//day of start date
var startDateObj;//javascript Date object for start date
var endDateObj;//javascript Date object for end date

$(document).ready(function(){

  	// get the end date (date of last data point) and start date (default to 1 month before)
	endYear = 2016;
	endMonth = 5;
	endDay = 3;
	startYear = endYear;
	startMonth = endMonth - 1;
	startDay = endDay;

	// format month and day to mm/dd
	endMonth = checkFormat(endMonth);
	endDay = checkFormat(endDay);
	startMonth = checkFormat(startMonth);
	startDay = checkFormat(startDay);

	startDateObj = new Date(startYear, (startMonth-1), startDay); //date object numbers months 0-11
	endDateObj = new Date(endYear, (endMonth-1), endDay);

	// turn dates into strings for use with date picker
	var stringStartDate = startYear + '-' + startMonth + '-' + startDay;
	var stringEndDate = endYear + '-' + endMonth + '-' + endDay;

	// display date to user in date picker
	$('#startDate').append(stringStartDate);
	$('#endDate').append(stringEndDate);

	// set start and end dates on change button press to ones calculated
	$('#dp4').fdatepicker('update', stringStartDate);
	$('#dp5').fdatepicker('update', stringEndDate);


	/*
		jQuery function that handles the user changing the end date for the data value range.
		Target is element with id=dp4 (the start date selector div)
		Event listener triggered by change of date
		Updates userVals object to contain the new values the user wants to see
		Redraws the visualization the user is viewing using the new data
	*/
	$('#dp4').fdatepicker()
		.on('changeDate', function (ev) {
		var newDate = new Date(ev.date);
		var validDate = checkDate(newDate);

		if (validDate) {
			if (ev.date.valueOf() > endDate.valueOf()) {
				//Catch basic user error
				$('#alert').show().find('strong').text('The start date can not be greater then the end date');
			} else {
				$('#alert').hide();
				startDate = new Date(ev.date);
				$('#startDate').text($('#dp4').data('date'));
				//User changed start date
				changeStartDate(startDate);
				startDateObj = new Date(startYear, (startMonth-1), startDay);
				//Get the values that the user wants to see
				getValRange(labelDelim,startDateObj,endDateObj);
				//Convert vals to kw (h/d/w)
				avgKWH();
				//Redraw the visualization using the new data
				if (indexPage)
					redrawMap();
				else if (linePage) {
					deleteSVGs();
					makeGraph();
				}
			}
		}
		$('#dp4').fdatepicker('hide');
	});

	/*
		jQuery function that handles the user changing the end date for the data value range.
		Target is element with id=dp5 (the end date selector div)
		Event listener triggered by change of date
		Updates userVals object to contain the new values the user wants to see
		Redraws the visualization the user is viewing using the new data
	*/

	$('#dp5').fdatepicker()
		.on('changeDate', function (ev) {
		var newDate = new Date(ev.date);
		var validDate = checkDate(newDate);

		if (validDate) {
			//Catch basic user error
			if (ev.date.valueOf() < startDate.valueOf()) {
				$('#alert').show().find('strong').text('The end date can not be less then the start date');
			} else {
				$('#alert').hide();
				endDate = new Date(ev.date);
				$('#endDate').text($('#dp5').data('date'));
				//User changed the end date
				changeEndDate(endDate);
				endYear = 2016;

				endDateObj = new Date(endYear, (endMonth-1), endDay);
				//Get the values that the user wants to see
				getValRange(labelDelim,startDateObj,endDateObj);
				//Convert to kw (/h/d/w) 
				avgKWH();
				//Redraw the visualization using the new data
				if (indexPage)
					redrawMap();
				else if (linePage) {
					deleteSVGs();
					makeGraph();
				}
			}
		}
		$('#dp5').fdatepicker('hide');
	});
});
/*
	Input: an interger representing a month or day of the year 
	Output: properly formatted integer for date picker
*/
function checkFormat(dateNum) {
	//Numbers less than 10 are formatted in date picker as 01 02 03 etc so these numbers need 
	if (dateNum < 10) 
		return ('0' + dateNum);
	else
		return dateNum;
}
/*
	Input: a date object containing the start date to which the user changed 
	Output: None, but fixes date objects that don't follow normal numbering convetions
*/
function changeStartDate(startDate) {
	startYear = startDate.getFullYear();//get user input day from the date object
	startMonth = checkFormat(startDate.getMonth()+1);//get user input month from the date object (add 1 as it starts at 0)
	startDay = checkFormat(startDate.getDate());//get user input year from the date object

	//March 31
	if (startDay == 31 && startMonth == 3) {
		startMonth = startDate.getMonth() + 2;
		startMonth = '0' + startMonth;
		startDay = '0' + 1;
	}
	//April 30
	else if (startDay == 30 && startMonth == 4) {
		startMonth = startDate.getMonth() + 2;
		startMonth = '0' + startMonth;
		startDay = '0' + 1;
	}
	else {
		var tempStartDay = startDate.getDate();
		startDay = '0' + (tempStartDay + 1);
	}
}
/*
	Input: a date object containing the end date to which the user changed 
	Output: None, but fixes date objects that don't follow normal numbering convetions
*/
function changeEndDate(endDate) {
	endYear = endDate.getFullYear();
	endMonth = checkFormat(endDate.getMonth()+1);
	endDay = checkFormat(endDate.getDate());

	//March 31
	if (endDay == 31 && endMonth == 3) {
		endMonth = endDate.getMonth() + 2;
		endDay = 1;
	}
	//April 30
	else if (endDay == 30 && endMonth == 4) {
		endMonth = endDate.getMonth() + 2;
		endDay = 1;
	}
	else {
		var tempEndDay = endDate.getDate();
		endDay = (tempEndDay + 1);
	}
}
/*
	Input: a date object containing the date to which the user changed 
	Output: boolean. true if valid date false if not.
	Additionaly fixes date objects that don't follow normal numbering convetions
*/
function checkDate(newDate) {

	var newDay = newDate.getDate();//get user input day from the date object
	var newMonth = newDate.getMonth()+1;//get user input month from the date object (add 1 as it starts at 0)
	var newYear = newDate.getFullYear();//get user input year from the date object

	//Fixing various abnormalites between how the date was stored in date object and how one would expect it would be stored 
	if (newDay == 31 && newMonth == 3) //March 31
		newDay = 1;
	else if (newDay == 30 && newMonth == 4)// April 30
		newDay = 1;
	else
		newDay += 1;
	// for some reason first of month gets month number of previous month
	if (newDay == 1) {
		newMonth += 1;
	}
	//End of abnormality fixing

	//Finds invalid inputs and returns false if one is found
	if (newYear !== 2016) {
		return false;
	}
	if (newMonth < 3 || newMonth > 5) {
		return false;
	}
	if (newMonth == 3 && newDay < farthestBackDay) {
		return false;
	}
	if (newMonth == 5 && newDay > 3)
		return false;
	//Valid input return true
	return true;
}
/*
	Input/Output:None but,
	Handles user on the consumption graph changing the delimeter for the data to hours
	Updates the userVal data structure
	Redraws the visualization
*/
function byHoursL() {
	getValRange("hour", startDateObj, endDateObj);//Update data structure for hours
	labelDelim = "hour";//set the global tracking the delimeter to hours 
	deleteSVGs();//delete old data
	makeGraph();//redisplay
}
/*
	Input/Output:None but,
	Handles user on the consumption graph changing the delimeter for the data to days
	Updates the userVal data structure
	Redraws the visualization
*/
function byDaysL() {
	getValRange("day", startDateObj, endDateObj);//Update data strcuture for days
	labelDelim = "day";//set global tracking the delimeter to days
	deleteSVGs();
	makeGraph();
}
/*
	Input/Output:None but,
	Handles user on the consumption graph changing the delimeter for the data to weeks
	Updates the userVal data structure
	Redraws the visualization
*/
function byWeeksL() {
	getValRange("week", startDateObj, endDateObj);//Update data strcuture for weeks
	labelDelim = "week"; //set global tracking the delimeter to week
	deleteSVGs();
	makeGraph();
}
/*
	Input/outpput:none, but
	Handles user on the heat map changing the delimeter for the data to hours
	Updates the userVal data structure
	Redraws the visualization
*/
function byHours() {
	getValRange("hour", startDateObj, endDateObj);
	labelDelim = "hour";
	avgKWH();//Heat map uses average kwh vals
	redrawMap(); //redraw map with new data
	resetScales(); //redraw scaled with new data
}
/*
	Input/outpput:none, but
	Handles user on the heat map changing the delimeter for the data to days
	Updates the userVal data structure
	Redraws the visualization
*/
function byDays() {
	getValRange("day", startDateObj, endDateObj);
	labelDelim = "day";
	avgKWH();
	redrawMap();
	resetScales();
}
/*
	Input/outpput:none, but
	Handles user on the heat map changing the delimeter for the data to weeks
	Updates the userVal data structure
	Redraws the visualization
*/
function byWeeks() {
	getValRange("week", startDateObj, endDateObj);
	labelDelim = "week";
	avgKWH();
	redrawMap();
	resetScales();
}