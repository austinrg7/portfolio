/*
Name: Austin Gillis

Program Name: Linear Algebra Roller Coaster

Purpose: Use splines of various continuity to connect a series of vertices and simulate a roller coaster moving 
along them. This technique of connecting vertices with splines, particularity of those of higher continuity, 
is useful in computer graphics for connecting a set of vertices with a curved line that does not change abruptly
at a vertex. Regardless of the level of continuity, each spline is found by solving a system of simultaneous 
equations, but each level has a different number of equations to solve. Linear algebra introduced the concept of
matrices and reduced row echelon form, which was implemented as it was more dynamic than solving the equations with
substitution as taught in class.   

Input (from keyboard): 0   = Choose linear piecewise spline (default)
					   1   = Choose parabolic piecewise spline 
					   2   = Choose cubic piecewise spline
					   -   = Move slower
					   +   = Move faster
					   r   = return to start
					   s   = start animation
					   q   = quit
	   				   esc = quit
      
      (from terminal): Name of input file. File specs- First line is the number of knots, each subsequent line
	                   is the x and y coordinate for a knot (separated by a space). First coordinate always
	                   0 0 and last always 1000 0. Sample input produces "nice" output. 

Output: An openGL window displaying a roller coaster simulation, a simple car moving along a track consisting of splines 
        connecting the input set of knots, driven by keyboard input.

	    C0 continuity = Each knot connected by a line.
	    C1 continuity = A line connects the first pair of knots. Each subsequent pair of knots is connected with a 
	                    parabolic spline where the slope of the parabolic spline at the beginning knot is the same 
	                    as the slope of the previous parabolic spline at this same point, with the exception of the 
	                    first parabolic spline which uses the slope of the linear spline as its beginning knot.
	    C2 continuity = A parabola connects the first pair of knots. Each subsequent pair of knots is connected with a 
	                    cubic spline where the slope and inflection of the cubic spline at the beginning knot is the 
	                    same as the slope of the previous cubic spline at this same point, with the exception of the 
	                    first cubic spline which uses the slope and inflection of the parabolic spline as its beginning 
	                    knot.
*/

using namespace std;

#include <stdio.h>
#include <GL/glut.h>
#include <iostream>
#include <vector>
#include <fstream> 
#include <time.h>
#include <string>
#include <algorithm>
#include <cmath>
#include <stdlib.h> 

//Begin globals---

int maxX = 1000; //Used to set up the coordinate space. X-range of window is from -200 to maxX+200 
int maxY = 3000; //Used to set up the coordinate space. Y-range of window is from -maxY to maxY


int continuity=0; //Continuity determines the type of spline connecting each knot (a location where two splines meet)
				  //Default value is 0 or linear splines

int sNum=0; //Keeps track of the spline in use (both for drawing the track and animating). Defaults to first spline.

float apexX =50;   //Used for first spline for continuity==2.  Parabola must got though each knot and this xCoord
float apexY =-300; //Used for first spline for continuity==2.  Parabola must got though each knot and this yCoord

long  NUM_TICKS = 10000;  //idle time between animation frames
bool stopped=true; //Used for animation. While true the animation is not triggered.

int oob=1; //Used for animation. Keeps track if a curve went out of bounds of not
int fudge=0; //Used for animation. Keeps track of how many curves went out of bounds

//---End globals

//---Start object declarations 
class Model {

public:
    
    Model () {startX=0;startY=0;};  //Constructor sets startX and startY to zero as the car always starts at 0,0 
     
    //Begin member functions---

    void readIn(char* inFilename);
    void drawCar();                 
    void drawKnots();
    
    void makeLinearMatrix(float x1,float y1,float x2,float y2);
    
    vector<float> rref(vector< vector<float> > A);

    void getLCoefficients();
    float linearValue(float x, int splineNum);
    void drawLinear();
    void makeParabMatrix(float x1,float y1,float x2,float y2, float slope);
    void makeParabMatrix(float x1,float y1,float x2,float y2, float x3,float y3);
    float parabSlope(float a, float b, float x);
    float parabValue(float x, int splineNum);
    void getPCoefficients();
    void drawParab();
    void makeCubeMatrix(float x1,float y1,float x2,float y2, float slope, float inflec);
    
    float cubeSlope(float a, float b, float c, float x);
    float cubeInflec(float a, float b, float x);
    float cubeValue(float x, int splineNum);
    float cubeExtrema(int f, int l, int& location, int splineNum);
    int findInboundX1(int xtremaX,int inbound, int splineNum);
    int findInboundX2(int firstX, int inboundY, int splineNum);
    void getCCoefficients();
    void drawCube();
    void clearVectors();

    //---End member functions

    //---Begin properties
    
    int numKnots; //Number of knots contained in the input file (first line of input file)
    float startX,startY; //Used for animation. startX is incremented by 1 at each tick and a new startY is calculated allowing the cart to move from it's previous position to its next postion 
    int anExtremaX;

