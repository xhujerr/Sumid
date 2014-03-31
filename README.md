# Sumid

## Motivation:
This program is used as a software support for my reserach project. The research project focuses on searching patterns in URL. I try to find, describe and quantify patterns in URL. The program could be categorized as a crawler (spider).
Folowing articles describing experiments with the program:
- [Numeric pattern in URL and its modification](documentation/GN78-Roman.Hujer-1.2.pdf)
- [Usage of the "Bag of words model" for URL](http://icee.dis.spbstu.ru/proceedings2012/papers/DIST/DIST2012-22.pdf)


## Program operation - in short
- Take input url from linklist.
- Expand it to a tree.
- Try to find a pattern(s) in input url
- Try to iterate the patern (there might be about 1000 iterations per url)
- Do an operation (log/download)

- The program is intended to run for very long time (about a week). From that reason is written in multithreaded manner with too chatty logging).


## Usage
- The essential configuration is in file sumid.ini. The fine tuning is in settings.py.
- Set-up at least the linklist parameter.
- It's also good idea to set-up the WorkDir and LogDir.

- Currently the script probably won't work under Windows, because of problems with filesystem paths.


## Files and contents
Sumid is more a toolbox than a single program. Would be good to separate it in several smaller pieces. The state of art now is a result of how the program evolved satisfying concrete needs rather than seeing it as a product. Currently I am exploring the scrapy framework in order to transfer the core functionality in it.

- sumid.py - the main program containing the four classes of consumer/producer line. Each producer runs in separate thread.
- comptree.py - basically implements a tree structure for exploring web resources.
- linklist.py - takes care of the input data.
- miscutil.py - holds settings, debugging and some misc funcionality.
- bow.py - implements bag of words. Analyses URLs and looks for words with highest frequencies.
- sls.py - adaptor to pydigg library. Used to collect links for further experiments.
