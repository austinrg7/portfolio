CLIBS= 		-lm -lglut -lGL -lGLU -lX11 
CPATHS=		-I/usr/include -L/usr/lib
CFLAGS=		$(CPATHS)$(CLIBS)


rollercoaster:		rollercoaster.cpp
		g++ rollercoaster.cpp -o rollercoaster $(CFLAGS)

fractals_test:		fractals_test.cpp
		g++ fractals_test.cpp -o fractals_test $(CFLAGS)

clean:
		rm *.o