  	vector<int> xCoords; //Vector to hold x coordinates of the knots contained in input file. All ints for simplicity but also wouldn't have much of an affect on "resolution" to force knots to ints if input as floats  
  	vector<int> yCoords; //Same as above but for the y coordinates 
  	vector<float> slopes; //Vector to hold the slopes of the splines at the point they intersect with a knot
  	vector<float> inflecs; //Same as above to hold inflections  
  	vector<vector<float> >linearMatrix; //Create an empty matrix to use in the RREF algorithm for linear splines
  	vector<vector<float> >parabMatrix; //Same as linearMatrix but for parabolic splines
  	vector<vector<float> >cubeMatrix; //Same as as linearMatrix but for cubic splines
 
  	vector<vector<float> >lCoefficients;//coefficients necessary to for the linear spline connecting each pair of knots 
  	vector<vector<float> >pCoefficients;//coefficients necessary to for the parabolic spline connecting each pair of knots 
  	vector<vector<float> >cCoefficients;//coefficients necessary to for the cubic equation connecting each pair of knots 
                                        //position 0 in the outer vector contains parabolic coefficients
  	//---End properties						 
	
};

Model rollercoaster;
//---End object declarations

//Begin object member function definitions---
void Model::readIn(char* inFilename){
	/*
	Reads in the input file and gives numKnots, xCoords, and yCoords
	their relevant values.

	Input: Pointer to the file
	Return: None if successful, error message if failed
	*/

	int inX,inY; //Hold the x and y values from the input file as they come in
	
	//Open the file
	ifstream inFile (inFilename);
	if (inFile.is_open()) {

		while(!inFile.eof()){
			
			//First line is number of knots
			inFile>>numKnots;
			
			int i=0;
			while(i<numKnots){
				//each subsequent line has x and y coords of a knot
				inFile>>inX>>inY;				
				xCoords.push_back(inX);
				yCoords.push_back(inY);
				i++;
			}
			
		}
	}
	else{
		//Could not read input
		cout<<"Input file could not be opened. Terminating..."<<endl;
		exit (EXIT_FAILURE);
	}
}

void Model::drawCar(){
	/*
	Draws a basic, red, roller coaster car centered around 0,0
	
	Input:None
	Return:None, but a basic car is drawn in the openGL window
	*/
	
	glColor3f (0.0, 0.0, 0.0);
	//Draw the cable that connects car to the track
	glBegin (GL_LINES);    
		glVertex2f (startX, startY);
		glVertex2f (startX, startY-450);
	glEnd();

	glColor3f (1.0, 0.0, 0.0);
	//Draw the car
	glBegin (GL_POLYGON);
		glVertex2f (startX-100, startY-450);
		glVertex2f (startX-100, startY-750);
		glVertex2f (startX+50, startY-750);
		glVertex2f (startX+50, startY-450);
	glEnd();

}

void Model::drawKnots(){
	/*
	Draws the knots given in the input file as vertical black line 
	centered on the proper coordinate

	Input:None
	Return:None, but the knots given in the input file are drawn in the 
		   openGL window
	*/

	glColor3f(0.0, 0.0, 0.0);


	for(int i=0;i<xCoords.size();i++){

		glBegin(GL_LINES);

		    glVertex2f(xCoords[i], yCoords[i] +500);			
		    glVertex2f(xCoords[i], yCoords[i]);

		glEnd();
	}

	glColor3f(0.7, 0.7, 0.7);
	glRectf(-250,-750,-15,0);
	glRectf(1000,-750,1550,0);

}


void Model::makeLinearMatrix(float x1,float y1,float x2,float y2){
	/*
	Creates the matrix necessary to use the RREF algorithm, which is
	required to find the coefficients for the equation of the linear spline
	connecting the given points    

	Input: Float value for the x and y coordinates of the two points we wish to connect
	Return:None, however it does update the linearMatrix property of the object
	*/

	linearMatrix.clear();

	//Matrix used for linear RREF has 2 rows
	vector<float> row0;
	vector<float> row1;

	//x1a+1b=y1c
	row0.push_back(x1);
	row0.push_back(1);
	row0.push_back(y1);

	//First row consists of the coefficients x1,1,y1
	linearMatrix.push_back(row0);
	
	//x2a+1b=y2c
	row1.push_back(x2);
	row1.push_back(1);
	row1.push_back(y2);

	//Second row consists of the coefficients x2,1,y2
	linearMatrix.push_back(row1);
	
}

