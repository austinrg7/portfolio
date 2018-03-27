CLIBS= 		-lm -pthread
CPATHS=		-I/usr/include -L/usr/lib
CFLAGS=		$(CPATHS)$(CLIBS)


pthread_proj:		thread_wp_sim.cpp
		g++ thread_wp_sim.cpp -o pthread_proj $(CFLAGS)

clean:
		rm *.o