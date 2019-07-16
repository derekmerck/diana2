import os
import pydicom
import zipfile

'''
Pre-req: grassroots dicom for decompression compatibility
conda install -c conda-forge gdcm
Installation successful if import gcdm works, but explicit import unnecessary
'''

directory = r"D:\Brown\Research\Raw_Data\tirads"
write_to = r"D:\Brown\Research\Raw_Data\tirads\cropped"


# Traverse subdirectories
def list_files(dir):
    r = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            if "PR" in name:
                print("Skipping: {}".format(name))
                continue
            r.append(os.path.join(root, name))
    return r


count = 0
for i, zipfn in enumerate(os.listdir(directory)):
    if zipfn.endswith(".zip"):
        count += 1
        print("Processing #{}: {}".format(count, zipfn))
        if not os.path.exists(os.path.join(directory, zipfn.split(".zip")[0])):
            file_path = os.path.join(directory, zipfn)
            print("Unzipping {}...".format(file_path))
            zip_ref = zipfile.ZipFile(file_path, 'r')
            zip_ref.extractall(os.path.join(directory, zipfn.split(".zip")[0]))
            zip_ref.close()

        print("Cropping .dcms...")
        for j, filename in enumerate(list_files(os.path.join(directory, zipfn.split(".zip")[0]))):
            dest_path = os.path.join(write_to, zipfn.split(".zip")[0], os.path.basename(os.path.normpath(filename)))
            if os.path.exists(dest_path):
                continue

            ds = pydicom.dcmread(filename)
            try:
                ds.decompress()
            except OSError:
                print("Skipped file")
                continue

            # Crop PHI at top of images
            num_rows_removed = 50
            try:
                if len(ds.pixel_array.shape) == 4:
                    if ds.Rows == ds.pixel_array.shape[1]:
                        ds.PixelData = ds.pixel_array[:, num_rows_removed:, :, :].tobytes()
                    else:
                        raise NotImplementedError
                if len(ds.pixel_array.shape) == 3:
                    if ds.Rows == ds.pixel_array.shape[0]:
                        ds.PixelData = ds.pixel_array[num_rows_removed:, :, :].tobytes()
                    elif ds.Rows == ds.pixel_array.shape[1]:
                        ds.PixelData = ds.pixel_array[:, num_rows_removed:, :].tobytes()
                elif len(ds.pixel_array.shape) == 2:
                    if ds.Rows == ds.pixel_array.shape[0]:
                        ds.PixelData = ds.pixel_array[num_rows_removed:, :].tobytes()
                    else:
                        raise NotImplementedError
                else:
                    print(filename)
                    raise NotImplementedError
            except ValueError:
                print("Pixel data length mismatch. Skipping {}".format(filename))
                continue
            ds.Rows = ds.Rows - num_rows_removed  # adjust header field accordingly

            if not os.path.exists(os.path.join(write_to, zipfn.split(".zip")[0])):
                os.mkdir(os.path.join(write_to, zipfn.split(".zip")[0]))
            ds.save_as(dest_path)