vector<float> Model::rref(vector< vector<float> > A){
	/*
	This function implements the Reduced Row Echelon Form algorithm which given a matrix ( A[n][n+1] where n= degree+2)  
	of a set of simultaneous equations transforms the matrix into A', a matrix with A'[n][n] being the identity matrix 
	and A'[1...n][n+1] being the coefficients of the equation satisfying this set.

	Ex:
			|3	 2	1	1|      |1	0	0  -0.0999|
		A=	|8	 7	6	5|  A'= |0	1	0	0.3999|   x= vector<float>{-0.0999,0.3999,0.5000}
			|9	11	1	4|      |0	0	1	0.5000|



	RREF algorithm used is under MIT license (included in folder) and found here 
	https://github.com/MartinThoma/algorithms/blob/master/gaussian-elimination/gauss.cpp
	
	

	Input: Vector augmented matrix containing the set of simultaneous equations that must be solved
	Return: Vector containing the coefficients for the equation that satisfies the input set
	        of simultaneous equations
	*/


    int n=A.size();     
    for (int i=0; i<n; i++) {
        // Search for maximum in this column
        float maxEl = abs(A[i][i]);
        int maxRow = i;
        for (int k=i+1; k<n; k++) {
            if (abs(A[k][i]) > maxEl) {
                maxEl = abs(A[k][i]);
                maxRow = k;
            }
        }

        // Swap maximum row with current row (column by column)
        for (int k=i; k<n+1;k++) {
            float tmp = A[maxRow][k];
            A[maxRow][k] = A[i][k];
            A[i][k] = tmp;
        }

        // Make all rows below this one 0 in current column
        for (int k=i+1; k<n; k++) {
            float c = -A[k][i]/A[i][i];
            for (int j=i; j<n+1; j++) {
                if (i==j) {
                    A[k][j] = 0;
                } else {
                    A[k][j] += c * A[i][j];
                }
            }
        }
    }

    // Solve equation Ax=b for an upper triangular matrix A
    vector<float> x(n);
    for (int i=n-1; i>=0; i--) {
        x[i] = A[i][n]/A[i][i];
        for (int k=i-1;k>=0; k--) {
            A[k][n] -= A[k][i] * x[i];
        }
    }

    return x;
}

void Model::getLCoefficients(){
	/*
	When called the function calculates the coefficients of the line connecting a pair of knots

	Input: None
	Return: None, but the lCoefficients vector is updated at each call to hold all the 
	        coefficients that have been calculated so far.
	*/

	vector<float> temp;
	//number of splines= number of knots -1 as each spline connects a pair of knots
	int numLines=numKnots-1;

	//Calculate the linear coefficients for each spline
	for(int i=0;i<numLines;i++){
		makeLinearMatrix(xCoords[i],yCoords[i],xCoords[i+1],yCoords[i+1]);
		temp=rref(linearMatrix);
		lCoefficients.push_back(temp);
	}

}

float Model::linearValue(float x, int splineNum){
	/*
	When called the function calculates the yVal using the linear coefficients
	
	Input: Float value for xVal that needs a yVal and the spline it belongs to 
	Return: The yVal that corresponds to the input along the given linear spline 
	*/

	//y=ax+b
	return(lCoefficients[splineNum][0]*x+lCoefficients[splineNum][1]);
}

void Model::drawLinear(){	
	/*
	Draws the linear splines connecting each knot
	
	Input: None
	Return: None, but lines are drawn in the openGL window between each pair of knots 
	*/

	int i;//For loop counter
	int numLines=numKnots-1;
	getLCoefficients();
	//Lines drawn between each pair of knots
	for(i=0;i<numLines;i++){

		glBegin(GL_LINES);

			glVertex2f(xCoords[i],linearValue(xCoords[i], i));
			glVertex2f(xCoords[i+1],linearValue(xCoords[i+1], i));

		glEnd();
	
	}
	
}

void Model::makeParabMatrix(float x1,float y1,float x2,float y2, float slope){
	/*
	Creates the matrix necessary to use the RREF algorithm, which is
	required to find the coefficients for the equation of the parabolic spline
	with a given slope connecting the given points    

	Input: X and Y coordinates of the knots to be connected and the desired slope
		   of the parabolic spline at the beginning knot  
	Return: None, but parabMatrix is updated
	*/

	//Clear out any previous values stored in parabMatrix
	parabMatrix.clear();
	
	//System of simultaneous equations for parabolas requires 3 equations
	vector<float> row0;
	vector<float> row1;
	vector<float> row2;

	//x1^2a+x1b+1c=y1d
	row0.push_back(x1*x1);
	row0.push_back(x1);
	row0.push_back(1);
	row0.push_back(y1);

	parabMatrix.push_back(row0);

	//x2^2a+x2b+1c=y2d
	row1.push_back(x2*x2);
	row1.push_back(x2);
	row1.push_back(1);
	row1.push_back(y2);

	parabMatrix.push_back(row1);

	//2X1a+1b+0c=slope*d
	row2.push_back(2*x1);
	row2.push_back(1);
	row2.push_back(0);
	row2.push_back(slope);

	parabMatrix.push_back(row2);

}

void Model::makeParabMatrix(float x1,float y1,float x2,float y2, float x3,float y3){

	//Clear out any previous values stored in parabMatrix
	parabMatrix.clear();
	
	//Sytem of simultaneous equations for parabolas requires 3 equations
	vector<float> row0;
	vector<float> row1;
	vector<float> row2;

	//x1^2a+x1b+1c=y1d
	row0.push_back(x1*x1);
	row0.push_back(x1);
	row0.push_back(1);
	row0.push_back(y1);

	parabMatrix.push_back(row0);

	//x2^2a+x2b+1c=y2d
	row1.push_back(x2*x2);
	row1.push_back(x2);
	row1.push_back(1);
	row1.push_back(y2);

	parabMatrix.push_back(row1);

	//x3^2a+x3b+1c=y3d
	row2.push_back(x3*x3);
	row2.push_back(x3);
	row2.push_back(1);
	row2.push_back(y3);

	parabMatrix.push_back(row2);


}

