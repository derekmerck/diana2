Diana-Plus
=================

Routines for pixel-based image post-processing that require numpy, scikit-learn, or pytorch.


Measure Scout
--------------

Estimates patient dimensions from CT localizer images for size-specific dose estimation.

Returns image orientation and estimated distance in centimeters.

```python
>>> from dxpl import MeasureScout
>>> d = DcmDir("my_dir").get("scout.dcm")
>>> d.MeasureScout()
("AP", 29.2)
```

Estimate Bone Age
--------------

Estimates the developmental age of a subject from a left-hand radiograph using Pan's classifier.  

Returns estimated age in in years and months.

```python
>>> from dxpl import BoneAge
>>> d = DcmDir("my_dir").get("ba.dcm")
>>> d.BoneAge()
(7, 10)
```

Detect Chest Pathology
--------------

Estimates probability that a (PA) chest radiograph shows pathology using Pan's classifier.


Detect Head Bleed
--------------

Estimates probability that a CT brain scan shows a bleed using Pan's classifier.


Findings Priority
--------------

Estimates a priority level and follow up requirement for report text using Zhang's classifier.

