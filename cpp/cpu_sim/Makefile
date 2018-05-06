CLIBS= 		-lm
CPATHS=		-I/usr/include -L/usr/lib
CFLAGS=		$(CPATHS)$(CLIBS)
CC = g++
OBJ = main.o job.o Simulation.o 


output.out: $(OBJ) 
	 $(CC) $(FLAGS) $(OBJ) -o output.out 

main.o: main.cpp 
	 $(CC)  main.cpp  $(FLAGS) -c  -o main.o 

job.o: job.cpp 
	 $(CC) job.cpp $(FLAGS) -c -o job.o 

Simulation.o: Simulation.cpp 
	 $(CC)  Simulation.cpp $(FLAGS) -c -o Simulation.o 


clean: 
	rm *.o
	rm *.out