float Model::parabSlope(float a, float b, float x){
	/*
	When called the function calculates the slope of the parabola with input
	coefficients at input x
	
	Input: A and b hold the coefficients for parabola at input x which holds the xCoord
	       of the point the slope must be calculated at
	Return: The slope of the parabola at x
	*/

	//slope= 2ax+b
	return(2*a*x+b);
}

float Model::parabValue(float x, int splineNum){
	/*
	When called the function calculates the yVal using the parabolic coefficients
	
	Input: Float value for xVal that needs a yVal and the spline it belongs to 
	Return: The yVal that corresponds to the input along the given parabolic spline 
	*/

	//y=ax^2+bx+c
	return(pCoefficients[splineNum][0]*x*x+pCoefficients[splineNum][1]*x+pCoefficients[splineNum][2]);
}

void Model::getPCoefficients(){
	/*
	When called the function calculates the coefficients of the parabola with given slope 
	connecting a pair of knots

	Input: None
	Return: None, but the pCoefficients vector is updated at each call to hold all the 
	        coefficients that have been calculated so far.
	*/
	
	int i; //For loop counter
	vector<float> temp; //Vector to hold temp hold coefficients after they are calculated 

	slopes.push_back((yCoords[1]-yCoords[0])/(xCoords[1]-xCoords[0])); //First spline is linear. Slope = (y2-y1)/(x2-x1)

	//Calculate all the parabolic coefficients
	for(i=1;i<numKnots;i++){
		makeParabMatrix(xCoords[i],yCoords[i],xCoords[i+1],yCoords[i+1], slopes[i-1]); //Slopes off by 1 as first is linear
		temp=rref(parabMatrix);
		pCoefficients.push_back(temp);
		slopes.push_back(parabSlope(temp[0],temp[1],xCoords[i+1]));
	}
	
}

void Model::drawParab (){
	/*
	Draws the linear spline connecting the first pair of knots and the parabolic spline connecting every other pair
	of knots
	
	Input: None
	Return: None, but the roller coaster continuity==1 "track" is drawn in the openGL window between each pair of knots 
	*/
	glEnable(GL_POINT_SMOOTH);
	//First pair connected by a line
	glBegin (GL_LINES);
		glVertex2f(xCoords[0],yCoords[0]);
		glVertex2f(xCoords[1],yCoords[1]);
	glEnd();


	getPCoefficients();

	int i;//Outer for loop counter
	float j;//Inner for loop counter
	float bound;//Stopping point for inner for loop	
	glPointSize(1.0);
	glBegin (GL_POINTS);
		int numParabs=numKnots-2;
		for(i=0;i<numParabs;i++){
			j=xCoords[i+1];//Start position of parabola
			bound= xCoords[i+2];//End position of parabola
			for(;j<=bound;j++){
				glVertex2f(j,parabValue(j,i));
			}
		}
	glEnd();

	glDisable(GL_POINT_SMOOTH);

}

void Model::makeCubeMatrix(float x1,float y1,float x2,float y2, float slope, float inflec){
	/*
	Creates the matrix necessary to use the RREF algorithm, which is
	required to find the coefficients for the equation of the cubic spline
	with a given slope and inflection connecting the given points    

	Input: X and Y coordinates of the knots to be connected and the desired slope and inflection
		   of the cubic spline at the beginning knot  
	Return: None, but cubeMatrix is updated
	*/
	
	//Clear out any previous values
	cubeMatrix.clear();

	//System of simultaneous equations for cubic requires 4 equations
	vector<float> row0;
	vector<float> row1;
	vector<float> row2;
	vector<float> row3;

	//x1^3a+x1b^2+x1c+1d=y1
	row0.push_back(x1*x1*x1);
	row0.push_back(x1*x1);
	row0.push_back(x1);
	row0.push_back(1);
	row0.push_back(y1);

	cubeMatrix.push_back(row0);

	//x2^3a+x2b^2+x2c+1d=y2e
	row1.push_back(x2*x2*x2);
	row1.push_back(x2*x2);
	row1.push_back(x2);
	row1.push_back(1);
	row1.push_back(y2);

	cubeMatrix.push_back(row1);

	//3x1^2a+2x1b+1c+0d=slope*e
	row2.push_back(3*x1*x1);
	row2.push_back(2*x1);
	row2.push_back(1);
	row2.push_back(0);
	row2.push_back(slope);

	cubeMatrix.push_back(row2);

	//6x1a+2b+0c+0d=inflec*e
	row3.push_back(6*x1);
	row3.push_back(2);
	row3.push_back(0);
	row3.push_back(0);
	row3.push_back(inflec);

	cubeMatrix.push_back(row3);

}

