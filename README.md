# Sumid

Script used for mass items downloading

## Motivation:
This program is used as a software support for my reserach project. The research project focuses on searching patterns in URL. I try to find, describe and quantify patterns in URL. The program could be categorized as a crawler (spider).
Folowing articles describing experiments with the program:
- [Numeric pattern in URL and its modification](documentation/GN78-Roman.Hujer-1.2.pdf)
- [Usage of the "Bag of words model" for URL](documentation/DIST2012-22-Roman.Hujer.pdf)


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