"""-------------------------Written in python3----------------------------------------
Programmer: Austin Gillis

SUMMARY: This program works and identifies and examines the upstream region of a 
         gene for three distinct motifs.
    
INPUT:   from terminal- User enters in the filename in FASTA format containting 
                        the DNA to be examined.

OUTPUT:  The program prints DNA with formatted TATA box, locations of upstream 
         sequence, TATA box and downstream sequence, upstream string, its length 
         and the percentage of its length to entire sequence, and the location 
         and percentage of upstream sequence for direct repeats, mirror repeats 
         and CAG repeats to the console as output.  If no TATA box or upstream 
         sequenece exist the program prints that to the console as output. 

        
Example output:

         ---+++ Upstream Sequence Analyzer v0.1 +++---

Enter the name of the file you want to use:test2.fna
The size of the region being searched is: 52 bp
-------------------------------------------------------------------------------------- 

aaagggccctttaaccccccTATATATAgcgggcggcttcgcgaggacttg
Upstream:   [1: 20 ]
TATA-Box:   [ 21 : 29 ]
Downstream: [ 29 : 52 ]

 ========================================

    UPSTREAM of TATA-box

======================================== 

AAAGGGCCCTTTAACCCCCC
The Upstream length is: 20
Percentage of upstream region is:38.46 %

 ========================================

    Searching for Direct Repeats (DR)

======================================== 

Found DR: CCCCCC [ 15 to 20 bp]

Percent of MR's in the upstream region is:30.00 %

 ========================================

    Searching for Mirror Repeats (MR)

======================================== 

Found MR: CCCC [ 15 to 18 bp]

Percent of MR's in the upstream region is:20.00 %

 ========================================

    Searching for CAG Repeats (CR) 

======================================== 

No CAG repeats were found.

    
------------------------------------------------------------------------------
"""

import re
import os

def getDNA( filename ):
    """ 
    Opens a FASTA file of DNA, reads it, and return the DNA as one string.

    Input: Name of file to be analyzed 
    Return: String containing the bases that make up of the input 

    """
    
    # make sure there really *is* a filename with this name
    if (not os.path.isfile(filename)):
        print ("No file found in current directory named: ", filename)
        return ""
    else:
        DNA = ""
        with open(filename) as INPUT:
            next(INPUT)  # skip the header line
            # now read all the other lines in the file
            for nextLine in INPUT: 
                nextLine= nextLine.strip()  # remove the newline
                DNA = DNA + nextLine
            # end for each line
            DNA= DNA.upper()    
            return DNA

def findDirectRepeats(upstreamSequence):
    """ 
    Reports all Direct Repeat (DR) motifs found of total length between 4-12 
    bp and their location within the substring

    Input: String representing sequence of DNA to be analyzed
    Return: None but,
    prints the results of its analysis to the terminal

    """
    
    DRregex = re.compile( r"([ATCG]{2,6})\1" ) #Between 2 and 6 AorTorCorG repeated  
    m= DRregex.search(upstreamSequence)
    DRiterator = DRregex.finditer(upstreamSequence) # find all matches
    
    totalDRlength=0
    if m:
        for nextDR in DRiterator: # loop thru list of matches
            DR = nextDR.group()
            DRstart = nextDR.start() # where did it begin
            DRend = nextDR.end()     # location just after the end
            totalDRlength= totalDRlength + len(DR) #Add the length of the current DR to the total
            print ("Found DR:", DR, "[", DRstart+1, "to", DRend, "bp]")
    
        directRepeatPercent= totalDRlength / (len(upstreamSequence)) * 100 #find length of all DR by length of upstream sequence
        print ("\nPercent of DR's in the upstream region is:%.02f" % directRepeatPercent, "%")
        
    else:
        print("No mirror repeats found")
    
 

def findMirrorRepeats(upstreamSequence):
    """ 
    Reports all Mirror Repeat (MR) motifs found of total length 6 bp and 
    their location within the substring

    Input: String representing sequence of DNA to be analyzed
    Return: None but,
    prints the results of its analysis to the terminal

    """
    
    MRregex = re.compile( r"(.)(.)(.)\3\2\1" ) # anycharAanyCharBanyCharCanyCharCanyCharBanycharA 
    m= MRregex.search(upstreamSequence)
    MRiterator = MRregex.finditer(upstreamSequence) # find all matches
    if m:
        totalMRlength=0
        for nextMR in MRiterator: # loop thru list of matches
            MR = nextMR.group()      # get the actual regex match
            MRstart = nextMR.start() # where did it begin
            MRend = nextMR.end()     # location just after the end
            totalMRlength= totalMRlength + len(MR) #Add the length of the current MR to the total
            print ("Found MR:", MR, "[", MRstart+1, "to", MRend, "bp]")
            
        
        mirrorRepeatPercent= totalMRlength / (len(upstreamSequence)) * 100 #find length of all MR by length of upstream sequence
        print ("\nPercent of MR's in the upstream region is:%.02f" % mirrorRepeatPercent, "%")
    
    else:
        print("No mirror repeats found")

def findCAGrepeats (upstreamSequence):
    """
    Finds all CAG repeats and their location within the substring

    Input: String representing sequence of DNA to be analyzed
    Return: None but,
    prints the results of its analysis to the terminal

    """
    
    
    CRregex = re.compile( r"(CAG)\1+" ) #CAGCAG(any more CAG)
    m= CRregex.search(upstreamSequence)
    CRiterator = CRregex.finditer(upstreamSequence) # find all matches
    
    
    totalCRlength=0
    if m:
        for nextCR in CRiterator: # loop thru list of matches
            CR = nextCR.group()
            CRstart = nextCR.start() # where did it begin
            CRend = nextCR.end()     # location just after the end
            print ("Found CR:", CR, "[", CRstart+1, "to", CRend, "bp]")        
            totalCRlength= totalCRlength + len(CR)  #Add the length of the current CR to the total
        
        percentCR= totalCRlength/len(upstreamSequence) * 100 #find length of all CR by length of upstream sequence     
        
        print("Percent of CR's in the upstream region is: %.02f" % percentCR, "%\n")
    
    else:
        print("No CAG repeats were found.\n")    