float Model::cubeSlope(float a, float b, float c, float x){
	/*
	When called the function calculates the slope of the cubic with input
	coefficients at input x
	
	Input: A,b,c hold the coefficients for cubic at input x which holds the xCoord
	       of the point the slope must be calculated at
	Return: The slope of the cubic at x
	*/

	//slope= 3ax^2+2bx+c
	return(3*a*x*x+2*b*x+c);
}

float Model::cubeInflec(float a, float b, float x){
	/*
	When called the function calculates the inflection of the cubic with input
	coefficients at input x
	
	Input: A,b hold the coefficients for cubic at input x which holds the xCoord
	       of the point the inflection must be calculated at
	Return: The inflection of the cubic at x
	*/

	//inflec= 6*ax+2b
	return(6*a*x+2*b);
}


float Model::cubeValue(float x, int splineNum){
	/*
	When called the function calculates the yVal using the cubic coefficients
	
	Input: xVal that needs a yVal and the spline it belongs to 
	Return: The yVal that corresponds to the input along the given cubic spline 
	*/

	//y=ax^3+bx^2+cx+d	
	return(cCoefficients[splineNum][0]*x*x*x+cCoefficients[splineNum][1]*x*x+cCoefficients[splineNum][2]*x+cCoefficients[splineNum][3]);
}

float Model::cubeExtrema(int f, int l, int& location,int splineNum){

	/*
	When called the function finds the ordered pair x, local max |f   (x)    |
	                                                             | splineNum | 
	
	Input: Range of x values represented by int f for first and int l for last,
	       int to hold the x coordinate of the extrema, and an int to determine
	       which spline to use 
	Return: The y coord of the extrema and (pass by reference) x coord of the extrema
	*/

	int i=f+1;//for loop counter
	float extrema, sign, tempA, tempB;//y coord of extrema, sign of extrema, temp variables used for swapping
	sign=cubeValue(f,splineNum);//Easier to do everything with absolute value and add the sign at the end
	extrema=fabs(sign); //arbitrarily set the first val to max
	for (; i <= l; i++){
		tempA=cubeValue(i,splineNum);
		tempB=fabs(tempA);
		//If next val is bigger than previous max replace it
		if(tempB> extrema){
			sign=tempA; //sign of new max
			extrema=tempB; //new max y coord
			location=i; //new max x coord
		}
	}
	//pos/pos=1 neg/pos=-1 allowing sign to be added back in
	return ((sign/(fabs(sign))) * extrema);
}

int Model::findInboundX1(int xtremaX,int inboundY, int splineNum){
	/*
	When called the function finds an inbound x coordinate to the left of the extrema with the desired y coord
	
	Input: Int x coord of the extrema, int y value of an inbound coordinate, and int splineNum 
	       for spline we are using
	      
	Return: The x coord of the inbound point to the left of the extrema with the desired y coord
	*/

	int xVal=xtremaX;
	//move away from the extrema to the left until y coord is inbound
	while (fabs(cubeValue(xVal,splineNum))>abs(inboundY)){
		xVal--;
	}

	return xVal;

}

int Model::findInboundX2(int firstX, int inboundY, int splineNum){
	/*
	When called the function finds an inbound x coordinate to the right of the extrema with the desired y coord
	
	Input: Int x coord of the extrema, int y value of an inbound coordinate, and int splineNum 
	       for spline we are using
	      
	Return: The x coord of the inbound point to the right of the extrema with the desired y coord
	*/


	int xVal=firstX;
	//move towards the extrema from the right until y coord is inbound
	while (fabs(cubeValue(xVal,splineNum))<abs(inboundY)){
		xVal--;
	}

	return xVal;

}

