GUID Mint
=========

Unique, deterministic study ids, psuedonyms, and pseudodobs for all!

Usage
-----

As a Python library:

.. code:: python

   >>> from diana.utils.guid import GUIDMint
   >>> GUIDMint().get_sham_id( name="MERCK^DEREK^L", age=30 )
   {
     'BirthDate': datetime.date(1988, 11, 20),
     'ID': 'VXNQHHN523ZQNJFIY3TXJM4YXABTL6SL',
     'Name': ['VANWASSENHOVE', 'XAVIER', 'N'],
     'TimeOffset': datetime.timedelta(-47, 82822)
   }

From ``diana-cli``:

.. code:: yaml

   $ diana-cli guid "MERCK^DEREK^L" --age 30
   Generating GUID
   ------------------------
   WARNING:GUIDMint:Creating non-reproducible GUID using current date
   {'birth_date': '19881120',
    'id': 'VXNQHHN523ZQNJFIY3TXJM4YXABTL6SL',
    'name': 'VANWASSENHOVE^XAVIER^N',
    'time_offset': '-47 days, 23:00:22'}

Or from the ``diana-REST`` api:

.. code:: yaml

   $ curl -X GET "http://localhost:8080/v1.0/guid?name=MERCK%5EDEREK%5EL&age=30&sex=U"
   {
     "birth_date": "19881120",
     "id": "VXNQHHN523ZQNJFIY3TXJM4YXABTL6SL",
     "name": "VANWASSENHOVE^XAVIER^N",
     "time_offset": "-47 days, 23:00:22"
   }

Algorithm
---------

The GUID mint generates a unique and reproducibly generated tag against
any consistent set of object-specific variables:

-  name (or any string)
-  gender ({m, f, u})
-  birth date (or age + reference date)

Global Unique ID
~~~~~~~~~~~~~~~~

Generation Algorithm:

1. Given ``name``, ``gender``, and ``dob`` parameters. Depending on the
   available data, ``name`` may be a patient name, an MRN, or a subject
   ID, or any unique combination of those elements. If ``dob`` is
   unavailable, an ``age`` parameter and a ``reference_date`` may be
   substituted. If no reference date is provided the algorithm defaults
   to today and the GUID will be unreproducible.
2. A unique key is generated based on the alphabetically sorted elements
   of ``name``, ``dob``, and ``gender``.
3. The `sha256 <http://en.wikipedia.org/wiki/Secure_Hash_Algorithm>`__
   hash of the key is computed and the result is encoded into
   `base32 <http://en.wikipedia.org/wiki/Base32>`__
4. If the first three characters are not alphabetic, the value is
   rehashed until it is (for pseudonym generation)

Pseudonym Generation
~~~~~~~~~~~~~~~~~~~~

| It is often useful to replace the subject name with something more
  natural than a GUID.
| Any string beginning with at least 3 (capitalized) alphabetic
  characters can be used to reproducibly generate a `“John
  Doe” <http://en.wikipedia.org/wiki/John_Doe>`__ style placeholder name
  in DICOM patient name format (``last^first^middle``)\ `1 <>`__. This
  is very useful for alphabetizing subject name lists similarly to their
  ID while still allowing for anonymized data sets to be referenced
  according to memorable names.

Generation Algorithm:

1. Given a ``guid`` and ``gender`` (M,F,U) (optional, defaults to U)
2. Using the ``guid`` as a random seed, a gender-appropriate first name
   and gender-neutral family name is selected from a uniform
   distribution taken from the US census
3. The result is returned in DICOM patient name format.

The default name map can be easily replaced to match your fancy
(Shakespearean names, astronauts, children book authors). With slight
modification, a DICOM patient name with up to 5 elements could be
generated (i.e., in ``last^first^middle^prefix^suffix`` format).

Approximate Date-of-Birth
~~~~~~~~~~~~~~~~~~~~~~~~~

As with pseudonyms, it can be useful to maintain a valid date-of-birth
(dob) in de-identified metadata. Using a GUID as a seed, any dob can be
mapped to a random nearby date for a nearly-age-preserving anonymization
strategy. This is useful for keeping an approximate patient age
available in a data browser.

Generation Algorithm:

1. Given a GUID and a ``dob`` parameter
2. Using the ``guid`` as a random seed, a random integer between -90 and
   +90 is selected
3. The original ``dob`` + the random delta in days is returned

Study-Time Offset
~~~~~~~~~~~~~~~~~

In order to keep study date-times in the correct order, a similar
algorithm is used to generate a days and seconds time offset that will
keep the study at roughly the same time of day (within an hour) while
offseting the study date up to +/-90 days.

Acknowledgements
----------------

-  Inspired in part by the
   `NDAR <https://ndar.nih.gov/ndarpublicweb/tools.html>`__ and
   `FITBIR <https://fitbir.nih.gov>`__ GUID schema.
-  Placeholder names inspired by the `Docker names
   generator <https://github.com/docker/docker/blob/master/pkg/namesgenerator/names-generator.go>`__

License
-------

`MIT <http://opensource.org/licenses/mit-license.html>`__
