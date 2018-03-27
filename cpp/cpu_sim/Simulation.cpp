/*
Main.cpp mostly just handles initializations and getting user input. 
All the work of the simulation is handled by this class
*/

#include "simulation.h"
#include <iostream>
#include <vector>

using namespace std;

Simulation::Simulation(){
	/*
	Default CTOR.  Accepts no arguments, initializes nothing, and doesn't return anything
	*/

}

Simulation::Simulation(int totalSimTime, int userQuantum, int degree, int numJobs, vector<Job*> initialList){
	/*
	Second CTOR.  Accepts an 4 integers (pass by value) total simulation time, quantum size, degree of multiprogramming. and number of jobs, as well as a vector containing all the relevant input job information, initializes all these values as well as initializing _context_switches and _cpu_idle; to 0, and doesn't return anything
	*/

	_sim_time= totalSimTime; 
	_quantum= userQuantum; 
	_degreeMP= degree; 
	_total_jobs= numJobs; 
	_fulll_list= initialList;
	_context_switches= 0;
	_cpu_idle=0;

}

Simulation::~Simulation(){
	/*
	DTOR necessary as each item in Simulation's queues is a pointer to a job.  Each time a job is popped it leaves the scope and the pointers
	to the job are deleted.
	*/

	while(!rQ.empty()){
		//When DTOR is called on the Simulation each job is popped and leaves the scope calling the Job DTOR 
		rQ.pop();
	}

	while(!ioQ.empty()){
		//When DTOR is called on the Simulation each job is popped and leaves the scope calling the Job DTOR 
		ioQ.pop();
	}

}

bool Simulation::rEnqueueCheck(){
	/*  
    Check whether or not a job can be pushed onto the ready queue 

    Input:  None
    Return: Bool indicating whether or not a job can be pushed onto the ready queue 
    */

	//Check If the size of the ready queue is greater than the degree of multiprogramming.
	if(rQ.size()<= _degreeMP){
		return true;
	}
	else 
		return false;
}
bool Simulation::rDequeueCheck(){
	/*  
    Check whether or not a job should be dequeued

    Input:  None
    Return: Bool indicating whether or not a dequeue is necessary
            If there is only 1 item in the ready queue it should not be dequeued
    */

	//If there is only one thing in the ready queue don't dequeue it because it can stay in the CPU
	if(rQ.size()==1 || rQ.empty()){
		return false;
	}
	return true;
} 
bool Simulation::cpu(int tickNum){
	/*  
    Simulates a cpu processing jobs

    Input:  None
    Return: Bool indicating whether or not a switch took place.
    Also preforms the action of the CPU for 1 clock tick
    */

	//If there is a job in the ready queue
	if(!(rQ.empty())){
		Job* process;
		//grab first process in queue
		process=rQ.front();
		//the process will require IO
		if(process->ioCheck()){
			//There is room in the IO queue
			if(this->ioEnqueueCheck()){
				//Send process to io queue and remove from ready queue
				ioQ.push(process);
				rQ.pop();
			}
			else{
				//No room in IO queue so process skipped
				rQ.pop();
			}
			//Job at front of queue went off to IO but there is another job so there is a context switch
			if(!(rQ.empty())){
				return true;
			}
			//Job at front of queue went off to IO but there isn't another job so there isn't a context switch
			else{
				return false;
			}

		}
		else{
		
			process->job_length--;
			//This job is finished  
			if(process->job_length==0){
				//Put it in the finished vector.  
				finished.push_back(process);
				rQ.pop();
				//Process finished but there is another in the ready queue so there is a context switch
				if(!(rQ.empty())){
					return true;
				}
				//Process finished but there wasn't another in the ready queue so there was no context switch
				else{
					return false;
				}
			}
			else if (tickNum==_quantum && this->rDequeueCheck()){
				return true;
			}
			else{
				return false;
			}

		}
	}
	else{
		return false;
	}
}