void Model::getCCoefficients(){
	/*
	When called the function calculates the coefficients of the cubic with given slope and inflection 
	connecting a pair of knots

	Input: None
	Return: None, but the cCoefficients vector is updated at each call to hold all the 
	        coefficients that have been calculated so far.
	*/

	vector<float> tempA;//temp vector to hold vals needs for spline0 (parabolic)
	//Have to make equation for first line a parab instead of a cubic
	makeParabMatrix(xCoords[0],yCoords[0],xCoords[1],yCoords[1],apexX,apexY);
	tempA=rref(parabMatrix);
	slopes.push_back(parabSlope(tempA[0],tempA[1],xCoords[1]));//Get calculated parabolas slope at end knot
	inflecs.push_back(2*tempA[0]); //Get calculated parabolas inflection at end knot
	cCoefficients.push_back(tempA);

	int offset=0;//keeps track of how much to offset to account for parabs to fix oob cubics
	int i,extremaX,inX1,inX2;//For loop counter, x val of y value of the extrema of a spline, inbound left x coordinate, inbound right x coordinate
	float extremaY,sign; //absolute y value of the extrema of a spline, y value of the extrema of a spline
	vector<float> tempB;//Temp hold cubic coefficients to calculate slope and inflection
	vector<float> tempC;//Temp hold parabolic coefficients connecting two inbound points of oob curve
	//Calculate all the cubic splines
	for(i=1;i<numKnots-1;i++){
		//need a cubic through xi,yi and xi+1,yi+1 with the same slope inflection at xi as xi-1
		makeCubeMatrix(xCoords[i],yCoords[i],xCoords[i+1],yCoords[i+1], slopes[i-1], inflecs[i-1]);
		tempB=rref(cubeMatrix);
		sign= cubeSlope(tempB[0],tempB[1],tempB[2],xCoords[i+1]);
		slopes.push_back(sign);
		//Squared equation has 2 solutions. need neg for decreasing (neg slope) and pos for increasing (pos slope)
		if(sign<0)
			inflecs.push_back(-1*cubeInflec(tempB[0],tempB[1],xCoords[i+1]));
		else
			inflecs.push_back(cubeInflec(tempB[0],tempB[1],xCoords[i+1]));

		cCoefficients.push_back(tempB);

		extremaY=cubeExtrema(xCoords[i],xCoords[i+1],extremaX,i+offset);
		//Part of the curve lies outside the window. Substitute with a parabola.
		if(extremaY>maxY){
			//Need to replace part of the curve above the window
			//Find two places that the curve is inside the window
			tempC.clear();
			inX1=findInboundX1(extremaX,maxY-500,i+offset);
			inX2=findInboundX2(xCoords[i+1],maxY-700,i+offset);
			//Make a parabola through those points and the point in between them with val maxy-200
			makeParabMatrix(inX1,maxY-500,((inX1+inX2)/2),maxY-200,inX2,cubeValue(inX2,i+offset));
			tempC=rref(parabMatrix);
			//Parabolic spline with cubic coefficients so a=0
			tempC.insert(tempC.begin(),0);
			cCoefficients.push_back(tempC);
			offset++;
		}

		else if(extremaY<-maxY){
			//Need to replace part of the curve below the window
			//Find two places that the curve is inside the window
			//Needs more room so cart doesn't go off screen
			tempC.clear();
			inX1=findInboundX1(extremaX,-maxY+900,i+offset);
			inX2=findInboundX2(xCoords[i+1],-maxY+900,i+offset);
			//Make a parabola through those points and the point in between them with val -maxy+800
			makeParabMatrix(inX1,-maxY+900,((inX1+inX2)/2),-maxY+800,inX2,cubeValue(inX2,i+offset));
			tempC=rref(parabMatrix);
			tempC.insert(tempC.begin(),0);
			cCoefficients.push_back(tempC);
			offset++;
		}
	}
}

void Model::drawCube (){
	/*
	Draws the parabolic spline connecting the first pair of knots and the cubic spline connecting every other pair
	of knots
	
	Input: None
	Return: None, but the roller coaster continuity==2 "track" is drawn in the openGL window between each pair of knots 
	*/
	
	getCCoefficients();
	
	//Draw a parab between start and the first knot
	glEnable(GL_POINT_SMOOTH);
	glBegin (GL_POINTS);

		for (int i = 0; i < xCoords[1]; i++){
			glVertex2f(i,cCoefficients[0][0]*i*i+cCoefficients[0][1]*i+cCoefficients[0][2]);
		}
		
	glEnd();

	int i, extremaX, inX2;//Outer for loop counter, x coordinate of extrema, x coordinate of the right side of the cubic inside the window
	float sign,extremaY;//is extrema a max or min, y coord extrema
	float j;//Inner for loop counter
	float bound;//Stopping condition for inner for loop	
	glPointSize(1.0);

	glBegin (GL_POINTS);
		
		int numCubes=cCoefficients.size()-1;//One less cubic spline because first is parabolic
		//Cubic functions for the rest of the splines
		for(i=1;i<numCubes;i++){
			j=xCoords[i];
			bound= xCoords[i+1];

			if(cCoefficients[i][0]==0)
				i++;

			sign=cubeExtrema(j,bound, extremaX,i);
			extremaY=fabs(sign);

			//only draw cubes that don't go out of bounds
			if(extremaY<maxY){
				
				for(;j<=bound;j+=.1){
					glVertex2f(j,cubeValue(j,i));
				}
			}
			
			else{
				//extrema is a max
				if(sign>0){ 

					inX2=findInboundX2(bound,maxY-700,i);
					//use cubic spline as normal until near extrema
					for(;cubeValue(j,i)<(maxY-500);j+=.1){
						glVertex2f(j,cubeValue(j,i));
					}
					//switch to parabolic until back in window
					for(;j<inX2;j+=.1){
						glVertex2f(j, cubeValue(j,i+1));
					}
					//back to cubic
					for (;j <= bound;j+=.1){
						glVertex2f(j,cubeValue(j,i));
					}
				}

				else{ 
					//extrema is a min
					inX2=findInboundX2(bound,-maxY+900,i);
					//use cubic spline as normal until near extrema
					//Mins need more room for cart to go below
					for(;cubeValue(j,i)>(-maxY+900);j+=.1){
						glVertex2f(j,cubeValue(j,i));
					}
					//parabolic
					for(;j<inX2;j+=.1){
		
						glVertex2f(j, cubeValue(j,i+1));
					}
					//cubic
					for (;j <= bound;j+=.1){
					
						glVertex2f(j,cubeValue(j,i));
					}
				}
			}
		}
	glEnd();
	
	glDisable(GL_POINT_SMOOTH);

}

