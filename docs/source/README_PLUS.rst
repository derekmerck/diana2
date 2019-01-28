Diana-Plus
==========

| Derek Merck
| derek_merck@brown.edu
| Rhode Island Hospital and Brown University
| Providence, RI

|Build Status| |Coverage Status| |Doc Status|

| Source: https://www.github.com/derekmerck/diana2
| Documentation: https://diana.readthedocs.io
| Image: https://cloud.docker.com/repository/docker/derekmerck/diana2

Routines for pixel-based image post-processing that require numpy,
scipy, scikit-learn, keras, and pytorch.

Measure Scout
-------------

Estimates patient dimensions from CT localizer images for size-specific
dose estimation. Basic algorithm is to use a 2-element Guassian mixture
model to find a threshold that separates air from tissue across breadth
of the image. Known to fail when patients do not fit in the scout field
of view.

Returns image orientation and estimated distance in centimeters. These
measurements can be converted into equivalent water volumes using
AAPM-published tables.

.. code:: text

    $ diana-plus ssde ../../tests/resources/scouts \
                      ct_scout_01.dcm ct_scout_02.dcm
    Measuring scout images
    ------------------------
    ct_scout_01.dcm (AP): 28.0cm
    ct_scout_02.dcm (LATERAL): 43.0cm

Estimate Bone Age
-----------------

Estimates the developmental age of a subject from a left-hand radiograph
using Pan's classifier.

Returns estimated age in in years and months.

.. code:: python

    >>> from dxpl import BoneAge
    >>> d = DcmDir("my_dir").get("ba.dcm")
    >>> d.BoneAge()
    (7, 10)

Detect Chest Pathology
----------------------

Estimates probability that a (PA) chest radiograph shows pathology using
Pan's classifier.

Pan, Ian, and Derek Merck. 2018. “MochiNets: Efficient Convolutional
Neural Networks for Binary Classification of Chest Radiographs.” Poster
presented at the Society for Imaging Informatics in Medicine (SIIM),
National Harbor, MD, May.

Detect Head Bleed
-----------------

Estimates probability that a CT brain scan shows a bleed using Pan's
classifier.

Pan, Ian, Owen Leary, Stefan Jung, Krishna Nand Keshavamurthy, Jason
Allen, David Wright, Lisa H. Merck, and Derek Merck. 2018. “Deep
Learning for Automatic Detection and Segmentation of Acute Epidural and
Subdural Hematomas in Head CT.” Research talk presented at the
Radiological Association of North America (RSNA), Chicago, IL, November
27.

Findings Priority
-----------------

Estimates a priority level and follow up requirement for report text
using Zhang's classifier.

Zhang, Yuhao, Ian Pan, Jonathan Movson, Derek Merck, and Curtis
Langlotz. 2018. “Deep Learning for the Automatic Detection of Urgent
Radiology Findings from Free-Text Radiology Reports.” Research talk
presented at the Radiological Society of North America (RSNA), Chicago,
IL, November 27.

License
-------

MIT

.. |Build Status| image:: https://travis-ci.org/derekmerck/diana2.svg?branch=master
   :target: https://travis-ci.org/derekmerck/diana2
.. |Coverage Status| image:: https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/derekmerck/diana2
.. |Doc Status| image:: https://readthedocs.org/projects/diana/badge/?version=master
   :target: https://diana.readthedocs.io/en/master/?badge=master
