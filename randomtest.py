from util import logcfg
import logging
import yaml
import os
import os.path
import random
from jinja2 import Environment, FileSystemLoader
import pdfkit
import PyPDF2
import argparse
import uuid
import qrcode
import base64
import copy
from getpass import getpass
import hashlib
from gtts import gTTS


RULES = [
    (20,2)
]

def are_the_same_question(q1, q2):
    def q1_in_q2(q1, q2):
        for k1 in q1.keys():
            if k1 not in q2:
                return False
            for v1 in q1[k1]:
                if v1 not in q2[k1]:
                    return False
        return True
    
    return q1_in_q2(q1, q2) and q1_in_q2(q2, q1)

def randomize_questions(questions):
    random.shuffle(questions)
    for q in questions:
        for v in q.values():
            random.shuffle(v)

def get_response_ix(q, qorgs):
    for qorg in qorgs:
        if are_the_same_question(q,qorg):
            key = list(q.keys())[0]
            return q[key].index(qorg[key][0])
    raise ValueError()

def get_qr_plain(responses):
    content = b'\x01'
    for r in responses:
        content += r.to_bytes(1, byteorder='little')
    return content

def get_responses(questions, qorgs):
    return [get_response_ix(q, qorgs) for q in questions]

def encrypt (clear, password):
    m = hashlib.sha256()
    m.update(password)
    pbytes = m.digest()
    return bytes([clear[i] ^ pbytes[i % len(pbytes)] for i in range(len(clear)) ])

def first_key(q):
    return list(q.keys())[0]

def apply_rules(questions, qorgs, rules):
    for rule in rules:
        q = questions[rule[0]]
        wanted_res = rule[1]
        old_res = get_response_ix(q, qorgs)
        qres = q[first_key(q)]
        if old_res != wanted_res:
            qres[old_res], qres[wanted_res] = qres[wanted_res], qres[old_res]
               
def get_qr_from_responses(i, responses, password, pfix, path):
    qr_bytes = get_qr_plain(responses)
    qr_crypt_bytes = encrypt(qr_bytes, password.encode("utf-8"))
    img = qrcode.make(base64.b64encode(qr_crypt_bytes))
    qrf = f"{pfix}_{i}.png"
    exqr = os.path.join(path, qrf)
    img.save(exqr)
    return os.path.abspath(exqr).replace('\\', '/')

def treat_responses(tres, path):
    res_str = "Estas son las respuestas de los exámenes:\n"
    for i in range(len(tres)):
        nexam = i+1
        res_str += f"Respuestas al examen {nexam}\n"
        for j in range(len(tres[i])):
            nres = j +1
            res_str += f"{nres} {chr((tres[i][j] + ord('a')))}\n"
    tts = gTTS(res_str, lang='es')
    tts.save(os.path.join(path,"responses.mp3"))
    with open(os.path.join(path, 'responses.txt'), "w") as f:
        f.write(res_str)

def get_pdfs(num_exams, data, path, template, password):
    pdfs = []
    options = {
        'page-size': 'A4',
        'margin-top': '1.5cm',
        'margin-right': '1.5cm',
        'margin-bottom': '1.5cm',
        'margin-left': '1.5cm',
        'encoding': "UTF-8",
        'enable-local-file-access': None
        # 'custom-header': [
        #     ('Accept-Encoding', 'gzip')
        # ],
        # 'cookie': [
        #     ('cookie-empty-value', '""')
        #     ('cookie-name1', 'cookie-value1'),
        #     ('cookie-name2', 'cookie-value2'),
        # ],
        # 'no-outline': None
    }   
    pfix = uuid.uuid4().hex
    questions = data['questions']
    org_questions = copy.deepcopy(questions)
    total_responses = []
    for i in range(num_exams):
        randomize_questions(questions)
        apply_rules(questions, org_questions, RULES)
        responses = get_responses(questions, org_questions)
        total_responses.append(responses)
        qr = get_qr_from_responses(i, responses, password, pfix, path)
        exid = f"Copia {i+1} de {num_exams}"
        content = template.render(questions=questions,
                                  stlevel=data['stlevel'],
                                  stname=data['stname'],
                                  modkey=data['modkey'],
                                  modname=data['modname'],
                                  date=data['date'],
                                  criteria=data['criteria'],
                                  qr=qr,
                                  exid=exid)
        exhtml = f"{pfix}_{i}.html"
        expdf = f"{pfix}_{i}.pdf"       
        exhtml = os.path.join(path, exhtml)
        expdf = os.path.join(path, expdf)
        with open(exhtml, "w", encoding="utf-8") as exf:
            exf.write(content)
        
        pdfkit.from_file(exhtml,
                         output_path=expdf,
                         options=options)
        os.remove(exhtml)
        os.remove(qr)
        pdfs.append(expdf)
    treat_responses(total_responses, path)
    return pdfs

def merge_pdfs(pdfs, fpdf):
    finalPdf = PyPDF2.PdfFileWriter()
    rpdfs = [open(pdf, "rb" ) for pdf in pdfs]
    for rpdf in rpdfs:
        partial = PyPDF2.PdfFileReader(rpdf)
        finalPdf.append_pages_from_reader(partial)
        if (len(partial.pages) % 2) == 1:
            finalPdf.addBlankPage()
    with open(fpdf, "wb") as wf:
        finalPdf.write(wf)
    for rpdf in rpdfs:
        rpdf.close()
    for pdf in pdfs:
        os.remove(pdf)

def enter_password():
    while True:
        print("Vamos a pedir que introduzcas dos veces la contraseña")
        password = getpass("Introduce la contraseña: ")
        password2 = getpass("Introduce otra vez la contraseña: ")
        if password == password2: 
            return password

def get_pars():
    DEFAULT_TEMPLATE="exam/templates/exam.html"
    DEFAULT_DATA="exam/data/data.yml"
    DEFAULT_RESULT="exam/results/exam.pdf"
    DEFAULT_NUM_EXAMS = 3

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", type=str, default=DEFAULT_TEMPLATE,
                        help=f"Fichero de plantilla. Por defecto {DEFAULT_TEMPLATE}")
    parser.add_argument("-d", "--data", type=str, default=DEFAULT_DATA,
                        help=f"Fichero de datos. Por defecto, {DEFAULT_DATA}")
    parser.add_argument("-r", "--result", type=str, default=DEFAULT_RESULT,
                        help=f"Fichero de resultado. Por defecto, {DEFAULT_RESULT}")
    parser.add_argument("-n", "--num-exams", type=int, default=DEFAULT_NUM_EXAMS,
                        help=f"Número de exámenes. Por defecto, {DEFAULT_NUM_EXAMS}")
    args = parser.parse_args()
    setattr(args, 'password', enter_password())
    return args

def get_dir_basename(f):
    fname = os.path.abspath(f)
    return os.path.split(fname)

def main():
    args = get_pars()

    template_dir, template_basename = get_dir_basename(args.template)  
    result_dir, result_basename = os.path.split(args.result)

    num_exams = args.num_exams

    with open(args.data, "r", encoding="utf-8") as f:
        dyaml = f.read()

    data = yaml.safe_load(dyaml)
    logging.info(dyaml)

    environment = Environment(loader=FileSystemLoader(template_dir))
    template = environment.get_template(template_basename)
    pdfs = get_pdfs(num_exams, data, result_dir, template, args.password)
    merge_pdfs(pdfs, args.result)

                     
if __name__ == "__main__":
    logcfg(__file__)
    logging.debug('Programa iniciado')
    main()
    logging.debug('Programa terminado')