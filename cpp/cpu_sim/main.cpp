/*
Name: Austin Gillis

Program Name: Single CPU MP Sim

Purpose: The purpose of this program is to simulate multiprogramming with one CPU as well as generate statistics
about how "well" the simulation went. 

Input (from terminal): 1) Name of input file. File specs- First line is first line is the number of jobs.
                       subsequent lines are four int values representing the start time, process ID, I/O probability, 
                       and the total job length
                       2) Three integers (entered separately) representing the total simulation time (seconds), quantum
                       size (milliseconds), and the number of processes allowed in the system. 

Output: The throughput, the number of jobs in the system when the simulation terminated, the number of jobs skipped, 
        the average job length excluding I/O time, average turnaround time, average waiting time per process, 
        and the percentage of time the CPU is busy.  

*/

using namespace std;
        
#include "job.h"
#include "simulation.h"
#include "constants.h"
#include <time.h> 
#include <stdlib.h>
#include <fstream>
#include <iostream>
#include <queue>
#include <vector>

int main(){
    //Seed random number generator
    srand (time(NULL));
    cout << "Enter the name of the file (including the extension) containing the jobs for this simulation."<< endl;
    //Variable for input filename
    string inFileName;   
    cin >> inFileName;

    //Variable for input file stream
    ifstream inFile (inFileName.c_str());
    //Grabbed desired file... attempting to open
    if (inFile.is_open()) {

		cout << "Enter the amount of time in (integer) seconds you wish to run the simulation."<< endl;
		//Variable for the total time the simulation will run
		int totalSimTime;
		cin >> totalSimTime;
		totalSimTime=totalSimTime*STOMS;

		cout << "Enter the size of the CPU quatum in (integer) milliseconds."<< endl;
		//Variable for the maximum time a job spends in the CPU before being switched out
		int userQuantum;
		cin >> userQuantum;

		cout << "Finally enter the maximum (integer) number of processes allowed to enter the CPU"<< endl;
		//Variable for the number of jobs allowed in the system
		int degree;
		cin >> degree;

		//Total number of jobs in input file
		int numJobs;
		inFile>>numJobs;

        //Placeholders for values to initialize a job to
		int tempStart, tempPID, tempProb, tempLength;
		//Vector to hold all the jobs in the input file which may or may not be processed 
		vector<Job*>initialList;

		int linecounter=0;
		//Read in all the jobs and add to vector
		while(linecounter<numJobs){
			inFile>>tempStart>>tempPID>>tempProb>>tempLength;
			initialList.push_back(new Job(tempStart, tempPID, tempProb, tempLength));
			linecounter++;
		}
		//Input file has been read in an can now be closed.
		inFile.close();

		//Create a Simulation object with the data the user has ended
		Simulation * sim= new Simulation(totalSimTime, userQuantum, degree, numJobs, initialList);
		
		//Run the simulation based on user input
		sim->run();
		//Display results of simulation as various statistics
		sim->displayStatistics();

		

	}
	//Could not open file as entered by user.
    else{
    	cout<<"Please enter a valid filename+extension.  Terminating..."<<endl;
    }

    return 0;
}