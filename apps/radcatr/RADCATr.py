"""
RADCATr - RADCAT Review Interface
Merck, Winter 2018
"""

import os, logging, csv, argparse
from tkinter import *
import tkinter.ttk as ttk

# In case running from /examples folder in git
sys.path.insert(0, os.path.abspath('../DixelKit'))
from diana.dixel import RadiologyReport

__desc__ = """
Open a CSV dump from Montage and audit entries with a Tkinter GUI.
Results are saved as they are generated as `source+audit.csv`.
"""
__version__ = "0.1.3"
__prog__ = "RADCATr"

root = Tk()
current = 0
items = []
fieldnames = []

def load_data():
    global items, fieldnames
    fp = os.path.join(data_root, fn)
    with open(fp, 'rU') as f:
        rows = csv.DictReader(f)
        for row in rows:
            # logging.debug(row)
            items.append(row)
        if fn.find("+audit") < 0:
            # Add answer columns
            fieldnames = rows.fieldnames + ['audit_radcat', 'audit_radcat3', 'agrees']
        else:
            fieldnames = rows.fieldnames


def save_data():
    if fn.find("+audit") < 0:
        out_fn = "{}+audit{}".format(os.path.splitext(fn)[0], os.path.splitext(fn)[1])
    else:
        out_fn = fn
    fp = os.path.join(data_root, out_fn)
    with open(fp, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)