void Model::clearVectors(){
	/*	
	Clears out the slopes, inflecs, pCoeffcients, and cCoefficints vectors

	Input: None
	Return: None, but the roller coaster continuity==2 "track" is drawn in the openGL window between each pair of knots 
	*/
	slopes.clear();
	inflecs.clear();
	pCoefficients.clear();
	cCoefficients.clear();
}

//---End object member function definitions

//Begin openGL functions---
static void Idle( void ){
	/*	
	Handles animation

	Input: None
	Return: None, but animates the car moving along the track
	*/
	if(!stopped){
	    clock_t endWait;  //end of wait interval 


		if(continuity==0){ //linear spline
			
			//Stops the animation when the car reaches the end of the track 
			if(rollercoaster.startX==maxX)
				return;
			//Catch only needed for continuity==0 as startX==0 doesn't satisfy the next else if conditional as intended 
			else if(rollercoaster.startX==0){
				rollercoaster.startX+=1;
				rollercoaster.startY=rollercoaster.linearValue(rollercoaster.startX, sNum);	
			}				
			//if the xCoord is not a knot advance the cart 1 tick according to current equation
			else if(find(rollercoaster.xCoords.begin(),rollercoaster.xCoords.end(),rollercoaster.startX) ==rollercoaster.xCoords.end()){
				rollercoaster.startX+=1;
				rollercoaster.startY=rollercoaster.linearValue(rollercoaster.startX, sNum);	
			}
			else{
				//Reached a knot an have to change equations before advancing
				sNum++;
				rollercoaster.startX+=1;
				rollercoaster.startY=rollercoaster.linearValue(rollercoaster.startX, sNum);	
			}
		}

		else if(continuity==1){ //parabolic splines
				//Stops the animation when the car reaches the end of the track 
				if (rollercoaster.startX==1000)
					return;

				//First spline is linear so animation is handled separately
				else if(rollercoaster.startX<(rollercoaster.xCoords[1])-1){
					rollercoaster.startX+=1;
					rollercoaster.startY=rollercoaster.linearValue(rollercoaster.startX, sNum);

				}
				else{
					//If the next tick isn't on a knot advance it one tick using the existing equation
					if(find(rollercoaster.xCoords.begin(),rollercoaster.xCoords.end(),rollercoaster.startX+1) ==rollercoaster.xCoords.end()){
						rollercoaster.startX+=1;
						rollercoaster.startY=rollercoaster.parabValue(rollercoaster.startX, sNum-1);
					}
					//Else change equations and advance one tick using the new equation
					else{
						sNum++;
						rollercoaster.startX+=1;
						//No equation for startX=1000 but has known value startY=0
						if (rollercoaster.startX==1000){
							rollercoaster.startY=0;
						}
						else
							rollercoaster.startY=rollercoaster.parabValue(rollercoaster.startX, sNum-1);
					}
				}
		}

		else if(continuity==2){ //cubic splines
				
				int inX1,inX2; 
				//Stops the animation when the car reaches the end of the track 
				if (rollercoaster.startX==1000)
					return;
				//First spline is parabolic so animation is handled separately
				else if(rollercoaster.startX<(rollercoaster.xCoords[1])-1){
					rollercoaster.startX+=1;
					rollercoaster.startY=rollercoaster.cCoefficients[0][0]*rollercoaster.startX*rollercoaster.startX+ rollercoaster.cCoefficients[0][1]*rollercoaster.startX+ rollercoaster.cCoefficients[0][2];
				}
				else{
					//If the next tick isn't on a knot 
					if(find(rollercoaster.xCoords.begin(),rollercoaster.xCoords.end(),rollercoaster.startX+1) ==rollercoaster.xCoords.end()){
						//If the spline we are on doesn't go out of bounds draw as normal
						if(fabs(rollercoaster.cubeExtrema(rollercoaster.xCoords[sNum],rollercoaster.xCoords[sNum+1],rollercoaster.anExtremaX,sNum+fudge))<maxY){
							rollercoaster.startX+=1;
							rollercoaster.startY=rollercoaster.cubeValue(rollercoaster.startX, sNum+fudge);
							//if the curve stays in bounds oob is not affected
							oob=oob*1;
						}
						else{
							//if curve goes over screen
							if(rollercoaster.cubeExtrema(rollercoaster.xCoords[sNum],rollercoaster.xCoords[sNum+1],rollercoaster.anExtremaX,sNum+fudge)>0){		
								inX1=rollercoaster.findInboundX1(rollercoaster.anExtremaX,maxY-500,sNum+fudge);
								inX2=rollercoaster.findInboundX2(rollercoaster.xCoords[sNum+1],maxY-700,sNum+fudge);
							}
							//else curve goes under screen
							else{
								inX1=rollercoaster.findInboundX1(rollercoaster.anExtremaX,-maxY+900,sNum+fudge);
								inX2=rollercoaster.findInboundX2(rollercoaster.xCoords[sNum+1],-maxY+900,sNum+fudge);
							}
							//If on part of curve that does not go out of bounds
							if(rollercoaster.startX<=inX1 || rollercoaster.startX>=inX2){
								//proceed as normal
								rollercoaster.startX+=1;
								rollercoaster.startY=rollercoaster.cubeValue(rollercoaster.startX, sNum+fudge);
							}

							else{
								//else use the equation connecting the two inbound points
								rollercoaster.startX+=1;
								rollercoaster.startY=rollercoaster.cubeValue(rollercoaster.startX, sNum+fudge+1);
							}
							//If the curve ever goes out of bounds oob will have a value of 0
							oob=oob*0;
						}
					}
					else{
						 
						//At a knot. change equations and advance one tick using the new equation
						sNum++;
						//If we went out of bounds have to advance another equation
						if(oob==0){
							fudge++;
							oob=1;//reset for next time through
						}
						//Handle last tick a little differently. Known value 1000,0
						if (rollercoaster.startX==1000){
							rollercoaster.startY=0;
						}
						//otherwise proceed as normal
						else{
							rollercoaster.startX+=1;
							rollercoaster.startY=rollercoaster.cubeValue(rollercoaster.startX, sNum+fudge);
						}
					}
				}
		}

	   endWait = clock () + NUM_TICKS;
	   //Wait until the tick ends
	   while (clock () < endWait);
	   
	   //Changes the next iteration of glutMainLoop
	   glutPostRedisplay();
	}
}


