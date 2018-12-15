import subprocess, tempfile, logging


def ok_to_compress( data ):
    # Read header and determine if there are pixels or not
    return True


def compress_dicom( data ):

    if not ok_to_compress( data ):
        return

    try:
        with tempfile.NamedTemporaryFile() as f:
            f.write(data)

            with tempfile.NamedTemporaryFile() as g:
                subprocess.call(['gdcmconv', '-U', '--j2k', f.name, g.name])
                data = g.read()

    except Exception:
        logging.warning("Could not compress DICOM data.")
        raise TypeError

    return data