bool Simulation::ioEnqueueCheck(){
	/*  
    Check if a job can be pushed onto the io queue

    Input:  None
    Return: Bool indicating whether or not a job can be pushed onto the io queue
    */

	if(ioQ.size()<= _degreeMP){
		return true;
	}
	else 
		return false;
}
void Simulation::io(){
	/*  
    Simulates handling io
	
    Input:  None
    Return: None, but
    handles the io part of the simulation. One millisecond of io time is removed from the total io time of the 
    job at the front of the io queue each time the function is called
    */

	//If there are jobs in the IO queue waiting for IO
	if(!ioQ.empty()){ 
		
		Job* process;
		//Grab the first one
		process=ioQ.front();
		//Do io for one tick
		process->totalIO++;
		process->io_length--;
		//If io is complete
		if(process->io_length==0){
			Job* doneIO;
			doneIO=ioQ.front();
			ioQ.pop();
			//Move it to ready queue if there's room
			if(this->rEnqueueCheck()){
				//Give it a new IO time 
				doneIO->io_length= generateRandom(IOMIN,IOMAX);
				doneIO->io_prob= generateRandom(PROBMIN-1,PROBRANGEMAX);
				//Add job finished with IO to ready queue
				rQ.push(doneIO);
			}
		}
		
	}	
}
void Simulation::run(){
	/*  
    Runs the simulation
	
    Input:  None
    Return: None, but
    allows jobs from an input file to enter the cpu and be processed (any io that may be necessary will also 
    be collected) based on start time for as long as the user has designated the simulation to run. The time a job 
    spends in the cpu is designated by the user as well as the amount of jobs that can be in the ready or io queue 
    at any one time.
    */

	//Counter for how many millisecond ticks have passed
	int msPassed= 0;
	//Keep running until out of sim time
	while(msPassed<_sim_time){
		//Check to see if a job is supposed to start at this time
		int index= linearSearch(_fulll_list, msPassed);
		//Either a job is supposed to start at this time or there is a job in the ready queue
		if(index >= 0 || !(rQ.empty())){
			//If it is a job starting at this time add it to the ready queue
			if(index >= 0 && rEnqueueCheck()){
				rQ.push(_fulll_list[index]);
			} 
			//Flag for if a context switch happened
			bool csOccurs;	
			//Number of jobs completed before context switch
			int numDone=finished.size();
			//Counter to ensure that each job is in the CPU for a maximum time=quantum
			int j=0;
			while(j<_quantum){
				//J starts at 0 but need tick number so add 1
				csOccurs=this->cpu(j+1);
				this->io();
				//Tick
				msPassed++;
				//Check if a job is scheduled to start after the tick
				index= linearSearch(_fulll_list, msPassed);
				if(index >= 0 && this->rEnqueueCheck()){
					//There is room in the ready queue so add the job onto it
					rQ.push(_fulll_list[index]);
				} 
				//A context switch occurred before the quantum expired so job done or off to IO 
				if(csOccurs){
					//If I finished a job with this context switch (and didn't go off to IO) then update the value for how long process took
					if(finished.size()!=numDone){
						finished.back()->finishTime=msPassed;
					}
					//Check for jobs with start time during context switch
					for(int i=msPassed;i<msPassed+CONTEXTSWITCH;i++){
						index= linearSearch(_fulll_list, msPassed);
						//If a job was scheduled to start during the context switch and there was room on the ready queue add it to it.
						if(index >= 0 && this->rEnqueueCheck()){
							rQ.push(_fulll_list[index]);
						} 
					}
					//Nothing happens in CPU during context switch
					msPassed+=CONTEXTSWITCH;
					//Increase the counter for context switches.  Important for calculating wait time and CPU utilization.
					_context_switches++;
					//If there was a job in the IO queue (meaning the job queue is greater than 1) before the context switch keep chuggin away
					if(ioQ.size() > 1 && (!(ioQ.empty()))){ 
					//Do IO while jobs being switch into and out of CPU
						for(int i=0;i<=CONTEXTSWITCH;i++){
							this->io();
						}
					}
					//Relinquish rest of quantum 
					j=_quantum;
				}
				else{
					//Job finished before quantum expired (or on last tick of quantum) but no context switch as there was not another process ready
					if(finished.size()!=numDone){
						finished.back()->finishTime=msPassed;
						j=_quantum;
					}
					//No job finished and no context switch so move to next tick
					else{
						j++;
					}
				}
			}
			//No context switch and no job finishing without a context switch
			if(!csOccurs && finished.size()!=numDone){
				//No context switch after quantum expired. Check if job is the only one on the ready queue
				if(this->rDequeueCheck()){
					//More than 1 job in the ready queue so move the one at the front to the back
					//Placeholder
					Job* temp;
					temp= rQ.front();
					//Remove the job that had its quantum from the front of the queue
					rQ.pop();
					//If job is not the only job in the ready queue check to see if there is room to put it back else skip it 
					if(this->rEnqueueCheck()){
						//if there is room on the ready queue place the job that was just removed from the front of the ready queue on the back
						rQ.push(temp);
					}
					//Check for jobs with start time during context switch
					for(int i=msPassed;i<msPassed+CONTEXTSWITCH;i++){
						index= linearSearch(_fulll_list, msPassed);
						if(index >= 0 && this->rEnqueueCheck()){
							rQ.push(_fulll_list[index]);
						} 
					}
					//Context switch occurred so increase the milliseconds passed so far by that amount
					msPassed+=CONTEXTSWITCH;
					//Increase the counter for context switches.  Important for calculating wait time and CPU utilization.
					_context_switches++;
					//Keep doing io during context switch
					for(int i=0;i<=CONTEXTSWITCH;i++){
							this->io();
					}
				}
				//If not then job stays in front of ready queue and time is only incremented by 1 
				else{
					msPassed++;		
				}
			}				
		}
		//No job scheduled to start at this time or in the ready queue
		else{
			this->io();
			_cpu_idle++;
			msPassed++;
		}
	}
}

