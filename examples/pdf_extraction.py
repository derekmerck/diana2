import csv
import PyPDF2 as pp
import re

from tqdm import tqdm

fn = r"D:\Brown\Research\Raw_Data\thyroid_bx_path\path2\Thyroid Cyto Abn 7-1-2014 to 11-10-2017.pdf"
# r"D:\Brown\Research\Raw_Data\thyroid_bx_path\path2\Thyroid Cyto Abn 7-1-2008 to 7-1-2014.pdf"
pos_neg = 'both'
pdf = pp.PdfFileReader(open(fn, 'rb'))

list_of_extracted_stuff = []
for page in tqdm(range(338), total=338):
    pdf_page = pdf.getPage(page)
    text_list = pdf_page.extractText().split('Primary Pathologist')
    for text in text_list:
        extracted_stuff = {}
        begin = False
        text = text.split('\n')
        for element in text:
            # Look for Case ID (C##-####)
            if re.search('Accession Date', element):
                begin = True
                extracted_stuff['ACCESSION DATE'] = text[text.index(element)-1]
            if begin and re.search('Sign-Out Date', element):
                extracted_stuff['SIGNOUT DATE'] = text[text.index(element)-2]
            if begin and re.search(r'C[0-9][0-9]-[0-9]*', element):
                extracted_stuff['id'] = element
            if begin and re.search('Gender', element):
                extracted_stuff['gender'] = text[text.index(element)+1]
            if begin and re.search('Race', element):
                extracted_stuff['race'] = text[text.index(element)+1]
            if begin and re.search('Age', element):
                extracted_stuff['age'] = text[text.index(element)+1]
            if begin and re.search('Interpretation', element):
                extracted_stuff['interpretation'] = ''.join(text[text.index(element):text.index(element)+6])
            if begin and re.search(r'^[0-9]+$', element):
                extracted_stuff['mrn'] = element
            if begin and re.search('Patient', element):
                extracted_stuff['patient'] = text[text.index(element)+1]

                extracted_stuff['LAST'] = extracted_stuff['patient'].split(',')[0]
                extracted_stuff['FIRST'] = extracted_stuff['patient'].split(',')[1].split(' ')[0]
                extracted_stuff['MIDDLE'] = extracted_stuff['patient'].split(',')[1].split(' ')[1].replace('.', ' ') if len(extracted_stuff['patient'].split(',')[1].split(' ')) > 1 else ''
        list_of_extracted_stuff.append(extracted_stuff)
list_of_extracted_stuff = [_ for _ in list_of_extracted_stuff if _ != {}]

headers = ['CASE', 'ACCESSION DATE', 'SIGNOUT DATE', 'SEX', 'AGE', 'LAST', 'FIRST', 'MIDDLE', 'Interpretation']
with open(r"D:\Brown\Research\Raw_Data\thyroid_bx_path\path2\{}_{}.csv".format(fn.split('\\')[-1][:-4], pos_neg).replace(' ', '_'), 'w', newline='') as myfile:
    wr = csv.writer(myfile)
    wr.writerow(headers)

    for i, e in enumerate(list_of_extracted_stuff):
        if pos_neg == 'pos':
            if 'interpretation' in e and 'CELLULAR ABNORMALITY' in e['interpretation']:
                pass
            else:
                continue
        elif pos_neg == 'neg':
            if 'interpretation' in e and 'NEGATIVE FOR MALIGNANCY' in e['interpretation']:
                pass
            else:
                continue
        elif pos_neg == 'both':
            pass
        else:
            raise NotImplementedError

        wr.writerow([e['id'], e['ACCESSION DATE'], e['SIGNOUT DATE'],
                    e['gender'], e['age'], e['LAST'], e['FIRST'], e['MIDDLE'],
                    e['interpretation'] if 'interpretation' in e else ''])
