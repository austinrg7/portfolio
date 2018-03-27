#ifndef SIMULATION_H
#define SIMULATION_H

#include "job.h"
#include "constants.h"
#include <queue>
#include <vector>

class Simulation
{
public:
	Simulation();//CTOR
	Simulation(int totalSimTime, int userQuantum, int degree, int numJobs, std::vector<Job*> initialList);//CTOR
	~Simulation();//DTOR

	//Begin member functions---
	bool rEnqueueCheck();
	bool rDequeueCheck(); 
	bool cpu(int tickNum);

	bool ioEnqueueCheck();
	void io();
	void run();
	void displayStatistics();
	//---End member functions

	//Begin simulation properties---
	int _sim_time; //How long to run the simulation
	int _quantum;  //How much time each job gets in the CPU before being moved out for a new job
	int _degreeMP; //Number of jobs allowed in the CPU at one time
	int _total_jobs; //Total number of jobs in the input file
	int _context_switches; //Number of times the CPU was idle to swap jobs
	int _cpu_idle; //Total time the cpu wasn't in use.

	std::vector<Job*> _fulll_list; //List of all jobs
	std::queue<Job*> rQ; //Queue of jobs ready for a time slice
	std::queue<Job*> ioQ;//Queue of jobs ready for io time
	std::vector<Job*> finished;//List of finished jobs	
	//---End simulation properties
};

int linearSearch(std::vector<Job*> V, int key);

#endif