void Simulation::displayStatistics(){
	/*  
    Calculates and displays various stats about the simulation
	
    Input:  None
    Return: None, but
    prints the statistics to the console
    */

	//Variables for various statistics of interest for this simulation
	int throughputVal,leftOverVal,skippedVal, totalJobsSystem;
	float jlNoIOval,turnaroundVal,waitVal,utilizationVal;

	//The vector finished stores all the jobs that finish their cpu time as well as any io time that may arise.  The throughput is equal to the number of hobs that finish before the end of the simulation.
	throughputVal= finished.size();
	//The jobs left in the system are those still in the ready and io queues when the simulation and as such is equal to the size of the ready queue added to the size of the io queue
	leftOverVal= rQ.size()+ioQ.size();
	//The number of jobs skipped is equal to the number of jobs in the input file minus the jobs that finished added to the jobs left in the ready and io queues when the simulation finished.
	skippedVal= _total_jobs-(throughputVal+leftOverVal);
	//Job length without io is equal to the time it took the job to finish minus the time the job spent in io.  Both these values are data members of the job class.
	float totTimeWOIO=0;
	for(int i=0;i<finished.size();i++){
		totTimeWOIO+=((finished[i]->finishTime - finished[i]->start_time) - finished[i]->totalIO);
	}
	//Average job time = the time all the jobs that finished took to finish not including io time dived by the number of jobs that finished 
	jlNoIOval=totTimeWOIO/throughputVal;
	float totTime=0;
	for(int i=0;i<finished.size();i++){
		totTime+=finished[i]->finishTime - finished[i]->start_time;
	}
	//Turn around value= the time it took every job that finished to finish (including io) divided by the total number of jobs that finished
	turnaroundVal= totTime/throughputVal;
	float totWait=0;throughputVal;
	for(int i=0;i<finished.size();i++){
		totWait+=(((finished[i]->finishTime - finished[i]->start_time)- finished[i]->totalIO)- finished[i]->orig_length);
	}
	//Wait time= time it took every job to finish (including io) minus the total time it should have taken each job to finish divided by the number of jobs that finished. 
	waitVal= totWait/throughputVal;
	//Percent utilization= 100-percent of time spent idle.
	//Percent time spent idle= cpuIdle counter (counts time when nothing is in ready queue when a tick occurs) plus the time the cpu was idle due to context switches
	float percentIdle= ((float)(_cpu_idle+(_context_switches*CONTEXTSWITCH))/(float)_sim_time);
	float decimal= 1- percentIdle;
	//Convert the decimal to a percent by multiplying by the constant 100
	utilizationVal=decimal*DTOP;

	//Display the statistics.
	cout<<"\nThroughput is: "<< throughputVal <<" jobs." <<endl;
	cout<<"Number of jobs still in the ready and IO queues is: "<< leftOverVal <<" jobs." <<endl;
	cout<<"Number of jobs skipped is: "<< skippedVal <<" jobs." <<endl;
	cout<<"Average job length excluding IO: "<< jlNoIOval <<" milliseconds." <<endl;
	cout<<"Turnaround is: "<< turnaroundVal <<" milliseconds." <<endl;
	cout<<"Average wait is: "<< waitVal <<" milliseconds." <<endl;
	cout<<"CPU utilization is: "<< utilizationVal <<" percent." <<endl;
}

int linearSearch(vector<Job*> V, int key) {
	/*
	Accept a vector of Jobs objects (pass by reference) an integer key (pass by value).
	Returns the index of Job in the array with a start_time=key or -1 if no start_time=key. 
	*/

	/*  
    Find a job with start time = key
	
    Input:  Vector of jobs to search and int key to search for
    Return: The index of Job in the array with a start_time=key or -1 if no start_time=key.
    */

   for (int i=0; i< V.size(); i++) {
       if (key == V[i]->start_time) {
          return i;
       }
   }
   return -1;    // failed to find key
}