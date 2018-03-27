CLIBS= 		-lm -lglut -lGL -lGLU -lX11 
CPATHS=		-I/usr/include -L/usr/lib
CFLAGS=		$(CPATHS)$(CLIBS)


fractals:		fractals.cpp
		g++ fractals.cpp -o fractals $(CFLAGS)

clean:
		rm *.o