#ifndef JOB_H
#define JOB_H

#include "constants.h"

class Job{
	public:

		Job();//CTOR
		Job(int start, int PID, int prob, int totalTime);//CTOR
		~Job();//DTOR
		//Begin member functions---
		bool ioCheck();
		//===End member functions

		//Begin job properties---
		int start_time;//Time that a job can start at
		int pid;//Identifier for the job
		int io_prob;//Probability that the job needs io to be completed
		int io_length;//Amount of io time needed for completion
		int totalIO;//Total amount of time spent on IO
		int job_length;//Total time it took to complete job including io
		int orig_length;//Total time job would take without wait time or io
		int finishTime;//Time into the simulation job finished
		//---End job properties
};

int generateRandom(int min, int max);

#endif