/*
This overall program simulates a CPU processing jobs with the same properties, but different values.
Each of these jobs is a class as defined below.
*/

#include "job.h"
#include "constants.h"
#include <stdlib.h>

Job::Job(){

	/*
	Default CTOR.  Accepts no arguments, makes no initializations, and doesn't return anything
	*/

}

Job::Job(int start, int PID, int prob, int totalTime){
	
	/*
	Second CTOR.  Accepts four ints (pass by value) denoting the time a process starts, the process ID, the IO probability, and the total jobLength 
	initializes start_time, pid, io_prob, and job_length to these values as well as initializing initial to true, io_length to a random number [5,25],
	and initializes totalIO to 0, and doesn't return anything
	*/

	//Initialize some values
	start_time= start;
	pid= PID;
	io_prob= prob;
	job_length = totalTime;
	orig_length = totalTime;
	io_length= generateRandom(IOMIN,IOMAX);
	totalIO=0;

}

Job::~Job(){
	/*
	Job class contains no pointers so no need to do anything in the DTOR
	*/
}

bool Job::ioCheck(){
	/*  
    Check whether or not a process needs to go to the IOqueue 

    Input: None
    Return: Bool indicating whether or not the process goes to the IOqueue 
    */

	//Start at 1 so something with 0 probability never makes it into first if statement	
	int check= generateRandom(PROBMIN,PROBMAX);

	if(check<= io_prob){
		//io happens
		return true;
	}
	else{
		//io doesn't happen
		return false;
	}
}

int generateRandom(int min, int max){
	/*  
    Generate a random number for use in IOcheck 

    Input: Two ints denoting the range the random number must fall in
    Return: One random number in the specified range 
    */

	//Place holder for random number generated
	int num;
	//Seed random number generator so numbers produced are unique
	
	num = rand() % ((max+1)-min) + min;
	return num;
}