void display (){
	/*	
	Draws the static elements of the scene as well as the track connecting the knots
	according to the value of continuity

	Input: None
	Return: None, but does manipulate openGL window as described above
	*/  

	glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	rollercoaster.drawCar();
	rollercoaster.drawKnots();

	if(continuity==0){
		rollercoaster.drawLinear();
	}

	else if(continuity==1){
		rollercoaster.clearVectors();
		rollercoaster.drawParab();
	}

	else if(continuity==2){
		rollercoaster.clearVectors();
		rollercoaster.drawCube();
	}

	else{
		//Any unexpected input caught and forced to linear
		rollercoaster.drawLinear();
	}

	glutSwapBuffers();

}

void init (){
	/*	
	Initializes the openGL window

	Input: None
	Return: None
	*/   
	glPixelStorei (GL_UNPACK_ALIGNMENT, 1);
	glClearColor (0.8, 0.8, 0.8, 0.0);

	glMatrixMode (GL_PROJECTION);
	glLoadIdentity();

	//Add a little room on the left and right so the line for the knot isn't right on the edge of the window
	gluOrtho2D (-200.0, maxX+200, -maxY, maxY);

}

void keyboard (unsigned char key, int x, int y){
	/*	
	Handles keyboard input

	Input: key,x,y which come from glutKeyboardFunc. Key is the pressed and x,y are the mouse position
	       when the key is pressed 
	Return: None
	*/
	switch (key) {
		case '0' : continuity=0;
				   sNum=0;
		           break;
		case '1' : continuity=1;
				   sNum=0;
		           break;
		case '2' : continuity=2;
				   sNum=0;
		           break;
		case 45  : NUM_TICKS+=250; //Decreases speed by increasing time between animation ticks
		           break;
		case 43  : NUM_TICKS-=250; //Increases speed by decreasing time between animation ticks
		           break;
		case 'r' : rollercoaster.startX=0;
				   rollercoaster.startY=0;
				   stopped=true;
				   sNum=0;
				   fudge=0;
				   NUM_TICKS = 10000;
		           break; //Resets the car to the start position, stops animation, resets to spine 0, and resets the speed to default
		case 's' : stopped=false;//Starts the animation
		           break;
		case 27  : 
		case 'q' : exit (1);    // either <esc> or 'q' will quit program
	}
	glutPostRedisplay();

}
//---End openGL functions

int main (int argc, char** argv)
{
	//Output controls to console
	cout<<"0: Choose linear piecewise spline (default)"<<endl;
	cout<<"1: Choose parabolic piecewise spline"<<endl;
	cout<<"2: Choose cubic piecewise spline"<<endl;  
	cout<<"-: Move slower"<<endl;
	cout<<"+: Move faster"<<endl;
	cout<<"r: return to start"<<endl;
	cout<<"s: start animation"<<endl;
	cout<<"q: quit"<<endl;

	//Read in the user input file
	rollercoaster.readIn(argv[1]);  

	//Begin openGL initializations---
	glutInit(&argc, argv);
    glutInitDisplayMode (GLUT_DOUBLE | GLUT_RGB);
    glutInitWindowSize (800, 600); 
    glutInitWindowPosition (100, 100);
    glutCreateWindow ("Five Flags Sim");
    init ();
    //---End openGL initializations

    glutDisplayFunc(display);

    //Animation function
    glutIdleFunc( Idle );
    //Begin openGL event handlers
    glutKeyboardFunc (keyboard);
    

    glutMainLoop();

    return 0; 
}