def make_ui():

    def submit(*args):
        # logging.debug("setting entries")
        unscored_btn.state(['!disabled'])

        match = re.match("RADCAT(?P<radcat>\d)\+?(?P<radcat3>3)?", radcat_entry.get())
        item = items[current]

        item['audit_radcat'] = match.group('radcat')
        item['audit_radcat3'] = "Yes" if match.group('radcat3') else "No"

        if item['audit_radcat'] == "3":
            item['audit_radcat'] = 2
            item['audit_radcat3'] = "Yes"

        agrees = (item['audit_radcat'] == item['radcat']) and (item['audit_radcat3'] == item['radcat3'])

        logging.debug(item['audit_radcat'])
        logging.debug(item['audit_radcat3'])

        logging.info("Report {:<3} RADCAT grade agreement: {} (originally scored {})".format(
            "{}:".format(current+1), item['audit_radcat']==item['radcat'], item['radcat']))
        logging.info("           RADCAT f/u agreement: {} (originally scored {})".format(
            item['audit_radcat3']==item['radcat3'], item['radcat3']))

        item['agrees'] = "Yes" if agrees else "No"

        save_data()

    def go_first():
        go(0)

    def go_next():
        if current+1 < len(items):
            go(current+1)

    def go_unscored():
        for i in range(current+1, len(items)):
            if not items[i].get('audit_radcat'):
                go(i)
                break

    def go_prev():
        if current-1 >= 0:
            go(current-1)

    def go(new):
        global current
        unscored_btn.state(['disabled'])
        current = new
        update_ui()

    def update_ui():
        if items[current].get('audit_radcat'):

            audit_radcat = items[current]['audit_radcat']
            audit_radcat3 = items[current]['audit_radcat3']

            if audit_radcat == 2 and audit_radcat3:
                audit_radcat = 3
                audit_radcat3 = False

            entry = "RADCAT{}{}".format(
                audit_radcat,
                "+3" if audit_radcat3 == "Yes" else ""
            )
            radcat_entry.set(entry)
            unscored_btn.state(['!disabled'])
        else:
            radcat_entry.set('')
            # fu_entry.set(False)

        item = items[current]

        r = RadiologyReport(text=item['report_text'])
        # logging.debug(r.text)

        # extractions = r.extractions()
        # item['radcat'] = int(extractions.get('radcat'))
        # item['radcat3'] = "Yes" if extractions.get('radcat3') else "No"

        complete = [k for k in items if k.get('audit_radcat')]
        task_label_str.set("Report {} of {} ({} complete)\n{age}yo {sex} {status} {bp} {mod}".format(
            current+1, len(items), len(complete),
            status=item['status'],
            age=item['age'],
            sex=item['sex'][0],
            bp=item['body_part'],
            mod=item['modality'])
        )

        report_text['state'] = 'normal'
        report_text.delete('1.0', 'end')
        report_text.insert('1.0', r.anonymized())
        report_text['state'] = 'disabled'

        # logging.debug(item['radcat'])
        # logging.debug(item['radcat3'])


    root.title("RADCAT Reviewer")

    """
    GUI layout row/column design
    +--------------+---+---------------+
    |              |   |     label     |    0
    +              |   +---------------+
    |              |   |     select    |    1
    +      text    | s +---------------+
    |              |   |      f/u      |    2
    +              |   +-------+-------+
    |              |   | <prev | next> |    3
    +              +   +-------+-------+
    |              |   |       | unsc> |    4
    +--------------+---+-------+-------+
           0        1     2       3
    
    """

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    mainframe.columnconfigure(0, weight=80)
    mainframe.columnconfigure(1, weight=4)
    mainframe.columnconfigure(2, weight=10)
    mainframe.columnconfigure(3, weight=10)

    mainframe.rowconfigure(0, weight=18)
    mainframe.rowconfigure(1, weight=2)
    mainframe.rowconfigure(2, weight=2)
    mainframe.rowconfigure(2, weight=2)

    report_text = Text(mainframe, width=80, height=24)
    report_text.grid(row=0, column=0, rowspan=5, sticky=(N,S,E,W))
    report_scroll = ttk.Scrollbar(mainframe, orient=VERTICAL, command=report_text.yview)
    report_scroll.grid(row=0, column=1, rowspan=5, sticky=(N,S))
    report_text['yscrollcommand'] = report_scroll.set

    task_label = ttk.Label(mainframe, text="hello there")
    task_label_str = StringVar()
    task_label['textvariable'] = task_label_str
    task_label.grid(row=0, column=2, columnspan=2, sticky=N )

    radcat_entry = StringVar()
    radcat_combo = ttk.Combobox(mainframe, textvariable=radcat_entry, state='readonly')
    radcat_combo['values'] = ('', 'RADCAT1', 'RADCAT2', 'RADCAT3', 'RADCAT4', 'RADCAT4+3', 'RADCAT5', 'RADCAT5+3')
    radcat_combo.grid(row=1, column=2, sticky=(S), columnspan=2)
    radcat_combo.bind('<<ComboboxSelected>>', submit)

    # fu_entry = BooleanVar()
    # fu_chk = ttk.Checkbutton(mainframe, text='Follow up (RADCAT3)', variable=fu_entry,
    #                          onvalue=True, offvalue=False, command=submit)
    # fu_chk.grid(row=2, column=2, columnspan=2)

    prev_btn = ttk.Button(mainframe, text="< Back", command=go_prev)
    prev_btn.grid(row=3, column=2, sticky=(W,E))

    first_btn = ttk.Button(mainframe, text="<< First", command=go_first)
    first_btn.grid(row=4, column=2, sticky=(W,E) )

    next_btn = ttk.Button(mainframe, text="Next >", command=go_next)
    next_btn.grid(row=3, column=3, sticky=(W,E) )

    unscored_btn = ttk.Button(mainframe, text="Unscored >>", command=go_unscored)
    unscored_btn.grid(row=4, column=3, sticky=(W,E) )

    def key_callback(event):
        # logging.debug(event.keysym)
        if event.keysym == "1":
            radcat_combo.current(1)
            submit()
        elif event.keysym == "2":
            radcat_combo.current(2)
            submit()
        elif event.keysym == "3":
            radcat_combo.current(3)
            submit()
        elif event.keysym == "4":
            radcat_combo.current(4)
            submit()
        elif event.keysym == "5":
            radcat_combo.current(5)
            submit()
        elif event.keysym == "Right":
            go_next()
        elif event.keysym == "Left":
            go_prev()
        elif event.keysym == "space" and unscored_btn.instate(["!disabled",]):
            go_unscored()
        elif event.keysym == "0":
            go_first()

    mainframe.bind_all('<Key>', key_callback )

    go(0)


def parse_args():
    parser = argparse.ArgumentParser(prog=__prog__, description=__desc__)
    parser.add_argument('csv_fp', help="Fully qualified path to Montage `source.csv` file.")
    parser.add_argument('--verbose', '-v', help="Report match info on console", action='count')
    parser.add_argument('--version', action="version", version='%(prog)s {}'.format(__version__))
    opts = parser.parse_args()

    global fn, data_root
    data_root = os.path.split(opts.csv_fp)[0]
    fn = os.path.split(opts.csv_fp)[1]

    return opts


if __name__=="__main__":

    opts = parse_args()

    if opts.verbose >= 2:
        logging_level = logging.DEBUG
    if opts.verbose == 1:
        logging_level = logging.INFO
    else:
        logging_level = logging.WARN

    # Then just go ahead and put it in DEBUG anyway...
    logging.basicConfig(level=logging.DEBUG)

    # logging.debug(logging_level)
    load_data()

    # logging.debug(items)

    make_ui()
    root.mainloop()