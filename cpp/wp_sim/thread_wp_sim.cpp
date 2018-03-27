/*
Name: Austin Gillis

Program Name: 'Word Processing UltraLite' Pthreads Simulation 

Purpose: Use pthreads to format and justify an input file. Using parallelism for this problem makes sense as it can be
         divided up into tasks that can run simultaneously. There is no reason to wait for the whole input file to be read 
         in before the first line can be formatted or printed as output. Threads are required as each subtask is working 
         on the same data and need shared memory. 

Input (from terminal): The input will be a text file of any length and the name of the file. The file will
                       contain normal words and punctuation as well as control sequences. No line may exceed 50 chars 
                       without adjusting CHARS_A_LINE accordingly.

                       The following are valid control sequences: /c /C /u
		               Only one control sequence can be used on one word. 

Output:  The program outputs to the console lines of the input file with the control sequence carried out. 

		 /ccomputer   -> Computer
		 /Cfriday     -> FRIDAY
		 /uNew /uYork -> _New_ _York_
*/

#include <iostream>
#include <string>
#include <string.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <pthread.h>
#include <unistd.h>
#include <semaphore.h>
#include <stdlib.h>

using namespace std;

//control sequence constants
const char SHIFT ='c';         //Capitalize the next letter
const char CAPS_LOCK='C';      //Capitalize the next word
const char UNDERLINE='u';      //Underline the next word (simulated as such: _underlined_)
const char CONTROL_DELIM=47;   // ASCII value for /  All control sequences start with /

const char APOS=39; //ASCII value for '  Needed so underline functions as such: _isn't_     and not as such: isnt'_t  
const char UNDERSCORE=95;//ASCII value for _

const int CHARS_A_LINE=50; // Number of characters to justify text to

//Global vector to hold lines as they come in and as they are processed
vector<string> input;

//counters for semaphore
sem_t find_replace_counter;     	  
sem_t write_out_counter; 

//Bool for find_and_replace and write_out.  Want to enter the loop the first time even if the size of vector is 0
bool first_pass= true;

int line_counter=0; //keeps track of number of lines read in from input file
int i_dont_space;//used to hold the index of a line that should not be justified
				 //ie last line of a paragraph

//Begin function declarations--- 
int count_words(string s);
void * read_in(void *);
void * find_and_replace(void *);
void * write_out(void *);
//---End function declarations

int main(){

	cout << "\nEnter the name of the file (including the extension) you wish to format."<< endl;

    //Variable for input filename
    string in_filename;
    
    cin >> in_filename;
    cout << "\n";

    //Initialize the counters to 0
    sem_init(&find_replace_counter, 0, 0);
    sem_init(&write_out_counter, 0, 0);
  
    //Pass the filename to the read function
    char * cstr = new char [in_filename.length()+1];
    strcpy (cstr, in_filename.c_str());

    //Create the threads
    pthread_t thread1, thread2, thread3;

    //Thread one reads in a line
    pthread_create( &thread1, NULL, read_in, (void *) cstr);
    //Thread two finds control sequences and carries them out           
    pthread_create( &thread2, NULL, find_and_replace, NULL); 
    //Thread three justifies the line and outputs it 
    pthread_create( &thread3, NULL, write_out, NULL); 

    //Wait for things to finish before moving on
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    pthread_join(thread3, NULL);


	return 0;
}

int count_words(string s) {

	/*
	This function counts the number of words in the input string

	Input: A string containing a line of input
	Return: Integer representing the number of words in the line
	*/

	//i is a counter, n holds the size of the string, and count holds the total word count
    int i = 0, N = s.size(), count = 0;
    while(i < N) {
        //Move over counter until it hits a letter or an underscore (leading underscore part of the word)
        while(i < N && !isalpha(s[i]) && s[i]!=UNDERSCORE) i++;
        //Stop if counter is at the end of the string
        if(i == N) break;
        //Move until not a letter (apostrophes and underscores do not signal end of word)
        while(i < N && isalpha(s[i]) || s[i]==APOS || s[i]==UNDERSCORE) i++;
        //Nonletter-letters-nonletter assumed to be word so increment the word count
        count++;
    }
    return count;
}

void * read_in(void * ptr){

	/*
	Reads in the input file 

	Input: Pointer to the file
	Return: None if successful, error message if failed
	Lines of input freely added to vector<string> input
	*/

	//Cast the pointer to the filename back to a char
	char * in_filename = (char *) ptr;

	ifstream infile (in_filename);
    //Grabbed desired file... attempting to open
    if (infile.is_open()) {
      //Variable to hold a line from the input file
      string line;
      //Keep adding lines to the vector until eof
      while ( getline (infile,line) ){
      	input.push_back(line);
      	line_counter++;
      	if(line.size()==0){
      		//index of line in vector<string> input
      		i_dont_space=line_counter-2;
      	}
      	//Every time a line is read in allow find_and_replace to run
      	sem_post(&find_replace_counter);
      }
    infile.close();
  	}
  	else{

  		cout<<"Unable to open specified file. Ending execution..."<<endl;
  		exit(1);
  	}
}

