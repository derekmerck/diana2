import logging
import numpy as np
from sklearn.mixture import GaussianMixture as GMM
from diana.dixel import Dixel

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def MeasureScout(dixel: Dixel):
    """Measure AP and Lateral dimensions from DICOM localizer images for SSDE calculations"""

    # TODO: add a tag check for "LOCALIZER"

    pixel_spacing = dixel.pixel_spacing

    def measured_dimension(dixel):
        """
        Determine measurement dimension

        Could also try to use "degrees of azimuth" to identify lateral vs. AP:
          - 90 its a lateral scout -> PA dimension
          - 0,180 its an AP scout -> lateral dimension
        """

        orientation = dixel.tags["ImageOrientationPatient"]

        if orientation[0] * orientation[0] > 0.2:
            # This is a PA scout, which gives the lateral measurement
            measured_dim = 'LATERAL'
        elif orientation[1] * orientation[1] > 0.2:
            # This is a lateral scout, which gives the AP measurement
            measured_dim = 'AP'
        else:
            measured_dim = 'UNKNOWN'

        return measured_dim

    measured_dim = measured_dimension(dixel)

    # Setup pixel array data
    dcm_px = np.array(dixel.get_pixels(), dtype=np.float32)

    # Determine weighted threshold separating tissue/non-tissue attenuations
    # using a Gaussian Mixture Model
    thresh = np.mean(dcm_px[dcm_px>0])

    gmm = GMM(2).fit(dcm_px[dcm_px>0].reshape(-1,1))
    thresh = np.sum(gmm.weights_[::-1]*gmm.means_.ravel())

    # logging.debug(gmm.weights_[::-1])
    # logging.debug(gmm.means_.ravel())

    logging.debug("Threshold: {0}".format(thresh))

    # Compute avg width based on unmasked pixels
    mask = dcm_px > thresh

    px_counts = np.sum(mask,axis=1)
    avg_px_count = np.mean(px_counts[px_counts>0])
    # Across image spacing is 2nd component (axis 1)
    d_avg = avg_px_count * pixel_spacing[1] / 10;

    logging.debug("Average {0} width: {1}".format(measured_dim, d_avg))

    return (measured_dim, d_avg)

# Monkey patch
Dixel.MeasureScout = MeasureScout
