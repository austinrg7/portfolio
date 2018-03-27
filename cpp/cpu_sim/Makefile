CPATHS=		-I/usr/include -L/usr/lib
CFLAGS=		$(CPATHS)


cpu_sim:		main.cpp job.cpp Simulation.cpp
		g++ main.cpp job.cpp Simulation.cpp -o cpu_sim $(CFLAGS)

clean:
		rm *.o