void * find_and_replace(void * arg){
	/*
	Searches a line for control characters
	If one if found the appropriate formatting is carried out and the control character is removed

	Input: Dummy argument as required by pthreads
	Return: None but,
	formatted lines added to vector<string> input. limited by the the read in function. cant process a line before it's read in
	*/

	//Process all lines. Likely to get here while input.size()=0 but must proceed to semaphore and wait there 
	for(int i = 0; i<input.size() || first_pass;i++){
		//Wait for read_in to signal that there is a line to process
		sem_wait(&find_replace_counter);

		int firstCC= input[i].find(CONTROL_DELIM); //First instance of / which indicates a control character is next 

		//If the line has any control characters
		if(firstCC!=string::npos) {
		
			//Holds the current match being processed
			int found= firstCC;

			//Nothing found by string find function returns string::npos
			while (found!= string::npos){
	  			//Find control character delimiter \ check next char to figure out if shift, caps lock, or underline
	  			if(input[i][found+1]==SHIFT){
		  			//Remove the control sequence
		    		input[i].erase(found,2);
		    		//Capitalize the first letter
		    		input[i][found]= toupper(input[i][found]);
	  			}

	  			else if(input[i][found+1]==CAPS_LOCK){
					//Remove the control sequence
					input[i].erase(found,2);
					int j= found;
					//j starts at first letter to be capitalized and increases by 1 until the char it indexes is not a letter
					while(isalpha(input[i][j])){
						input[i][j]= toupper(input[i][j]);
						j++;
					}
	  			}

	  			else if(input[i][found+1]==UNDERLINE){
	  				//Erase control sequence characters from string
					input[i].erase(found,2); 
					//Add leading _
					input[i].insert(found, "_");
					int j= found+1;
					//j starts at first letter to be capitalized and increases by 1 until the char it indexes is not a letter (starts off at found+1 to account for the added _)
					while(isalpha(input[i][j]) || input[i][j]== APOS){
						j++;
					}
					//Add trailing _
					input[i].insert(j, "_");
	  			}
	  			//Find next control character
	  			found= input[i].find(CONTROL_DELIM, found); 
			}  
		}
		else{
			//Catch paragraphs.  Newlines read in by getline return ""
			if(input[i].size()==0){
				input[i]+="\n";
			}
		}
		//Set first pass to false after first time through the loop
		first_pass=false;
		//Every time a line is finished with the find_and_replace routine allow write_out to run
		sem_post(&write_out_counter);
	}
}

void * write_out(void * arg){	
	/*
	Justifies each line to 50 characters with extra characters being distributed as extra spaces between words
	then writes the line out to the console

	Input: Dummy argument as required by pthreads
	Return: None but,
	formatted lines justified and wrote out to console. limited by the the find and replace function. cant print a line before it's formatted
	*/

	//Allows function to get to wait if this thread gets to the for before the first line is read in
	first_pass=true;

	//Loop until the last entry as that one does not need spaces added
	for(int i=0;i<(input.size() -1) || first_pass ;i++){
		//Wait until find_and_replace signals there is a line ready for processing
		sem_wait(&write_out_counter);
		if(input[i]!="\n" && i!=i_dont_space){
			//Make all double space single spaces (rather common to put two spaces after a period)
			int first_two_space= input[i].find("  ");

			while (first_two_space!= string::npos){ 

				input[i].erase(first_two_space,1);
				first_two_space=input[i].find("  ", first_two_space);

			}

		  	//Find first and last space
		    int first_space= input[i].find(" "); 
		    int lastSp= input[i].rfind(" ");

		    //Number of spaces = number of words -1
		    int count= count_words(input[i]) -1;
		    //Number of extra spaces to be added to each existing space
		    int space_count= ((CHARS_A_LINE-input[i].size())/count);

			//if there is a space in the line
			if(first_space!=string::npos){
		    //If there is only one space
			    if (first_space== lastSp){
			      for(int j=0;j<space_count;j++){
			            input[i].insert(first_space, " ");
			          }
			    }
			    //If there is more than one space
			    else{
					//Holds the current match being processed
					int found= first_space;
					//Only go up to the last space as that space may need more than the rest added to it
					while (found!= string::npos){
					//Add in the necessary spaces
						for(int j=0;j<space_count;j++){
							input[i].insert(found, " ");
						}
						//Move found to the next match
						found= input[i].find(" ", found+space_count+1);
					}
					int j=0;//counter to mark where a space was found
					if(count*space_count!=CHARS_A_LINE-input[i].size()){
						while(input[i].size()!=CHARS_A_LINE){
							//Find a space to add more space to
							while(isalpha(input[i][j])|| input[i][j]==UNDERSCORE){ 
								j++;
							}
							//add the extra spaces
							input[i].insert(j, " ");
							while(!isalpha(input[i][j])){
								if(input[i][j]!=UNDERSCORE)
									j++;
							}
						}
					}
			    }
			}
		}
		//If the line is not a newline print it and add a newline
		if(input[i]!="\n"){
			cout << input[i]<<endl;
		}
		//If the line is a newline just print the newline
		else{
			cout << input[i];
		}
		//Set first_pass to false after the first time through to prevent infinite loop
		first_pass=false;
	}
	//Last sentence should not be spaced as the others so just print it normally
	sem_wait(&write_out_counter);
	cout << input.back()<<endl; 
}