def main():
    
    print ("\n       ---+++ Upstream Sequence Analyzer v0.1 +++---\n")

# (1) Read in user imputed DNA file
    
    filename= input("Enter the name of the file you want to use:")
    DNA= getDNA(filename)

#-------------------------------------------------------------------------------

# (2) Determine if there is a TATA box. 
    """
    =================================================================== 

    TATA box: total length 8 bp where the first four nucleotides are 
              TATA, the fifth nucleotide is either an A or a T, the 
              sixth nucleotide is an A, the seventh nucleotide is 
              either an A or a T, and the eighth nucleotide is either 
              an A or a G    

    REGEX patterns used: TATA[AT]A[AT][AG]  


    ===================================================================
    """


    TATAboxRegex = re.compile(r'TATA[AT]A[AT][AG]')
    m= TATAboxRegex.search(DNA)
    
#-------------------------------------------------------------------------------
    
# (3) Print DNA with formatted TATA box.    
    if m:
        
        TATAboxRegex= re.compile(r'TATA[AT]A[AT][AG]')
        m = TATAboxRegex.search(DNA)

        boxStart= m.start()
        boxEnd= m.end()
        upstreamSequence= DNA[:boxStart]
        TATAbox= DNA[boxStart:boxEnd]
        downstreamSequence= DNA[boxEnd+1:]

        # formattedDNA= upstreamSequence.lower() + TATAbox + downstreamSequence.lower()
        
        print("The size of the region being searched is:", len(DNA), "bp")
        print("-"*50,"\n")
        # print(formattedDNA)
    
        #-----------------------------------------------------------------------
        
        # (4) Print locations of upstream sequence, TATA box, and downstream sequence
        
        if len(upstreamSequence)>0:
            TATAstart= len(upstreamSequence)+ 1
            TATAend= TATAstart + len(TATAbox) 
            print("Upstream:   [1:", len(upstreamSequence),"]")
            print("TATA-Box:   [", TATAstart, ":", TATAend,"]")
            if len(downstreamSequence)>0:
                print("Downstream: [", TATAend, ":", len(DNA),"]")
            else:
                print("Downstream:  [Does not exist]") 
       
        else:
            TATAstart= len(upstreamSequence)+ 1
            TATAend= TATAstart + len(TATAbox)             
            print("Upstream:   [Does not exist]")
            print("TATA-Box:   [", TATAstart, ":", TATAend,"]")
            if len(downstreamSequence)>0:
                print("Downstream: [", TATAend+1, ":", len(DNA),"]")
            else:
                print("Downstream:  [Does not exist]")             
        
        
        #-----------------------------------------------------------------------
        
        # (5) Print upstream string, its length, and the percentage of its length to entire sequence 
        if len(upstreamSequence)>0:
            
            print("\n","="*50)
            print("\n\tUPSTREAM of TATA-box\n") 
            print("="*50,"\n")
            
            upstreamLength= len(upstreamSequence)
            upstreamPercentage= upstreamLength/len(DNA) * 100
            print(upstreamSequence)
            print("The Upstream length is:", upstreamLength)
            print("Percentage of upstream region is:%.02f" % upstreamPercentage, "%")
            
        #-----------------------------------------------------------------------    
            
        # (6) Find Direct Repeats, their location, and percentage of upstream sequence     
            
            print("\n","="*50)
            print("\n\tSearching for Direct Repeats (DR)\n") 
            print("="*50,"\n")
            
            """
             ===================================================================

             Direct repeats: total length 4 to 12 bp where the first half of 
                             the nucleotides are the same as the second half, 
                             e.g.: GCGC is a DR of total length = 4bp; 
                             AAATTCAAATTC is a DR of total length = 12 bp

             REGEX patterns used: ([ATCG]{2,6})\1  

             =================================================================== 
   
            """
            
            
            
            findDirectRepeats(upstreamSequence) 
            
            
        
        #-----------------------------------------------------------------------    
                
        # (7) Find Mirror Repeats, their location, and percentage of upstream sequence            
            
            print("\n","="*50)
            print("\n\tSearching for Mirror Repeats (MR)\n") 
            print("="*50,"\n")                        
            
            """
            =================================================================== 

            Mirror repeats:  total length 6 bp where the first three
                             nucleotides are "mirrored" by the last 
                             three nucleotides, e.g.:   ACGGCA

            REGEX patterns used: (.)(.)(.)\3\2\1 

            ===================================================================

            """
            
            findMirrorRepeats(upstreamSequence)
            
        
        #-----------------------------------------------------------------------    
                    
        # (8) Find CAG repeats, their location, and percentage of upstream sequence        
        
            print("\n","="*50)
            print("\n\tSearching for CAG Repeats (CR) \n") 
            print("="*50,"\n")                                    
        
            """
            =================================================================== 

            CAG repeats: total length of at least 6bp where CAG is repeated,
                         e.g.: CAGCAGCAG is a CAG repeat of total length = 9bp  


            REGEX patterns used: (CAG)\1+ 

 
            ===================================================================

            """
            
            findCAGrepeats(upstreamSequence)
        
        
        
        
        
        
        
        #-----------------------------------------------------------------------
        
        else:
            print("No upstream region to analyze")
        

    else:
        print("No TATA box found.")




    


main()