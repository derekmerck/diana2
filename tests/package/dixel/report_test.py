import os, logging
from test_utils import find_resource
from diana.dixel import LungScreeningReport

def test_reader():

    path = find_resource("resources/reports")

    with open(os.path.join(path, "screening_rpt_anon.txt"), "r") as f:
        text = f.readlines()

    r = LungScreeningReport(text=text)

    logging.debug(r)

    logging.debug( r.current_smoker() )
    logging.debug( r.lungrads() )
    logging.debug( r.radcat() )
    logging.debug( r.years_since_quit() )

    assert( r.current_smoker() == True )
    assert( r.lungrads() == "2S" )
    assert( r.radcat() == ('3', True) )



if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_reader()

