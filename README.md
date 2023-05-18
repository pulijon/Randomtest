# Rationale for randomtest.py

Paper-based examinations avoid sophisticated methods of copying but make very easy checking own answers against those of others.

Online exams allow randomisation of questions, combating the natural temptation for students to answer as their neighbours do.

However, online exams require computers and they are not always available in examination rooms. In addition, computers themselves can hide unholy tools that can affect honesty.

The tool randomtest.py produce as many different paper-based exams as students. Everybody receives the same questions and the same possible answers, but questions are randomized (question 3 for an alumn can be question 17 for other) and answers for the same questions are also randomized (for the same question, student X shoud answer a as student Y shoud answer b).

This method could difficult the correction of tests. Because of that, randomtest.py includes a QR code with encrypted answers that can be read by an Android application (still not uploaded). There is also a text file with the correct answer of each exam (every exam is identified by a number) and an audio file with the TTS (text to speech) conversion of the text file.

Questions and metadata for the exam are defined in a YAML file. The number of exams, the directory for templates and results, the password for encryption answers are options for the program.

The result is a PDF file with all the exams

# Requirements
Computer Linux, Mac or Windows with:
* Python 3.x installation
* Modules:
    * yaml
    * qrcode
    * jinja2
    * pdfkit
    * pypdf2
    * base64
    * getpass
    * hashlib

# User guide

**randomtest.py** is a Python module that runs through a Python 3.x interpreter.

It has a very simple CLI interface autodocumented (option **-h**)

```console
C:\Desarrollo\Python\Randomtest>py randomtest.py -h
usage: randomtest.py [-h] [-t TEMPLATE] [-d DATA] [-r RESULT] [-n NUM_EXAMS]

options:
  -h, --help            show this help message and exit
  -t TEMPLATE, --template TEMPLATE
                        Fichero de plantilla. Por defecto exam/templates/exam.html
  -d DATA, --data DATA  Fichero de datos. Por defecto, exam/data/data.yml
  -r RESULT, --result RESULT
                        Fichero de resultado. Por defecto, exam/results/exam.pdf
  -n NUM_EXAMS, --num-exams NUM_EXAMS
                        Número de exámenes. Por defecto, 3
```