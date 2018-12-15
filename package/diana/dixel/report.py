# Major differences are just in the RE's available.
#
# Can "cast" from RadiologyReport in a dixel.report like so
# > LungScreeningReport.current_smoker(my_dixel.report)

import re, logging
import attr

@attr.s
class RadiologyReport(object):
    text = attr.ib()

    def __str__(self):
        return self.text

    # Based on Lifespan/RIMI report template
    PHI_RE = re.compile(r'^.* MD.*$|^.*MRN.*$|^.*DOS.*$|^(?:.* )Dr.*$|^.* NP.*$|^.* RN.*$|^.* RA.*$|^.* PA.*$|^Report created.*$|^.*Signing Doctor.*$|^.*has reviewed.*$',re.M)
    FINDINGS_RE = re.compile(r'^.*discussed.*$|^.*nurse practitioner.*$|^.*physician assistant.*$|^.*virtual rad.*$', re.M | re.I)
    RADCAT_RE = re.compile(r'^.*RADCAT.*$', re.M)
    # https://stackoverflow.com/questions/16699007/regular-expression-to-match-standard-10-digit-phone-number
    PHONE_RE = re.compile(r'\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*', re.M)

    def anonymize(self):
        self.text = self.anonymized()

    def anonymized(self):
        # Explicitly decode it
        # raw_text = self.text.decode('utf-8', 'ignore')

        # Anonymize and blind to RADCAT
        anon_text = self.text
        anon_text = RadiologyReport.PHI_RE.sub(u"", anon_text, 0)
        anon_text = RadiologyReport.FINDINGS_RE.sub(u"", anon_text, 0)
        anon_text = RadiologyReport.RADCAT_RE.sub(u"", anon_text, 0)
        anon_text = RadiologyReport.PHONE_RE.sub(u"(555) 555-5555 ", anon_text, 0)

        # try:
        #     anon_text = anon_text.encode("utf-8", errors='ignore')
        # except UnicodeDecodeError:
        #     logging.error(anon_text)
        #     raise Exception('Cannot encode this report')

        anon_text = anon_text.rstrip() + "\n"

        return anon_text


    def radcat(self):
        radcat_pattern = re.compile(r'(?i)RADCAT(?: Grade)?:? ?R?(\d)')
        match = radcat_pattern.findall(self.text)

        if len(match)>0:
            radcat = match[0]
        else:
            logging.error(self.text)
            raise ValueError("No RADCAT score indicated!")

        radcat3_pattern = re.compile(r'(?i)RADCAT(?: Grade)?:? ?R?3')
        match = radcat3_pattern.findall(self.text)

        if len(match)>0:
            radcat3 = True
        else:
            radcat3 = False

        return (radcat, radcat3)

@attr.s
class MammographyReport(RadiologyReport):

    def birads(self):

        # "BI-RADS CATEGORY 4"

        birad_pattern = re.compile(r'(?i)BI[- ]RADS (?:CATEGORY )?([0-6])')
        match = birad_pattern.findall(self.text)

        if len(match)>0:
            return max(match)
        else:
            logging.error(self.text)
            raise ValueError("No BI-RADS score indicated!")

@attr.s
class BoneAgeReport(RadiologyReport):

    numbers = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11
    }

    def skeletal_age(self):

        text = self.text
        for k,v in BoneAgeReport.numbers.items():
            text = re.sub( r"\W{}\W".format(k), " {} ".format(v), text )

        # logging.debug(text)

        pattern = re.compile( r'(?:(?:[Bb]one)|(?:[Ss]keletal)) age[^\d]*(\d{1,2}) year[^\d]*(\d{1,2}) month' )
        match = pattern.findall(text)
        if len(match) > 0:
            return match[-1]  # Sometimes there is an addendum


    def chronological_age(self):

        text = self.text
        for k,v in BoneAgeReport.numbers.items():
            text = re.sub( r"\W{}\W".format(k), " {} ".format(v), text )

        pattern = re.compile( r'[Cc]hronologic[^\d]*(\d{1,2}) year[^\d]*(\d{1,2}) month' )
        match = pattern.findall(text)
        if len(match) > 0:
            return match[-1]


@attr.s
class LungScreeningReport(RadiologyReport):

    def is_annual(self):

        pattern = re.compile( r'no.*prior.*comparison')
        match = pattern.findall(self.text)
        return len(match) == 0

    def current_smoker(self):

        pattern = re.compile( r'(?<! not) (?:a )?([Cc]urrent)(?:ly)? (?!> no[nt])(smok)' )
        match = pattern.findall(self.text)
        return len(match) > 0

    def pack_years(self):

        pattern = re.compile(r"(?P<years>\d{1,4}).*(?=pack).*(?=y(?:ea)?r)")
        match = pattern.findall(self.text)

        if len(match) > 0:
            if max(match) > '0':
                return max(match)

    def years_since_quit(self):

        pattern = re.compile(r"(quit)[^\d]*(\d{1,4}) ?(months|years)?", re.IGNORECASE)
        match = pattern.findall(self.text)

        if len(match) > 0:
            # They quit
            tokens = match[0]
            units = tokens[2]

            if units == "years":
                # print("  Years: {}".format(tokens[1]))
                return tokens[1]
            elif units == "months":
                # print("  Months: {}".format(tokens[1]))
                return int( int(tokens[1])/12 + 1 )
            elif len(tokens[1]) > 3:
                # It's a date
                # print("  Date: {}".format(tokens[1]))
                return 2018-int(tokens[1])

    def lungrads(self):

        pattern = re.compile(r"(?:Lung-RADS)[^\d]*(\d[SC]*)")
        match = pattern.findall(self.text)

        if len(match)>0:
            return match[0]
