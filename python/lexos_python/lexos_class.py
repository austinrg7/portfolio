""" Written in python2 """

import StringIO
from copy import deepcopy
from math import sqrt, log, exp
import shutil
import zipfile
import re
import os
from os.path import join as pathjoin
from os import makedirs, remove
import textwrap
import chardet

import numpy as np

from flask import request, send_file
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from helpers.general_functions import matrixtodict
from analyze.topword import testall, groupdivision, testgroup, KWtest

import prepare.scrubber as scrubber
import prepare.cutter as cutter
import helpers.general_functions as general_functions
import helpers.session_functions as session_functions
import helpers.constants as constants
import analyze.dendrogrammer as dendrogrammer
import analyze.rw_analyzer as rw_analyzer
import analyze.multicloud_topic as multicloud_topic
import analyze.KMeans as KMeans
import analyze.similarity as similarity
import analyze.information as information

"""
FileManager:

Description:
    Class for an object to hold all information about a user's files and choices throughout Lexos.
    Each user will have their own unique instance of the FileManager.

Major data attributes:
files:  A dictionary holding the LexosFile objects, each representing an uploaded file to be
        used in Lexos. The key for the dictionary is the unique ID of the file, with the value
        being the corresponding LexosFile object.
"""


class FileManager:
    def __init__(self):
        """ Constructor:
        Creates an empty file manager.

        Args:
            None

        Returns:
            FileManager object with no files.
        """
        self.files = {}
        self.nextID = 0

        makedirs(pathjoin(session_functions.session_folder(), constants.FILECONTENTS_FOLDER))

    def addFile(self, originalFilename, fileName, fileString):
        """
        Adds a file to the FileManager, identifying the new file with the next ID to be used.

        Args:
            fileName: The original filename of the uploaded file.
            fileString: The string contents of the text.

        Returns:
            The id of the newly added file.
        """
        # solve the problem that there is file with the same name
        ExistCloneFile = True
        while ExistCloneFile:
            ExistCloneFile = False
            for file in self.files.values():
                if file.name == fileName:
                    fileName = 'copy of ' + fileName
                    ExistCloneFile = True
                    break

        newFile = LexosFile(originalFilename, fileName, fileString, self.nextID)

        self.files[newFile.id] = newFile

        self.nextID += 1

        return newFile.id

    def deleteFiles(self, IDs):
        """
        delete all the file that has id in IDs
        :param IDs: an array contain all the id of the file need to be deleted
        """
        for id in IDs:
            id = int(id)  # in case that the id is not int
            self.files[id].cleanAndDelete()
            del self.files[id]  # Delete the entry

    def getActiveFiles(self):
        """
        Creates a list of all the active files in FileManager.

        Args:
            None

        Returns:
            A list of LexosFile objects.
        """
        activeFiles = []

        for lFile in self.files.values():
            if lFile.active:
                activeFiles.append(lFile)

        return activeFiles

    def deleteActiveFiles(self):
        """
        Deletes every active file by calling the delete method on the LexosFile object before removing it
        from the dictionary.

        Args:
            None.

        Returns:
            None.
        """
        for fileID, lFile in self.files.items():
            if lFile.active:
                lFile.cleanAndDelete()
                del self.files[fileID]  # Delete the entry

    def disableAll(self):
        """
        Disables every file in the file manager.

        Args:
            None

        Returns:
            None
        """
        for lFile in self.files.values():
            lFile.disable()

    def enableAll(self):
        """
        Enables every file in the file manager.

        Args:
            None

        Returns:
            None
        """
        for lFile in self.files.values():
            lFile.enable()

    def getPreviewsOfActive(self):
        """
        Creates a formatted list of previews from every active file in the file manager.

        Args:
            None

        Returns:
            A formatted list with an entry (tuple) for every active file, containing the preview information.
        """
        previews = []

        for lFile in self.files.values():
            if lFile.active:
                previews.append((lFile.id, lFile.name, lFile.classLabel, lFile.getPreview()))

        return previews

    def getPreviewsOfInactive(self):
        """
        Creates a formatted list of previews from every inactive file in the file manager.

        Args:
            None

        Returns:
            A formatted list with an entry (tuple) for every inactive file, containing the preview information.
        """
        previews = []

        for lFile in self.files.values():
            if not lFile.active:
                previews.append((lFile.id, lFile.name, lFile.classLabel, lFile.getPreview()))

        return previews

    def toggleFile(self, fileID):
        """
        Toggles the active status of the given file.

        Args:
            fileID: The id of the file to be toggled.

        Returns:
            None
        """

        lFile = self.files[fileID]

        if lFile.active:
            lFile.disable()
        else:
            lFile.enable()

    def classifyActiveFiles(self):
        """
        Applies a given class label (contained in the request.data) to every active file.

        Args:
            None

        Returns:
            None
        """
        classLabel = request.data

        for lFile in self.files.values():
            if lFile.active:
                lFile.setClassLabel(classLabel)

    def addUploadFile(self, File, fileName):
        # detect (and apply) the encoding type of the file's contents
        # since chardet runs slow, initially detect (only) first 500 chars;
        # if that fails, chardet entire file for a fuller test
        try:
            encodingDetect = chardet.detect(
                File[:constants.MIN_ENCODING_DETECT])  # Detect the encoding from the first 500 characters
            encodingType = encodingDetect['encoding']

            fileString = File.decode(
                encodingType)  # Grab the file contents, which were encoded/decoded automatically into python's format
        except:
            encodingDetect = chardet.detect(File)  # :( ... ok, detect the encoding from entire file
            encodingType = encodingDetect['encoding']

            fileString = File.decode(
                encodingType)  # Grab the file contents, which were encoded/decoded automatically into python's format

        #checking for /r in Windows files

        if '\r' in fileString[:constants.MIN_NEWLINE_DETECT]:
            fileString = fileString.replace('\r', '')

        self.addFile(fileName, fileName, fileString)  # Add the file to the FileManager

    def handleUploadWorkSpace(self):
        """
        this function take care of the session when you upload a .lexos file

        """
        # save .lexos file
        savePath = os.path.join(constants.UPLOAD_FOLDER, constants.WORKSPACE_DIR)
        savefile = os.path.join(savePath, str(self.nextID) + '.zip')
        try:
            os.makedirs(savePath)
        except:
            pass
        f = open(savefile, 'wb')
        f.write(request.data)
        f.close()

        # clean the session folder
        shutil.rmtree(session_functions.session_folder())

        # extract the zip
        with zipfile.ZipFile(savefile) as zf:
            zf.extractall(savePath)
        NewSessionPath = os.path.join(savePath, constants.WORKSPACE_UPLOAD_DIR)
        general_functions.copydir(NewSessionPath, session_functions.session_folder())

        # remove temp
        os.remove(savefile)
        shutil.rmtree(savePath)

    def updateWorkspace(self):
        """

        update the file to the new path when upload a workspace
        """
        # update the savepath of each file
        for lFile in self.files.values():
            lFile.savePath = pathjoin(session_functions.session_folder(), constants.FILECONTENTS_FOLDER,
                                      str(lFile.id) + '.txt')
        # update the session
        session_functions.loadSession()

    def scrubFiles(self, savingChanges):
        """
        Scrubs the active files, and creates a formatted preview list with the results.

        Args:
            savingChanges: A boolean saying whether or not to save the changes made.

        Returns:
            A formatted list with an entry (tuple) for every active file, containing the preview information.
        """
        previews = []

        for lFile in self.files.values():
            if lFile.active:
                previews.append((lFile.id, lFile.label, lFile.classLabel, lFile.scrubContents(savingChanges)))

        return previews

    def cutFiles(self, savingChanges):
        """
        Cuts the active files, and creates a formatted preview list with the results.

        Args:
            savingChanges: A boolean saying whether or not to save the changes made.

        Returns:
            A formatted list with an entry (tuple) for every active file, containing the preview information.
        """
        activeFiles = []
        for lFile in self.files.values():
            if lFile.active:
                activeFiles.append(lFile)

        previews = []
        for lFile in activeFiles:
            lFile.active = False

            childrenFileContents = lFile.cutContents()

            if savingChanges:
                for i, fileString in enumerate(childrenFileContents):
                    originalFilename = lFile.name
                    fileID = self.addFile(originalFilename, lFile.label + '_' + str(i + 1) + '.txt', fileString)

                    self.files[fileID].setScrubOptionsFrom(parent=lFile)
                    self.files[fileID].saveCutOptions(parentID=lFile.id)

            else:
                cutPreview = []
                for i, fileString in enumerate(childrenFileContents):
                    cutPreview.append(('Chunk ' + str(i + 1), general_functions.makePreviewFrom(fileString)))

                previews.append((lFile.id, lFile.label, lFile.classLabel, cutPreview))

        if savingChanges:
            previews = self.getPreviewsOfActive()

        return previews

    def zipActiveFiles(self, fileName):
        """
        Sends a zip file containing files containing the contents of the active files.

        Args:
            fileName: Name to assign to the zipped file.

        Returns:
            Zipped archive to send to the user, created with Flask's send_file.
        """
        zipstream = StringIO.StringIO()
        zfile = zipfile.ZipFile(file=zipstream, mode='w')
        for lFile in self.files.values():
            if lFile.active:
                zfile.write(lFile.savePath, arcname=lFile.name, compress_type=zipfile.ZIP_STORED)
        zfile.close()
        zipstream.seek(0)

        return send_file(zipstream, attachment_filename=fileName, as_attachment=True)

    def zipWorkSpace(self):
        """
        Sends a zip file containing a pickle file of the session and the session folder.

        Args:
            fileName: Name to assign to the zipped file.

        Returns:
            the path of the zipped workspace
        """
        # initialize the save path
        savepath = os.path.join(constants.UPLOAD_FOLDER, constants.WORKSPACE_DIR)
        id = str(self.nextID % 10000)  # take the last 4 digit
        workspacefilepath = os.path.join(constants.UPLOAD_FOLDER, id + '_' + constants.WORKSPACE_FILENAME)
        print 'path'

        # move session folder to work space folder
        try:
            os.remove(workspacefilepath)
        except:
            pass
        try:
            shutil.rmtree(savepath)
        except:
            pass
        general_functions.copydir(session_functions.session_folder(), savepath)
        print 'copy'

        # save session in the work space folder
        session_functions.saveSession(savepath)
        print 'save'

        # zip the dir
        print 'ziping'
        zipf = zipfile.ZipFile(workspacefilepath, 'w')
        print 'zip object creat'
        general_functions.zipdir(savepath, zipf)
        print 'ziped'
        zipf.close()
        print 'zip'
        # remove the original dir
        shutil.rmtree(savepath)

        return workspacefilepath

    def checkActivesTags(self):
        """
        Checks the tags of the active files for DOE/XML/HTML/SGML tags.

        Args:
            None

        Returns:
            Two booleans, the first signifying the presence of any type of tags, the secondKeyWord
            the presence of DOE tags.
        """
        foundTags = False
        foundDOE = False

        for lFile in self.files.values():
            if not lFile.active:
                continue  # with the looping, do not do the rest of current loop

            if lFile.type == 'doe':
                foundDOE = True
                foundTags = True
            if lFile.hasTags:
                foundTags = True

            if foundDOE and foundTags:
                break

        return foundTags, foundDOE

    def updateLabel(self, fileID, fileLabel):
        """
        Sets the file label of the file denoted by the given id to the supplied file label.

        Args:
            fileID: The id of the file for which to change the label.
            fileLabel: The label to set the file to.

        Returns:
            None
        """
        self.files[fileID] = fileLabel

    def getActiveLabels(self):
        """
        Gets the labels of all active files in a dictionary of { file_id: file_label }.

        Args:
            None

        Returns:
            Returns a dictionary of the currently active files' labels.
        """
        labels = {}
        for lFile in self.files.values():
            if lFile.active:
                labels[lFile.id] = lFile.label

        return labels

    def greyword(self, ResultMatrix, CountMatrix):
        """
        The help function used in GetMatrix method to remove less frequent word, or GreyWord(non-functioning word).
        This function takes in 2 word count matrix(one of them may be in proportion) and calculate the boundary of the
        low frequency word with the following function:
            round(sqrt(log(Total * log(Max) / log(Total + 1) ** 2 + exp(1))))
            * log is nature log, sqrt is the square root, round is round to the nearest integer
            * Max is the word count of the most frequent word in the Chunk
            * Total is the total word count of the chunk
        Mathematical property:
            * the data is sensitive to Max when it is small (because Max tend to be smaller than Total)
            * the function return 1 when Total and Max approaches 0
            * the function return infinity when Total and Max approaches infinity
            * the function is a increasing function with regard to Max or total

        all the word with lower word count than the boundary of that Chunk will be a low frequency word
        if a word is a low frequency word in all the chunks, this will be deemed as non-functioning word(GreyWord) and deleted

        :param ResultMatrix: a matrix with header in 0 row and 0 column
                            it row represent chunk and the column represent word
                            it contain the word count (might be proportion depend on :param useFreq in function gerMatix())
                                of a particular word in a particular chunk

        :param CountMatrix: it row represent chunk and the column represent word
                            it contain the word count (might be proportion depend on :param useFreq in function gerMatix())
                                of a particular word in a particular chunk

        :return: a matrix with header in 0 row and 0 column
                it row represent chunk and the column represent word
                it contain the word count (might be proportion depend on :param useFreq in function gerMatix())
                    of a particular word in a particular chunk
                this matrix do not contain GreyWord
        """

        # find boundary
        Bondaries = []  # the low frequency word boundary of each chunk
        for i in range(len(CountMatrix)):
            Max = max(CountMatrix[i])
            Total = sum(CountMatrix[i])
            Bondary = round(
                sqrt(log(Total * log(Max + 1) / log(Total + 1) ** 2 + exp(1))))  # calculate the Boundary of each file
            Bondaries.append(Bondary)

        # find low frequency word
        for i in range(len(CountMatrix[0])):  # focusing on the columns
            AllBelowBoundary = True
            for j in range(len(CountMatrix)):  # focusing on the rows
                if CountMatrix[j][i] > Bondaries[j]:
                    AllBelowBoundary = False
                    break
            if AllBelowBoundary:
                for j in range(len(CountMatrix)):
                    ResultMatrix[j + 1][i + 1] = 0
        return ResultMatrix

    def culling(self, ResultMatrix, CountMatrix):
        """
        This function is a help function of the getMatrix function.
        This function will delete(make count 0) all the word that appear in strictly less than Lowerbound number of document.
        (if the Lowerbound is 2, all the word only contain 1 document will be deleted)

        :param ResultMatrix: The Matrix that getMatrix() function need to return(might contain Prop, Count or weighted depend on user's choice)
        :param CountMatrix: The Matrix that only contain word count
        :param Lowerbound: the least number of chunk that a word need to be in in order to get kept in this function
        :return: a new ResultMatrix (might contain Prop, Count or weighted depend on user's choice)
        """
        Lowerbound = int(request.form['cullnumber'])

        for i in range(len(CountMatrix[0])):  # focusing on the column
            NumChunkContain = 0
            for j in range(len(CountMatrix)):
                if CountMatrix[j][i] != 0:
                    NumChunkContain += 1
            if NumChunkContain < Lowerbound:
                for j in range(len(CountMatrix)):
                    ResultMatrix[j + 1][i + 1] = 0
        return ResultMatrix

    def mostFrequentWord(self, ResultMatrix, CountMatrix):
        """
        This function is a help function of the getMatrix function.
        This function will rank all the word by word count(across all the chunks)
        Then delete(make count 0) all the words that has ranking lower than LowerRankBound (tie will be kept)
        * the return will not be sorted

        :param ResultMatrix: The Matrix that getMatrix() function need to return(might contain Porp, Count or weighted depend on user's choice)
        :param CountMatrix: The Matrix that only contain word count
        :param LowerRankBound: The lowest rank that this function will kept, ties will all be kept
        :return: a new ResultMatrix (might contain Prop, Count or weighted depend on user's choice)
        """
        LowerRankBound = int(request.form['mfwnumber'])

        # trap the error that if the LowerRankBound is larger than the number of unique word
        if LowerRankBound > len(CountMatrix[0]):
            LowerRankBound = len(CountMatrix[0])

        WordCounts = []
        for i in range(len(CountMatrix[0])):  # focusing on the column
            WordCounts.append(sum([CountMatrix[j][i] for j in range(len(CountMatrix))]))
        sortedWordCounts = sorted(WordCounts)

        Lowerbound = sortedWordCounts[len(CountMatrix[0]) - LowerRankBound]

        for i in range(len(CountMatrix[0])):
            if WordCounts[i] < Lowerbound:
                for j in range(len(CountMatrix)):
                    ResultMatrix[j + 1][i + 1] = 0

        return ResultMatrix

    def getMatrixOptions(self):
        """
        Gets all the options that are used to generate the matrices from GUI

        Args:
            None

        Returns:
            useWordTokens: A boolean: True if 'word' tokens; False if 'char' tokens
            useTfidf: A boolean: True if the user wants to use "TF/IDF" (weighted counts) to normalize
            normOption: A string representing distance metric options: only applicable to "TF/IDF", otherwise "N/A"
            onlyCharGramWithinWords: True if 'char' tokens but only want to count tokens "inside" words
            ngramSize: int for size of ngram (either n-words or n-chars, depending on useWordTokens)
            useFreq: A boolean saying whether or not to use the frequency (count / total), as opposed to the raw counts, for the count data.
            greyWord: A boolean (default is False): True if the user wants to use greyword to normalize
            MostFrequenWord: a boolean to show whether to apply MostFrequentWord to the Matrix (see self.mostFrequenWord method for more)
            Culling: a boolean the a boolean to show whether to apply Culling to the Matrix (see self.culling method for more)
        """
        ngramSize = int(request.form['tokenSize'])
        useWordTokens = request.form['tokenType'] == 'word'
        try:
            useFreq = request.form['normalizeType'] == 'freq'

            useTfidf = request.form['normalizeType'] == 'tfidf'  # if use TF/IDF
            normOption = "N/A"  # only applicable when using "TF/IDF", set default value to N/A
            if useTfidf:
                if request.form['norm'] == 'l1':
                    normOption = u'l1'
                elif request.form['norm'] == 'l2':
                    normOption = u'l2'
                else:
                    normOption = None
        except:
            useFreq = useTfidf = False
            normOption = None

        onlyCharGramsWithinWords = False
        if not useWordTokens:  # if using character-grams
            if 'inWordsOnly' in request.form:
                onlyCharGramsWithinWords = request.form['inWordsOnly'] == 'on'

        greyWord = 'greyword' in request.form
        MostFrequenWord = 'mfwcheckbox' in request.form
        Culling = 'cullcheckbox' in request.form

        showDeletedWord = False
        if 'greyword' or 'mfwcheckbox' or 'cullcheckbox' in request.form:
            if 'onlygreyword' in request.form:
                showDeletedWord = True

        return ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showDeletedWord, onlyCharGramsWithinWords, MostFrequenWord, Culling

    def getMatrix(self, useWordTokens, useTfidf, normOption, onlyCharGramsWithinWords, ngramSize, useFreq, showGreyWord,
                  greyWord, MFW, cull, roundDecimal=False):
        """
        Gets a matrix properly formatted for output to a CSV file, with labels along the top and side
        for the words and files. Uses scikit-learn's CountVectorizer class

        Args:
            useWordTokens: A boolean: True if 'word' tokens; False if 'char' tokens
            useTfidf: A boolean: True if the user wants to use "TF/IDF" (weighted counts) to normalize
            normOption: A string representing distance metric options: only applicable to "TF/IDF", otherwise "N/A"
            onlyCharGramWithinWords: True if 'char' tokens but only want to count tokens "inside" words
            ngramSize: int for size of ngram (either n-words or n-chars, depending on useWordTokens)
            useFreq: A boolean saying whether or not to use the frequency (count / total), as opposed to the raw counts, for the count data.
            greyWord: A boolean (default is False): True if the user wants to use greyword to normalize
            MFW: a boolean to show whether to apply MostFrequentWord to the Matrix (see self.mostFrequenWord() method for more)
            cull: a boolean to show whether to apply culling to the Matrix (see self.culling() method for more)
            roundDecimal: A boolean (default is False): True if the float is fixed to 6 decimal places

        Returns:
            Returns the sparse matrix and a list of lists representing the matrix of data.
        """

        allContents = []  # list of strings-of-text for each segment
        tempLabels = []  # list of labels for each segment
        for lFile in self.files.values():
            if lFile.active:
                contentElement = lFile.loadContents()
                # contentElement = ''.join(contentElement.splitlines()) # take out newlines
                allContents.append(contentElement)

                if request.form["file_" + str(lFile.id)] == lFile.label:
                    tempLabels.append(lFile.label.encode("utf-8"))
                else:
                    newLabel = request.form["file_" + str(lFile.id)].encode("utf-8")
                    tempLabels.append(newLabel)

        if useWordTokens:
            tokenType = u'word'
        else:
            tokenType = u'char'
            if onlyCharGramsWithinWords:
                tokenType = u'char_wb'

        # heavy hitting tokenization and counting options set here

        # CountVectorizer can do 
        #       (a) preprocessing (but we don't need that); 
        #       (b) tokenization: analyzer=['word', 'char', or 'char_wb'; Note: char_wb does not span 
        #                         across two words, but *will* include whitespace at start/end of ngrams)]
        #                         token_pattern (only for analyzer='word')
        #                         ngram_range (presuming this works for both word and char??)
        #       (c) culling:      min_df..max_df (keep if term occurs in at least these documents)
        #                         stop_words 
        #       Note:  dtype=float sets type of resulting matrix of values; need float in case we use proportions

        # for example:
        # word 1-grams ['content' means use strings of text, analyzer='word' means features are "words";
        #                min_df=1 means include word if it appears in at least one doc, the default;
        #                if tokenType=='word', token_pattern used to include single letter words (default is two letter words)

        # \b[\w\']+\b: means tokenize on a word boundary but do not split up possessives (joe's) nor contractions (i'll)
        CountVector = CountVectorizer(input=u'content', encoding=u'utf-8', min_df=1,
                                      analyzer=tokenType, token_pattern=ur'(?u)\b[\w\']+\b',
                                      ngram_range=(ngramSize, ngramSize),
                                      stop_words=[], dtype=float, max_df=1.0)

        # make a (sparse) Document-Term-Matrix (DTM) to hold all counts
        DocTermSparseMatrix = CountVector.fit_transform(allContents)
        RawCountMatrix = DocTermSparseMatrix.toarray()

        """Parameters TfidfTransformer (TF/IDF)"""
        # Note: by default, idf use natural log
        #
        # (a) norm: 'l1', 'l2' or None, optional
        #            {USED AS THE LAST STEP: after getting the result of tf*idf, normalize the vector (row-wise) into unit vector}
        #           'l1': Taxicab / Manhattan distance (p=1)
        #                 [ ||u|| = |u1| + |u2| + |u3| ... ]
        #           'l2': Euclidean norm (p=2), the most common norm; typically called "magnitude"
        #                 [ ||u|| = sqrt( (u1)^2 + (u2)^2 + (u3)^2 + ... )]
        #            *** user can choose the normalization method ***
        #
        # (b) use_idf: boolean, optional ; "Enable inverse-document-frequency reweighting."
        #              which means: True if you want to use idf (times idf)
        #                           False if you don't want to use idf at all, the result is only term-frequency
        #              *** we choose True here because the user has already chosen TF/IDF, instead of raw counts ***
        #
        # (c) smooth_idf: boolean, optional; "Smooth idf weights by adding one to document frequencies, as if an extra 
        #                 document was seen containing every term in the collection exactly once. Prevents zero divisions.""
        #                 if True,  idf = log( float(number of doc in total) / number of doc where term t appears ) + 1
        #                 if False, idf = log( float(number of doc in total + 1) / (number of doc where term t appears + 1) ) + 1
        #                 *** we choose False, because denominator never equals 0 in our case, no need to prevent zero divisions ***
        # 
        # (d) sublinear_tf: boolean, optional ; "Apply sublinear tf scaling"
        #                   if True,  tf = 1 + log(tf) (log here is base 10)
        #                   if False, tf = term-frequency
        #                   *** we choose False as the normal term-frequency ***

        if useTfidf:  # if use TF/IDF
            transformer = TfidfTransformer(norm=normOption, use_idf=True, smooth_idf=False, sublinear_tf=False)
            DocTermSparseMatrix = transformer.fit_transform(DocTermSparseMatrix)

        # elif use Proportional Counts
        elif useFreq:  # we need token totals per file-segment
            totals = DocTermSparseMatrix.sum(1)
            # make new list (of sum of token-counts in this file-segment) 
            allTotals = [totals[i, 0] for i in range(len(totals))]
        # else:
        #   use Raw Counts

        # need to get at the entire matrix and not sparse matrix
        matrix = DocTermSparseMatrix.toarray()

        # snag all features (e.g., word-grams or char-grams) that were counted
        allFeatures = CountVector.get_feature_names()

        # build countMatrix[rows: fileNames, columns: words]
        countMatrix = [[''] + allFeatures]
        for i, row in enumerate(matrix):
            newRow = []
            newRow.append(tempLabels[i])
            for j, col in enumerate(row):
                if not useFreq:  # use raw counts OR TF/IDF counts
                    # if normalize != 'useFreq': # use raw counts or tf-idf
                    newRow.append(col)
                else:  # use proportion within file
                    newProp = float(col) / allTotals[i]
                    if roundDecimal:
                        newProp = round(newProp, 4)
                    newRow.append(newProp)
            # end each column in matrix
            countMatrix.append(newRow)
        # end each row in matrix

        # encode the Feature and Label into UTF-8
        for i in xrange(len(countMatrix)):
            row = countMatrix[i]
            for j in xrange(len(row)):
                element = countMatrix[i][j]
                if isinstance(element, unicode):
                    countMatrix[i][j] = element.encode('utf-8')

        # grey word
        if greyWord:
            countMatrix = self.greyword(ResultMatrix=countMatrix, CountMatrix=RawCountMatrix)

        # culling
        if cull:
            countMatrix = self.culling(ResultMatrix=countMatrix, CountMatrix=RawCountMatrix)

        # Most Frequent Word
        if MFW:
            countMatrix = self.mostFrequentWord(ResultMatrix=countMatrix, CountMatrix=RawCountMatrix)

        return countMatrix

    def generateCSVMatrix(self, roundDecimal=False):
        """
        Gets a matrix properly formatted for output to a CSV file and also a table displaying on the Tokenizer page, with labels along the top and side
        for the words and files. Generates matrices by calling getMatrix()

        Args:
            roundDecimal: A boolean (default is False): True if the float is fixed to 6 decimal places

        Returns:
            Returns the sparse matrix and a list of lists representing the matrix of data.
        """
        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showDeleted, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()
        transpose = request.form['csvorientation'] == 'filecolumn'

        countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
                                                          normOption=normOption,
                                                          onlyCharGramsWithinWords=onlyCharGramsWithinWords,
                                                          ngramSize=ngramSize, useFreq=useFreq,
                                                          roundDecimal=roundDecimal, greyWord=greyWord,
                                                          showGreyWord=showDeleted, MFW=MFW, cull=culling)

        NewCountMatrix = countMatrix

        # -- begin taking care of the Deleted word Option --
        if greyWord or MFW or culling:
            if showDeleted:
                # append only the word that are 0s
                BackupCountMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
                                                          normOption=normOption,
                                                          onlyCharGramsWithinWords=onlyCharGramsWithinWords,
                                                          ngramSize=ngramSize, useFreq=useFreq,
                                                          roundDecimal=roundDecimal, greyWord=False,
                                                          showGreyWord=showDeleted, MFW=False, cull=False)
                NewCountMatrix = []

                for row in countMatrix:  # append the header for the file
                    NewCountMatrix.append([row[0]])

                # to test if that row is all 0 (if it is all 0 means that row is deleted)
                for i in range(1, len(countMatrix[0])):
                    AllZero = True
                    for j in range(1, len(countMatrix)):
                        if countMatrix[j][i] != 0:
                            AllZero = False
                            break
                    if AllZero:
                        for j in range(len(countMatrix)):
                            NewCountMatrix[j].append(BackupCountMatrix[j][i])
            else:
                # delete the column with all 0
                NewCountMatrix = [[]] * len(countMatrix)  # initialize the NewCountMatrix

                # see if the row is deleted
                for i in range(len(countMatrix[0])):
                    AllZero = True
                    for j in range(1, len(countMatrix)):
                        if countMatrix[j][i] != 0:
                            AllZero = False
                            break
                    # if that row is not all 0 (not deleted then append)
                    if not AllZero:
                        for j in range(len(countMatrix)):
                            NewCountMatrix[j].append(countMatrix[j][i])
        # -- end taking care of the GreyWord Option --

        if transpose:
            NewCountMatrix = zip(*NewCountMatrix)

        return NewCountMatrix

    def generateTokenizeResults(self):
        countMatrix = self.generateCSVMatrix(roundDecimal=True)

        # Calculate the sum of a row and add a new column "Total" at the end
        dtm = []
        for row in xrange(1, len(countMatrix)):
            rowList = list(countMatrix[row])
            rowList.append(round(sum(rowList[1:]), 6))
            dtm.append(rowList)

        # Add titles of the matrix into a list
        matrixTitle = list(countMatrix[0])
        matrixTitle[0] = "Token"
        matrixTitle[0] = matrixTitle[0].encode("utf-8")
        matrixTitle.append("Row Total")

        # Server-side process the matrix and make an HTML Unicode string for injection
        titleStr = u'<tbody>'
        # Make a row list to store each row of matrix within HTML tags
        rowList = []
        newAppendRow = rowList.extend
        # Iterate through the matrix to extend rows
        for row in dtm:
            # Make a cell list to store each cell of a matrix row within HTML tags
            cellList = [u'<tr>']
            newAppendCell = cellList.append
            # Iterate through each matrix row to append cell
            for data in row:
                newAppendCell(u'<td>%s</td>' % (str(data).decode('utf-8')))
            newAppendCell(u'</tr>')
            # Extend cellList into rowList
            newAppendRow(cellList)
        newAppendRow(u'</tbody>')
        # Turn a list into a string with HTML tags
        tableStr = titleStr + u''.join(rowList)

        return matrixTitle, tableStr


    def generateCSV(self):
        """
        Generates a CSV file from the active files.

        Args:
            None

        Returns:
            The filepath where the CSV was saved, and the chosen extension (.csv or .tsv) for the file.
        """
        transpose = request.form['csvorientation'] == 'filerow'
        useTSV = request.form['csvdelimiter'] == 'tab'
        extension = '.tsv' if useTSV else '.csv'

        countMatrix = self.generateCSVMatrix()

        delimiter = '\t' if useTSV else ','

        # replace newlines and tabs with space to avoid messing output sheet format
        countMatrix[0] = [item.replace('\t', ' ') for item in countMatrix[0]]
        countMatrix[0] = [item.replace('\n', ' ') for item in countMatrix[0]]

        # replace comma with Chinese comma to avoid messing format for .csv output file
        if delimiter == ',':
            newComma = u'\uFF0C'.encode('utf-8')
            countMatrix[0] = [item.replace(',', newComma) for item in countMatrix[0]]

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)
        outFilePath = pathjoin(folderPath, 'results' + extension)

        classLabelList = ["Class Label"]
        for lFile in self.files.values():
            if lFile.active:
                classLabelList.append(lFile.classLabel)

        with open(outFilePath, 'w') as outFile:
            for i, row in enumerate(countMatrix):
                rowStr = delimiter.join([str(x) for x in row])
                if transpose:
                    rowStr += delimiter + classLabelList[i]

                outFile.write(rowStr + '\n')

            if not transpose:
                outFile.write(delimiter.join(classLabelList) + '\n')
        outFile.close()

        return outFilePath, extension

    def generateStatistics(self):
        """
        the function calls analyze/information to get the information about each file and the whole corpus

        :return:
        FileInfoList: a list contain a tuple contain the file id and the file information
                        (see analyze/information.py/Corpus_Information.returnstatistics() function for more)
        corpusInformation: the statistics information about the whole corpus
                        (see analyze/information.py/File_Information.returnstatistics() function for more)
        """
        FileInfoList = []
        folderpath = os.path.join(session_functions.session_folder(),
                                  constants.RESULTS_FOLDER)  # folder path for storing
        # graphs and plots
        try:
            os.mkdir(folderpath)  # attempt to make folder to store graphs/plots
        except:
            pass

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showDeleted, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
                                            normOption=normOption,
                                            onlyCharGramsWithinWords=onlyCharGramsWithinWords,
                                            ngramSize=ngramSize, useFreq=useFreq, greyWord=greyWord,
                                            showGreyWord=showDeleted, MFW=MFW, cull=culling)
        WordLists = general_functions.matrixtodict(countMatrix)
        Files = [file for file in self.getActiveFiles()]
        for i in range(len(Files)):
            fileinformation = information.File_Information(WordLists[i], Files[i].name)
            FileInfoList.append((Files[i].id, fileinformation.returnstatistics()))
            try:
                fileinformation.plot(os.path.join(folderpath, str(Files[i].id) + constants.FILE_INFORMATION_FIGNAME))
            except:
                pass

        corpusInformation = information.Corpus_Information(WordLists, Files)  # make a new object called corpus
        corpusInfoDict = corpusInformation.returnstatistics()
        try:
            corpusInformation.plot(os.path.join(folderpath, constants.CORPUS_INFORMATION_FIGNAME))
        except:
            pass
        return FileInfoList, corpusInfoDict

    def getDendrogramLegend(self, distanceList):
        """
        Generates the legend for the dendrogram from the active files.

        Args:
            None

        Returns:
            A string with all the formatted information of the legend.
        """
        strFinalLegend = ""

        # ----- DENDROGRAM OPTIONS -----
        strLegend = "Dendrogram Options - "

        needTranslate, translateMetric, translateDVF = dendrogrammer.translateDenOptions()

        if needTranslate == True:
            strLegend += "Distance Metric: " + translateMetric + ", "
            strLegend += "Linkage Method: " + request.form['linkage'] + ", "
            strLegend += "Data Values Format: " + translateDVF + "\n\n"
        else:
            strLegend += "Distance Metric: " + request.form['metric'] + ", "
            strLegend += "Linkage Method: " + request.form['linkage'] + ", "
            strLegend += "Data Values Format: " + request.form['normalizeType'] + " (Norm: " + request.form[
                'norm'] + ")\n\n"

        strWrappedDendroOptions = textwrap.fill(strLegend, constants.CHARACTERS_PER_LINE_IN_LEGEND)
        # -------- end DENDROGRAM OPTIONS ----------

        strFinalLegend += strWrappedDendroOptions + "\n\n"

        distances = ', '.join(str(x) for x in distanceList)
        distancesLegend = "Dendrogram Distances - " + distances
        strWrappedDistancesLegend = textwrap.fill(distancesLegend, (constants.CHARACTERS_PER_LINE_IN_LEGEND - 6))

        strFinalLegend += strWrappedDistancesLegend + "\n\n"

        for lexosFile in self.files.values():
            if lexosFile.active:
                strFinalLegend += lexosFile.getLegend() + "\n\n"

        return strFinalLegend

    def generateDendrogram(self):
        """
        Generates dendrogram image and pdf from the active files.

        Args:
            None

        Returns:
            Total number of PDF pages, ready to calculate the height of the embedded PDF on screen
        """

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showGreyWord, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
                                                          normOption=normOption,
                                                          onlyCharGramsWithinWords=onlyCharGramsWithinWords,
                                                          ngramSize=ngramSize, useFreq=useFreq, greyWord=greyWord,
                                                          showGreyWord=showGreyWord, MFW=MFW, cull=culling)

        # Gets options from request.form and uses options to generate the dendrogram (with the legends) in a PDF file
        orientation = str(request.form['orientation'])
        title = request.form['title']
        pruning = request.form['pruning']
        pruning = int(request.form['pruning']) if pruning else 0
        linkage = str(request.form['linkage'])
        metric = str(request.form['metric'])

        augmentedDendrogram = False
        if 'augmented' in request.form:
            augmentedDendrogram = request.form['augmented'] == 'on'

        showDendroLegends = False
        if 'dendroLegends' in request.form:
            showDendroLegends = request.form['dendroLegends'] == 'on'

        dendroMatrix = []
        fileNumber = len(countMatrix)
        totalWords = len(countMatrix[0])

        for row in range(1, fileNumber):
            wordCount = []
            for col in range(1, totalWords):
                wordCount.append(countMatrix[row][col])
            dendroMatrix.append(wordCount)

        distanceList = dendrogrammer.getDendroDistances(linkage, metric, dendroMatrix)

        legend = self.getDendrogramLegend(distanceList)

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)

        # we need labels (segment names)
        tempLabels = []
        for matrixRow in countMatrix:
            tempLabels.append(matrixRow[0])

        pdfPageNumber = dendrogrammer.dendrogram(orientation, title, pruning, linkage, metric, tempLabels, dendroMatrix,
                                                 legend, folderPath, augmentedDendrogram, showDendroLegends)
        return pdfPageNumber

    def generateKMeansPCA(self):
        """
        Generates a table of cluster_number and file name from the active files.

        Args:
            None

        Returns:
            kmeansIndex.tolist(): a list of index of the closest center of the file
            silttScore: a float of silhouette score based on KMeans algorithm
            fileNameStr: a string of file names, separated by '#'
            KValue: an int of the number of K from input
        """

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showGreyWord, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        # countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
        #                                                   normOption=normOption,
        #                                                   onlyCharGramsWithinWords=onlyCharGramsWithinWords,
        #                                                   ngramSize=ngramSize, useFreq=useFreq, greyWord=greyWord,
        #                                                   showGreyWord=showGreyWord, MFW=MFW, cull=culling, docTermSparseMatrixNeeded=True)

        countMatrix= self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,normOption=normOption,onlyCharGramsWithinWords=onlyCharGramsWithinWords,ngramSize=ngramSize, useFreq=False, greyWord=greyWord,showGreyWord=showGreyWord, MFW=MFW, cull=culling)

        del countMatrix[0]
        for row in countMatrix:
            del row[0]

        matrix= np.array(countMatrix)

        # Gets options from request.form and uses options to generate the K-mean results
        KValue = len(self.getActiveFiles()) / 2  # default K value
        max_iter = 300  # default number of iterations
        initMethod = request.form['init']
        n_init = 300
        tolerance = 1e-4

        if (request.form['nclusters'] != '') and (int(request.form['nclusters']) != KValue):
            KValue = int(request.form['nclusters'])
        if (request.form['max_iter'] != '') and (int(request.form['max_iter']) != max_iter):
            max_iter = int(request.form['max_iter'])
        if request.form['n_init'] != '':
            n_init = int(request.form['n_init'])
        if request.form['tolerance'] != '':
            tolerance = float(request.form['tolerance'])

        metric_dist = request.form['KMeans_metric']

        fileNameList = []
        for lFile in self.files.values():
            if lFile.active:
                if request.form["file_" + str(lFile.id)] == lFile.label:
                    fileNameList.append(lFile.label.encode("utf-8"))
                else:
                    newLabel = request.form["file_" + str(lFile.id)].encode("utf-8")
                    fileNameList.append(newLabel)

        fileNameStr = fileNameList[0]

        for i in range(1, len(fileNameList)):
            fileNameStr += "#" + fileNameList[i]

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)

        kmeansIndex, silttScore, colorChart = KMeans.getKMeansPCA(matrix, KValue, max_iter,
                                                                  initMethod, n_init, tolerance, metric_dist,
                                                                  fileNameList, folderPath)

        return kmeansIndex, silttScore, fileNameStr, KValue, colorChart

    def generateKMeansVoronoi(self):
        """
        Generates a table of cluster_number and file name from the active files.

        Args:
            None

        Returns:
            kmeansIndex.tolist(): a list of index of the closest center of the file
            silttScore: a float of silhouette score based on KMeans algorithm
            fileNameStr: a string of file names, separated by '#' 
            KValue: an int of the number of K from input
        """

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showGreyWord, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        # countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,
        #                                                   normOption=normOption,
        #                                                   onlyCharGramsWithinWords=onlyCharGramsWithinWords,
        #                                                   ngramSize=ngramSize, useFreq=useFreq, greyWord=greyWord,
        #                                                   showGreyWord=showGreyWord, MFW=MFW, cull=culling, docTermSparseMatrixNeeded=True)

        countMatrix= self.getMatrix(useWordTokens=useWordTokens, useTfidf=useTfidf,normOption=normOption,onlyCharGramsWithinWords=onlyCharGramsWithinWords,ngramSize=ngramSize, useFreq=False, greyWord=greyWord,showGreyWord=showGreyWord, MFW=MFW, cull=culling)

        del countMatrix[0]
        for row in countMatrix:
            del row[0]

        matrix= np.array(countMatrix)
        
        # Gets options from request.form and uses options to generate the K-mean results
        KValue = len(self.getActiveFiles()) / 2  # default K value
        max_iter = 300  # default number of iterations
        initMethod = request.form['init']
        n_init = 300
        tolerance = 1e-4

        if (request.form['nclusters'] != '') and (int(request.form['nclusters']) != KValue):
            KValue = int(request.form['nclusters'])
        if (request.form['max_iter'] != '') and (int(request.form['max_iter']) != max_iter):
            max_iter = int(request.form['max_iter'])
        if request.form['n_init'] != '':
            n_init = int(request.form['n_init'])
        if request.form['tolerance'] != '':
            tolerance = float(request.form['tolerance'])

        metric_dist = request.form['KMeans_metric']

        fileNameList = []
        for lFile in self.files.values():
            if lFile.active:
                if request.form["file_" + str(lFile.id)] == lFile.label:
                    fileNameList.append(lFile.label.encode("utf-8"))
                else:
                    newLabel = request.form["file_" + str(lFile.id)].encode("utf-8")
                    fileNameList.append(newLabel)

        fileNameStr = fileNameList[0]

        for i in range(1, len(fileNameList)):
            fileNameStr += "#" + fileNameList[i]

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)

        kmeansIndex, silttScore, colorChart, finalPointsList, finalCentroidsList, textData, maxVal = KMeans.getKMeansVoronoi(
            matrix, KValue, max_iter, initMethod, n_init, tolerance, metric_dist, fileNameList)

        return kmeansIndex, silttScore, fileNameStr, KValue, colorChart, finalPointsList, finalCentroidsList, textData, maxVal

    def generateRWA(self):
        """
        Generates the data for the rolling window page.

        Args:
            None

        Returns:
            The data points, as a list of [x, y] points, the title for the graph, and the labels for the axes.
        """
        fileID = int(request.form['filetorollinganalyze'])  # file the user selected to use for generating the grpah
        fileString = self.files[fileID].loadContents()

        # user input option choices
        countType = request.form['counttype']  # rolling average or rolling ratio
        tokenType = request.form['inputtype']  # string, word, or regex
        windowType = request.form['windowtype']  # letter, word, or lines
        windowSize = request.form['rollingwindowsize']
        keyWord = request.form['rollingsearchword']
        secondKeyWord = request.form['rollingsearchwordopt']
        msWord = request.form['rollingmilestonetype']
        hasMileStones = 'rollinghasmilestone' in request.form
        #get data from RWanalyzer
        dataList, graphTitle, xAxisLabel, yAxisLabel = rw_analyzer.rw_analyze(fileString, countType, tokenType,
                                                                              windowType, keyWord, secondKeyWord,
                                                                              windowSize)

        # make graph legend labels
        keyWordList = keyWord.replace(",", ", ")
        keyWordList = keyWordList.split(", ")

        if countType == "ratio":
            keyWordList2 = secondKeyWord.replace(",", ", ")
            keyWordList2 = keyWordList2.split(", ")
            for i in xrange(len(keyWordList)):
                keyWordList[i] = keyWordList[i] + "/(" + keyWordList[i] + "+" + keyWordList2[i] + ")"

        legendLabelsList = []
        legendLabels = ""

        for i in xrange(len(keyWordList)):
            legendLabels = legendLabels + str(keyWordList[i].encode('utf-8') + "#")

        legendLabelsList.append(legendLabels)

        dataPoints = []  # makes array to hold simplified values

        # begin plot reduction alg
        for i in xrange(len(dataList)):  # repeats algorithm for each plotList in dataList
            lastDraw = 0  # last drawn elt = plotList[0]
            firstPoss = 1  # first possible point to plot
            nextPoss = 2  # next possible point to plot
            dataPoints.append([[lastDraw + 1, dataList[i][lastDraw]]])  # add lastDraw to list of points to be plotted
            while nextPoss < len(dataList[i]):  # while next point is not out of bounds
                mone = (dataList[i][lastDraw] - dataList[i][firstPoss]) / (
                    lastDraw - firstPoss)  # calculate the slope from last draw to firstposs
                mtwo = (dataList[i][lastDraw] - dataList[i][nextPoss]) / (
                    lastDraw - nextPoss)  # calculate the slope from last draw to nextposs
                if abs(mone - mtwo) > (0.0000000001):  # if the two slopes are not equal
                    dataPoints[i].append([firstPoss + 1, dataList[i][firstPoss]])  # plot first possible point to plot
                    lastDraw = firstPoss  # firstposs becomes last draw
                firstPoss = nextPoss  # nextpossible becomes firstpossible
                nextPoss += 1  # nextpossible increases by one
            dataPoints[i].append(
                [nextPoss, dataList[i][nextPoss - 1]])  # add the last point of the data set to the points to be plotted
        #end pot reduction

        if hasMileStones:  # if milestones checkbox is checked
            globmax = 0
            for i in xrange(len(dataPoints)):  # find max in plot list to know what to make the y value for the milestone points
                for j in xrange(len(dataPoints[i])):
                    if dataPoints[i][j][1] >= globmax:
                        globmax = dataPoints[i][j][1]
            milestonePlot = [[1, 0]]  # start the plot for milestones
            if windowType == "letter":  # then find the location of each occurence of msWord (milestoneword)
                i = fileString.find(msWord)
                while i != -1:
                    milestonePlot.append([i + 1, 0])  # and plot a vertical line up and down at that location
                    milestonePlot.append([i + 1, globmax])  # sets height of vertical line to max val of data
                    milestonePlot.append([i + 1, 0])
                    i = fileString.find(msWord, i + 1)
                milestonePlot.append([len(fileString) - int(windowSize) + 1, 0])  #append very last point
            elif windowType == "word":  # does the same thing for window of words and lines but has to break up the data
                splitString = fileString.split()  # according to how it is done in rw_analyze(), to make sure x values are correct
                splitString = [i for i in splitString if i != '']
                wordNum = 0
                for i in splitString:  #for each 'word' 
                    wordNum += 1 #counter++
                    if i.find(msWord) != -1:  #If milestone is found in string
                        milestonePlot.append([wordNum, 0])          #
                        milestonePlot.append([wordNum, globmax])    # Plot vertical line
                        milestonePlot.append([wordNum, 0])          #
                milestonePlot.append([len(splitString) - int(windowSize) + 1, 0])  #append very last point
            else:  # does the same thing for window of words and lines but has to break up the data
                if re.search('\r',
                             fileString) is not None:  # according to how it is done in rw_analyze(), to make sure x values are correct
                    splitString = fileString.split('\r')
                else:
                    splitString = fileString.split('\n')
                lineNum = 0
                for i in splitString: #for each line
                    lineNum += 1      #counter++
                    if i.find(msWord) != -1:  #If milestone is found in string
                        milestonePlot.append([lineNum, 0])          #
                        milestonePlot.append([lineNum, globmax])    #Plot vertical line
                        milestonePlot.append([lineNum, 0])          #
                milestonePlot.append([len(splitString) - int(windowSize) + 1, 0]) #append last point
            dataPoints.append(milestonePlot)    #append milestone plot list to the list of plots
            legendLabelsList[0] += msWord.encode('UTF-8')   #add milestone word to list of plot labels

        return dataPoints, dataList, graphTitle, xAxisLabel, yAxisLabel, legendLabelsList

    def generateRWmatrixPlot(self, dataPoints, legendLabelsList):
        """
        Generates rolling windows graph raw data matrix

        Args:
            dataPoints: a list of [x, y] points

        Returns:
            Output file path and extension.
        """

        extension = '.csv'
        deliminator = ','

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)
        outFilePath = pathjoin(folderPath, 'RWresults' + extension)

        maxlen = 0
        for i in xrange(len(dataPoints)):
            if len(dataPoints[i]) > maxlen: maxlen = len(dataPoints[i])
        maxlen += 1

        rows = [""] * maxlen

        legendLabelsList[0] = legendLabelsList[0].split('#')

        rows[0] = (deliminator+deliminator).join(legendLabelsList[0]) + deliminator + deliminator
        
        with open(outFilePath, 'w') as outFile:
            for i in xrange(len(dataPoints)):
                for j in xrange(1, len(dataPoints[i]) + 1):
                    rows[j] = rows[j] + str(dataPoints[i][j - 1][0]) + deliminator + str(
                        dataPoints[i][j - 1][1]) + deliminator

            for i in xrange(len(rows)):
                outFile.write(rows[i] + '\n')
        outFile.close()

        return outFilePath, extension

    def generateRWmatrix(self, dataList):
        """
        Generates rolling windows graph raw data matrix
        Args:
            dataPoints: a list of [x, y] points
        Returns:
            Output file path and extension.
        """

        extension = '.csv'
        deliminator = ','

        folderPath = pathjoin(session_functions.session_folder(), constants.RESULTS_FOLDER)
        if (not os.path.isdir(folderPath)):
            makedirs(folderPath)
        outFilePath = pathjoin(folderPath, 'RWresults' + extension)

        rows = ["" for _ in xrange(len(dataList[0]))]

        with open(outFilePath, 'w') as outFile:
            for i in xrange(len(dataList)):

                for j in xrange(len(dataList[i])):
                    rows[j] = rows[j] + str(dataList[i][j]) + deliminator

            for i in xrange(len(rows)):
                outFile.write(rows[i] + '\n')
        outFile.close()

        return outFilePath, extension

    def generateJSONForD3(self, mergedSet):
        """
        Generates the data formatted nicely for the d3 visualization library.

        Args:
            mergedSet: Boolean saying whether to merge all files into one dataset or, if false,
                create a list of datasets.

        Returns:
            An object, formatted in the JSON that d3 needs, either a list or a dictionary.
        """
        chosenFileIDs = [int(x) for x in request.form.getlist('segmentlist')]

        activeFiles = []
        if chosenFileIDs:
            for ID in chosenFileIDs:
                activeFiles.append(self.files[ID])
        else:
            for lFile in self.files.values():
                if lFile.active:
                    activeFiles.append(lFile)

        if mergedSet:  # Create one JSON Object across all the chunks
            minimumLength = int(request.form['minlength']) if 'minlength' in request.form else 0
            masterWordCounts = {}
            for lFile in activeFiles:
                wordCounts = lFile.getWordCounts()

                for key in wordCounts:
                    if len(key) <= minimumLength:
                        continue

                    if key in masterWordCounts:
                        masterWordCounts[key] += wordCounts[key]
                    else:
                        masterWordCounts[key] = wordCounts[key]

            if 'vizmaxwords' in request.form:
                maxNumWords = int(request.form['maxwords'])
                sortedwordcounts = sorted(masterWordCounts, key=masterWordCounts.__getitem__)
                j = len(sortedwordcounts) - maxNumWords
                for i in xrange(len(sortedwordcounts) - 1, -1, -1):
                    if i < j:
                        del masterWordCounts[sortedwordcounts[i]]

            returnObj = general_functions.generateD3Object(masterWordCounts, objectLabel="tokens", wordLabel="name",
                                                           countLabel="size")

        else:  # Create a JSON object for each chunk
            returnObj = []
            for lFile in activeFiles:
                returnObj.append(lFile.generateD3JSONObject(wordLabel="text", countLabel="size"))

        return returnObj  # NOTE: Objects in JSON are dictionaries in Python, but Lists are Arrays are Objects as well.

    def generateMCJSONObj(self, malletPath):
        """
        Generates a JSON object for multicloud when working with a mallet .txt file.

        Args:
            malletPath: path to the saved mallet .txt file 

        Returns:
            An object, formatted in the JSON that d3 needs, either a list or a dictionary.
        """

        if request.form['analysistype'] == 'userfiles':

            JSONObj = self.generateJSONForD3(mergedSet=False)

        else:  # request.form['analysistype'] == 'topicfile'

            topicString = str(request.files['optuploadname'])
            topicString = re.search(r"'(.*?)'", topicString)
            topicString = topicString.group(1)

            if topicString != '':
                request.files['optuploadname'].save(malletPath)

            f = open(malletPath, 'r')
            content = f.read()
            f.close()
            if content.startswith('#doc source pos typeindex type topic'):
                # --- begin converting a Mallet file into the file d3 can understand ---
                tuples = []
                # Read the output_state file
                with open(malletPath) as f:
                    # Skip the first three lines
                    for _ in xrange(3):
                        next(f)
                    # Create a list of type:topic combinations
                    for line in f:
                        line = re.sub('\s+', ' ', line)  # Make sure the number of columns is correct
                        try:
                            doc, source, pos, typeindex, type, topic = line.rstrip().split(' ')
                            tuple = type + ':' + topic
                            tuples.append(tuple)
                        except:
                            raise Exception(
                                "Your source data cannot be parsed into a regular number of columns. Please ensure that there are no spaces in your file names or file paths. It; may be easiest to open the outpt_state file in a spreadsheet using a space as; the delimiter and text as the field type. Data should only be present in columns; A to F. Please fix any misaligned data and run this script again.")

                # Count the number of times each type-topic combo appears
                from collections import defaultdict

                topicCount = defaultdict(int)
                for x in tuples:
                    topicCount[x] += 1

                # Populate a topicCounts dict with type: topic:count
                words = []
                topicCounts = {}
                for k, v in topicCount.iteritems():
                    type, topic = k.split(':')
                    count = int(v)
                    tc = topic + ":" + str(count)
                    if type in words:
                        topicCounts[type] = topicCounts[type] + " " + tc
                    else:
                        topicCounts[type] = tc
                    words.append(type)

                # Add a word ID
                out = ""
                i = 0
                for k, v in topicCounts.iteritems():
                    out += str(i) + " " + k + " " + v + "\n"
                    i += 1

                # Write the output file
                f = open(malletPath + '_jsonform', 'w')
                f.write(out)  # Python will convert \n to os.linesep
                f.close()
                # --- end converting a Mallet file into the file d3 can understand ---
            else:
                f = open(malletPath + '_jsonform', 'w')
                f.write(content)
                f.close()

            JSONObj = multicloud_topic.topicJSONmaker(malletPath + '_jsonform')

        return JSONObj

    def generateSimilarities(self):
        """
        Generates cosine similarity rankings between the comparison file and a model generated from other active files.

        Args:
            compFile: ID of the comparison file (a lexos file) sent through from the request.form (that's why there's funky unicode stuff that has to happen)  

        Returns:
            Two strings, one of the files ranked in order from best to worst, the second of those files' cosine similarity scores 
        """

        # generate tokenized lists of all documents and comparison document
        compFile = request.form['uploadname']
        useWordTokens = request.form['tokenType'] == 'word'
        ngramSize = int(request.form['tokenSize'])
        useUniqueTokens = 'simsuniquetokens' in request.form
        onlyCharGramsWithinWords = 'inWordsOnly' in request.form


        # iterates through active files and adds each file's contents as a string to allContents and label to tempLabels
        # this loop excludes the comparison file
        allContents = []  # list of strings-of-text for each segment
        tempLabels = []  # list of labels for each segment
        for lFile in self.files.values():
            if lFile.active and (str(lFile.id).decode("utf-8") != compFile.decode("utf-8")):
                contentElement = lFile.loadContents()
                contentElement = ''.join(contentElement.splitlines())  # take out newlines
                allContents.append(contentElement)

                if (request.form["file_" + str(lFile.id)] == lFile.label):
                    tempLabels.append((lFile.label).encode("utf-8", "replace"))
                else:
                    newLabel = request.form["file_" + str(lFile.id)].encode("utf-8", "replace")
                    tempLabels.append(newLabel)

        # builds textAnalyze according to tokenize/normalize options so that the file contents (in AllContents) can be processed accordingly
        if useWordTokens:
            tokenType = u'word'
        else:
            tokenType = u'char'
            if onlyCharGramsWithinWords:
                tokenType = u'char_wb'

        CountVector = CountVectorizer(input=u'content', encoding=u'utf-8', min_df=1,
                                      analyzer=tokenType, token_pattern=ur'(?u)\b[\w\']+\b',
                                      ngram_range=(ngramSize, ngramSize),
                                      stop_words=[], dtype=float)

        textAnalyze = CountVector.build_analyzer()

        texts = []
        # processes each file according to CountVector options. This returns a list of tokens created from each allContents string and appends it
        # to texts
        for list in allContents:
            texts.append(textAnalyze(list))

        # saves the path to the contents of the comparison File, reads it into doc and then processes it using textAnalyze as compDoc
        docPath = self.files[int(compFile.decode("utf-8"))].savePath

        doc = ""
        with open(docPath) as f:
            for line in f:
                doc += line.decode("utf-8")
        f.close()
        compDoc = textAnalyze(doc)

        # call similarity.py to generate the similarity list
        docsListscore, docsListname = similarity.similarityMaker(texts, compDoc, tempLabels, useUniqueTokens)

        # concatinates lists as strings with *** delimiter so that the info can be passed successfully through the html/javascript later on
        docStrScore = ""
        docStrName = ""
        for score in docsListscore:
            docStrScore += str(score).decode("utf-8") + "***"
        for name in docsListname:
            docStrName += str(name).decode("utf-8") + "***"

        return docStrScore.encode("utf-8"), docStrName.encode("utf-8")

    def getTopWordOption(self):
        """
        get the top word option from the front end

        :return:
            testbyClass: option for proportional z test to see whether to use testgroup() or testall()
                            see analyze/topword.py testgroup() and testall() for more
            option: the word filter to determine what word to send to the topword analysis
                        see analyze/topword.py testgroup() and testall() for more
            High: the Highest Proportion that sent to topword analysis
            Low: the Lowest Proportion that sent to topword analysis
        """
        if 'testInput' in request.form:  # when do KW this is not in request.form
            testbyClass = request.form['testInput'] == 'useclass'
        else:
            testbyClass = True

        outlierMethod = 'StdE' if request.form['outlierMethodType'] == 'stdErr' else 'IQR'

        # begin get option
        Low = 0.0  # init Low
        High = 1.0  # init High

        if outlierMethod == 'StdE':
            outlierRange = request.form["outlierTypeStd"]
        else:
            outlierRange = request.form["outlierTypeIQR"]

        if request.form['groupOptionType'] == 'all':
            option = 'CustomP'
        elif request.form['groupOptionType'] == 'bio':
            option = outlierRange + outlierMethod
        else:
            if request.form['useFreq'] == 'RC':
                option = 'CustomR'
                High = int(request.form['upperboundRC'])
                Low = int(request.form['lowerboundRC'])
                print 'bound'
            else:
                option = 'CustomP'
                High = float(request.form['upperboundPC'])
                Low = float(request.form['lowerboundPC'])
                print 'bound'

        return testbyClass, option, Low, High

    def GenerateZTestTopWord(self):
        """

        this method read from the
        :return:
        """
        testbyClass, option, Low, High = self.getTopWordOption()

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showDeleted, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=False, normOption=normOption,
                                            onlyCharGramsWithinWords=onlyCharGramsWithinWords, ngramSize=ngramSize,
                                            useFreq=False, greyWord=greyWord, showGreyWord=showDeleted, MFW=MFW,
                                            cull=culling)
        WordLists = matrixtodict(countMatrix)

        if not testbyClass:   # test for all

            return testall(WordLists, option=option, Low=Low, High=High)

        else:   # test by class

            # create division map
            divisionmap, NameMap, classLabelMap = self.getClassDivisionMap()
            if len(divisionmap) == 1:
                raise ValueError('only one class given, cannot do Z-test By class, at least 2 class needed')

            # divide into group
            diviCopy = deepcopy(divisionmap)  # because the division map need to be used later
            GroupWordLists = groupdivision(WordLists, diviCopy)

            # test
            analysisResult = testgroup(GroupWordLists, option=option, Low=Low, High=High)

            # convert to human readable form
            humanResult = {}
            for key in analysisResult.keys():
                fileName = NameMap[key[0]][key[1]]
                CompClassName = classLabelMap[key[2]]
                humanResult.update({'file: ' + fileName + ' compare to class ' + CompClassName: analysisResult[key]})

            return humanResult

    def generateKWTopwords(self):

        """


        :return: :raise ValueError:
        """
        testbyClass, option, Low, High = self.getTopWordOption()

        ngramSize, useWordTokens, useFreq, useTfidf, normOption, greyWord, showDeleted, onlyCharGramsWithinWords, MFW, culling = self.getMatrixOptions()

        countMatrix = self.getMatrix(useWordTokens=useWordTokens, useTfidf=False, normOption=normOption,
                                            onlyCharGramsWithinWords=onlyCharGramsWithinWords, ngramSize=ngramSize,
                                            useFreq=False, greyWord=greyWord, showGreyWord=showDeleted, MFW=MFW,
                                            cull=culling)

        # create a word list to handle wordfilter in KWtest()
        WordLists = general_functions.matrixtodict(countMatrix)

        # create division map
        divisionmap, NameMap, classLabel = self.getClassDivisionMap()
        print divisionmap
        if len(divisionmap) == 1:
            raise ValueError('only one class given, cannot do Kruaskal-Wallis test, at least 2 class needed')

        # divide the countMatrix via division map
        words = countMatrix[0][1:]  # get the list of word
        for i in range(len(divisionmap)):
            for j in range(len(divisionmap[i])):
                id = divisionmap[i][j]
                divisionmap[i][j] = countMatrix[id + 1]  # +1 because the first line is words
        Matrixs = divisionmap

        AnalysisResult = KWtest(Matrixs, words, WordLists=WordLists, option=option, Low=Low, High=High)

        return AnalysisResult

    def getClassDivisionMap(self):
        """


        :return:
        """
        # create division map
        divisionmap = [[0]]  # initialize the division map (at least one file)
        files = self.getActiveFiles()
        Namemap = [[files[0].name]]
        ClassLabelMap = [files[0].classLabel]

        for id in range(1, len(files)):  # because 0 is defined in the initialize

            insideExistingGroup = False

            for i in range(len(divisionmap)):  # for group in division map
                for existingid in divisionmap[i]:
                    if files[existingid].classLabel == files[id].classLabel:
                        divisionmap[i].append(id)
                        Namemap[i].append(files[id].name)
                        insideExistingGroup = True
                        break

            if not insideExistingGroup:
                divisionmap.append([id])
                Namemap.append([files[id].name])
                ClassLabelMap.append(files[id].classLabel)

        return divisionmap, Namemap, ClassLabelMap

    ###### DEVELOPMENT SECTION ########
    def classifyFile(self):
        """
        Applies a given class label the selected file.

        Args:
            None

        Returns:
            None
        """
        classLabel = request.data

        self.files.setClassLabel(classLabel)

    def getPreviewsOfAll(self):
        """
        Creates a formatted list of previews from every  file in the file manager. For use in the Select screen.

        Args:
            None

        Returns:
            A list of dictionaries with preview information for every file.
        """
        previews = []

        for lFile in self.files.values():
            values = {"id": lFile.id, "filename": lFile.name, "label": lFile.label, "class": lFile.classLabel,
                      "source": lFile.originalSourceFilename, "preview": lFile.getPreview(), "state": lFile.active}
            previews.append(values)

        return previews

    def deleteAllFile(self):
        """
        Deletes every active file by calling the delete method on the LexosFile object before removing it
        from the dictionary.

        Args:
            None.

        Returns:
            None.
        """
        for fileID, lFile in self.files.items():
            lFile.cleanAndDelete()
            del self.files[fileID]  # Delete the entry

###### END DEVELOPMENT SECTION ########

"""
LexosFile:

Description:
    Class for an object to hold all information about a specific uploaded file.
    Each uploaded file will be stored in a unique object, and accessed through the FileManager files dictionary.

Major data attributes:
contents: A string that (sometimes) contains the text contents of the file. Most of the time
"""


class LexosFile:
    def __init__(self, originalFilename, fileName, fileString, fileID):
        """ Constructor
        Creates a new LexosFile object from the information passed in, and performs some preliminary processing.

        Args:
            fileName: File name of the originally uploaded file.
            fileString: Contents of the file's text.
            fileID: The ID to assign to the new file.

        Returns:
            The newly constructed LexosFile object.
        """
        self.id = fileID  # Starts out without an id - later assigned one from FileManager
        self.originalSourceFilename = originalFilename
        self.name = fileName
        self.contentsPreview = self.generatePreview(fileString)
        self.savePath = pathjoin(session_functions.session_folder(), constants.FILECONTENTS_FOLDER,
                                 str(self.id) + '.txt')
        self.saveContents(fileString)

        self.active = True
        self.classLabel = ''

        splitName = self.name.split('.')

        self.label = '.'.join(splitName[:-1])

        self.setTypeFrom(splitName[-1], fileString)

        self.hasTags = self.checkForTags(fileString)

        self.options = {}

    def cleanAndDelete(self):
        """
        Handles everything necessary for the LexosFile object to be deleted cleanly, after this method has been called.

        Args:
            None

        Returns:
            None
        """
        # Delete the file on the hard drive where the LexosFile saves its contents string
        remove(self.savePath)

    def loadContents(self):
        """
        Loads the contents of the file from the hard drive.

        Args:
            None

        Returns:
            The string of the file contents.
        """
        # encryption
        # # decrypt file
        # if constants.FILE_CONTENT_KEY != '':
        #     savepath = general_functions.decryptFile(self.savePath, constants.FILE_CONTENT_KEY)
        # else:
        #     savepath = self.savePath

        # reading content
        content = open(self.savePath, 'r').read().decode('utf-8')

        # encryption
        # # delete the plain text file
        # if constants.FILE_CONTENT_KEY != '':
        #     os.remove(savepath)

        return content

    def saveContents(self, fileContents):
        """
        Saves the contents of the file to the hard drive, possibly overwriting the old version.

        Args:
            fileContents: The string with the contents of the file to be saved.

        Returns:
            None
        """
        open(self.savePath, 'w').write(fileContents.encode('utf-8'))
        # encryption
        # if constants.FILE_CONTENT_KEY != '':
        #     general_functions.encryptFile(self.savePath, constants.FILE_CONTENT_KEY)

    def setTypeFrom(self, extension, fileContents):
        """
        Sets the type of the file from the file's extension and contents.

        Args:
            None

        Returns:
            None
        """
        DOEPattern = re.compile("<publisher>Dictionary of Old English")

        if DOEPattern.search(fileContents) != None:
            self.type = 'doe'

        elif extension == 'sgml':
            self.type = 'sgml'

        elif extension == 'html' or extension == 'htm':
            self.type = 'html'

        elif extension == 'xml':
            self.type = 'xml'

        else:
            self.type = 'text'

    def checkForTags(self, fileContents):
        """
        Checks the file for tags.

        Args:
            None

        Returns:
            A boolean representing the presence of tags in the contents.
        """
        if re.search('\<.*\>', fileContents):
            return True
        else:
            return False

    def generatePreview(self, textString=None):
        """
        Generates a preview either from the provided text string or from the contents on the disk.

        Args:
            textString: Optional argument of a string from which to create the preview.

        Returns:
            A string containing a preview of the larger string.
        """
        if textString == None:
            return general_functions.makePreviewFrom(self.loadContents())
        else:
            return general_functions.makePreviewFrom(textString)

    def getPreview(self):
        """
        Gets the previews, and loads it before if necessary.

        Args:
            None

        Returns:
            The preview string of the contents of the file.
        """
        if self.contentsPreview == '':
            self.contentsPreview = self.generatePreview()

        return self.contentsPreview

    def enable(self):
        """
        Enables the file, re-generating the preview.

        Args:
            None

        Returns:
            None
        """
        self.active = True
        self.contentsPreview = self.generatePreview()

    def disable(self):
        """
        Disables the file, emptying the preview.

        Args:
            None

        Returns:
            None
        """
        self.active = False
        self.contentsPreview = ''

    def setClassLabel(self, classLabel):
        """
        Assigns the class label to the file.

        Args:
            classLabel= the label to be assigned to the file

        Returns:
            None
        """
        self.classLabel = classLabel

    def setName(self, filename):
        """
        Assigns the class label to the file.

        Args:
            filename= the filename to be assigned to the file

        Returns:
            None
        """
        self.name = filename

    def getScrubOptions(self):
        """
        Gets the options for scrubbing from the request.form and returns it in a formatted dictionary.

        Args:
            None

        Returns:
            A dictionary of the chosen options for scrubbing a file.
        """
        scrubOptions = {}

        for uploadFile in constants.OPTUPLOADNAMES:
            if uploadFile in self.options['scrub']:
                scrubOptions[uploadFile] = self.options['scrub'][uploadFile]

        for checkbox in constants.SCRUBBOXES:
            scrubOptions[checkbox] = (checkbox in request.form)
        for textarea in constants.SCRUBINPUTS:
            scrubOptions[textarea] = request.form[textarea]
        for uploadFile in request.files:
            fileName = request.files[uploadFile].filename
            if (fileName != ''):
                scrubOptions[uploadFile] = fileName
        if 'tags' in request.form:
            scrubOptions['keepDOEtags'] = request.form['tags'] == 'keep'

        return scrubOptions

    def scrubContents(self, savingChanges):
        """
        Scrubs the contents of the file according to the options chosen by the user, saves the changes or doesn't,
        and returns a preview of the changes either way.

        Args:
            savingChanges: Boolean saying whether or not to save the changes made.

        Returns:
            Returns a preview string of the possibly changed file.
        """
        cache_options = []
        for key in request.form.keys():
            if 'usecache' in key:
                cache_options.append(key[len('usecache'):])

        if 'scrub' not in self.options:
            self.options['scrub'] = {}
        scrubOptions = self.getScrubOptions()

        if savingChanges:
            textString = self.loadContents()
        else:
            textString = self.contentsPreview

        textString = scrubber.scrub(textString,
                                    filetype=self.type,
                                    lower=scrubOptions['lowercasebox'],
                                    punct=scrubOptions['punctuationbox'],
                                    apos=scrubOptions['aposbox'],
                                    hyphen=scrubOptions['hyphensbox'],
                                    digits=scrubOptions['digitsbox'],
                                    tags=scrubOptions['tagbox'],
                                    keeptags=scrubOptions['keepDOEtags'],
                                    opt_uploads=request.files,
                                    cache_options=cache_options,
                                    cache_folder=session_functions.session_folder() + '/scrub/',
                                    previewing=not savingChanges)

        if savingChanges:
            self.saveContents(textString)

            self.contentsPreview = self.generatePreview()
            textString = self.contentsPreview

            self.saveScrubOptions()

        return textString

    def saveScrubOptions(self):
        """
        Saves the scrubbing options into the LexosFile object's metadata.

        Args:
            None

        Returns:
            None
        """
        self.options['scrub'] = self.getScrubOptions()

    def setScrubOptionsFrom(self, parent):
        """
        Sets the scrubbing options from another file, most often the parent file that a child file was cut from.

        Args:
            None

        Returns:
            None
        """
        if ("scrub" not in self.options):
            self.options['scrub'] = {}
            if ("scrub" in parent.options):
                self.options['scrub'] = parent.options['scrub']
            else:
                parent.options['scrub'] = {}

    def cutContents(self):
        """
        Cuts the contents of the file according to options chosen by the user.

        Args:
            None

        Returns:
            The substrings that the file contents have been cut up into.
        """
        textString = self.loadContents()

        cuttingValue, cuttingType, overlap, lastProp = self.getCuttingOptions()

        textStrings = cutter.cut(textString, cuttingValue=cuttingValue, cuttingType=cuttingType, overlap=overlap,
                                 lastProp=lastProp)

        return textStrings

    def getCuttingOptions(self, overrideID=None):
        """
        Gets the cutting options for a specific file, or if not defined, then grabs the overall options, from the request.form.

        Args:
            overrideID: An id for which to grab the options instead of the object's id.

        Returns:
            A tuple of options for cutting the files.
        """
        if overrideID == None:
            fileID = self.id
        else:
            fileID = overrideID

        if request.form['cutValue_' + str(fileID)] != '' or 'cutByMS_' + str(
                fileID) in request.form:  # A specific cutting value has been set for this file
            optionIdentifier = '_' + str(fileID)
        else:
            optionIdentifier = ''

        cuttingValue = request.form[
            'cutValue' + optionIdentifier] if 'cutByMS' + optionIdentifier not in request.form else request.form[
            'MScutWord' + optionIdentifier]
        cuttingType = request.form[
            'cutType' + optionIdentifier] if 'cutByMS' + optionIdentifier not in request.form else 'milestone'
        overlap = request.form[
            'cutOverlap' + optionIdentifier] if 'cutOverlap' + optionIdentifier in request.form else '0'
        lastProp = request.form['cutLastProp' + optionIdentifier].strip(
            '%') if 'cutLastProp' + optionIdentifier in request.form else '50'

        return (cuttingValue, cuttingType, overlap, lastProp)

    def saveCutOptions(self, parentID):
        """
        Saves the cutting options into the LexosFile object's metadata.

        Args:
            parentID: The id of the parent file from which this file has been cut.

        Returns:
            None
        """
        cuttingValue, cuttingType, overlap, lastProp = self.getCuttingOptions(parentID)

        if 'cut' not in self.options:
            self.options['cut'] = {}

        self.options['cut']['value'] = cuttingValue
        self.options['cut']['type'] = cuttingType
        self.options['cut']['chunk_overlap'] = overlap
        self.options['cut']['last_chunk_prop'] = lastProp

    def numLetters(self):
        """
        Gets the number of letters in the file.

        Args:
            None

        Returns:
            Number of letters in the file.
        """
        length = len(self.loadContents())
        return length

    def numWords(self):
        """
        Gets the number of words in the file.

        Args:
            None

        Returns:
            Number of words in the file.
        """
        length = len(self.loadContents().split())
        return length

    def numLines(self):
        """
        Gets the number of lines in the file.

        Args:
            None

        Returns:
            Number of lines in the file.
        """
        length = len(self.loadContents().split('\n'))
        return length

    def getWordCounts(self):
        """
        Gets the dictionary of { word: word_count }'s in the file.

        Args:
            None

        Returns:
            The word count dictionary for this file.
        """
        from collections import Counter

        wordCountDict = dict(Counter(self.loadContents().split()))
        return wordCountDict

    def generateD3JSONObject(self, wordLabel, countLabel):
        """
        Generates a JSON object for d3 from the word counts of the file.

        Args:
            wordLabel: Label to use for identifying words in the sub-objects.
            countLabel: Label to use for identifying counts in the sub-objects.

        Returns:
            The resultant JSON object, formatted for d3.
        """
        wordCounts = self.getWordCounts()
        return general_functions.generateD3Object(wordCounts, self.label, wordLabel, countLabel)

    def getLegend(self):
        """
        Generates the legend for the file, for use in the dendrogram.

        Args:
            None

        Returns:
            A string with the legend information for the file.
        """

        if request.form["file_" + str(self.id)] == self.label:
            strLegend = self.label + ": \n"
        else:
            strLegend = request.form["file_" + str(self.id)] + ": \n"

        strLegend += "\nScrubbing Options - "

        if 'scrub' in self.options:

            if ("punctuationbox" in self.options["scrub"]) and (self.options["scrub"]['punctuationbox'] == True):
                strLegend += "Punctuation: removed, "

                if ('aposbox' in self.options["scrub"]) and (self.options["scrub"]['aposbox'] == True):
                    strLegend += "Apostrophes: kept, "
                else:
                    strLegend += "Apostrophes: removed, "

                if ('hyphensbox' in self.options["scrub"]) and (self.options["scrub"]['hyphensbox'] == True):
                    strLegend += "Hyphens: kept, "
                else:
                    strLegend += "Hypens: removed, "
            else:
                strLegend += "Punctuation: kept, "

            if ('lowercasebox' in self.options["scrub"]) and (self.options["scrub"]['lowercasebox'] == True):
                strLegend += "Lowercase: on, "
            else:
                strLegend += "Lowercase: off, "

            if ('digitsbox' in self.options["scrub"]) and (self.options["scrub"]['digitsbox'] == True):
                strLegend += "Digits: removed, "
            else:
                strLegend += "Digits: kept, "

            if ('tagbox' in self.options["scrub"]) and (self.options["scrub"]['tagbox'] == True):
                strLegend += "Tags: removed, "
            else:
                strLegend += "Tags: kept, "

            if 'keepDOEtags' in self.options["scrub"]:
                if (self.options["scrub"]['keepDOEtags'] == True):
                    strLegend += "corr/foreign words: kept, "
                else:
                    strLegend += "corr/foreign words: discard, "

            # stop words
            if ('swfileselect[]' in self.options["scrub"]) and (self.options["scrub"]['swfileselect[]'] != ''):
                strLegend = strLegend + "Stopword file: " + self.options["scrub"]['swfileselect[]'] + ", "
            if ('manualstopwords' in self.options["scrub"]) and (self.options["scrub"]['manualstopwords'] != ''):
                strLegend = strLegend + "Stopwords: [" + self.options["scrub"]['manualstopwords'] + "], "

            # lemmas
            if ('lemfileselect[]' in self.options["scrub"]) and (self.options["scrub"]['lemfileselect[]'] != ''):
                strLegend = strLegend + "Lemma file: " + self.options["scrub"]['lemfileselect[]'] + ", "
            if ('manuallemmas' in self.options["scrub"]) and (self.options["scrub"]['manuallemmas'] != ''):
                strLegend = strLegend + "Lemmas: [" + self.options["scrub"]['manuallemmas'] + "], "

            # consolidations
            if ('consfileselect[]' in self.options["scrub"]) and (self.options["scrub"]['consfileselect[]'] != ''):
                strLegend = strLegend + "Consolidation file: " + self.options["scrub"]['consfileselect[]'] + ", "
            if ('manualconsolidations' in self.options["scrub"]) and (
                        self.options["scrub"]['manualconsolidations'] != ''):
                strLegend = strLegend + "Consolidations: [" + self.options["scrub"]['manualconsolidations'] + "], "

            # special characters (entities) - pull down
            if ('entityrules' in self.options["scrub"]) and (self.options["scrub"]['entityrules'] != 'default'):
                strLegend = strLegend + "Special Character Rule Set: " + self.options["scrub"]['entityrules'] + ", "
            if ('scfileselect[]' in self.options["scrub"]) and (self.options["scrub"]['scfileselect[]'] != ''):
                strLegend = strLegend + "Special Character file: " + self.options["scrub"]['scfileselect[]'] + ", "
            if ('manualspecialchars' in self.options["scrub"]) and (self.options["scrub"]['manualspecialchars'] != ''):
                strLegend = strLegend + "Special Characters: [" + self.options["scrub"]['manualspecialchars'] + "], "

        else:
            strLegend += "Unscrubbed."

        strWrappedScrubOptions = textwrap.fill(strLegend, constants.CHARACTERS_PER_LINE_IN_LEGEND)


        # ----------- CUTTING OPTIONS -------------------
        strLegend = "Cutting Options - "

        if "cut" not in self.options:
            strLegend += "Not cut."

        else:
            if (self.options["cut"]["value"] != ''):
                strLegend += "Cut by [" + self.options["cut"]['type'] + "]: " + self.options["cut"]["value"] + ", "
            else:
                strLegend += "Cut by [" + self.options["cut"]['type'] + "], "

            strLegend += "Percentage Overlap: " + str(self.options["cut"]["chunk_overlap"]) + ", "
            if self.options["cut"]['type'] != 'number':
                strLegend += "Last Chunk Proportion: " + str(self.options["cut"]["last_chunk_prop"])

        strLegend += "\n"

        strWrappedCuttingOptions = textwrap.fill(strLegend, constants.CHARACTERS_PER_LINE_IN_LEGEND)

        # make the three section appear in separate paragraphs
        strLegendPerObject = strWrappedScrubOptions + "\n" + strWrappedCuttingOptions

        return strLegendPerObject