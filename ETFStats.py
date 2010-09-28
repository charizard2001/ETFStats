# :TODO: Remove 2010 and add a constant.
class ETFStats:
    """ Klasa koja omogucava jednostavno koristenje podataka sa zamgera u svrhu
    racunanja prosjeka studenata ETFSa i jos nekih stvari. """
    # Static member
    zamger_kodovi_predmeta = [
            [40, 12, 44, 20, 1],    # 1. Semestar
            [71, 129, 128, 13, 2],  # 2. Semestar
            [42, 4, 43, 11, 9, 10, 63, 35, 60, 62, 52, 36, 14, 61, 51,
                37, 15, 45, 49, 38, 29, 180, 64, 46, 16, 57, 34, ],   # 3.
            [67, 73, 104, 105, 72, 106, 107, 22, 69, 81, 85, 82, 68,
                86, 88, 87, 84, 83, 77, 65, 91, 92, 76, 89, 90, 93,
                74, 30, 119, 120, 117, 121, 78, 118],                 # 4.
            [8, 41, 179, 130, 23, 28, 217, 7, 6, 24, 32, 58, 25, 178,
                21, 55, 33, 177, 54, 59, 133, 47, 18, 132, 56, 48,
                50, 26, 53, 27, 135, 17, 134, 19, 39],                # 5.
            [112, 115, 113, 111, 114, 116, 108, 110, 109, 131, 96, 31,
                70, 97, 95, 94, 131, 98, 80, 101, 99, 100, 103, 66,
                102, 131, 125, 123, 122, 75, 126, 124, 127, 131]      # 6.
    ]
    def __init__(self, students_file):
        self.students_file = students_file
        self.godina = self.__get_godina()
    def __get_godina(self):
        import linecache
        return int(linecache.getline(self.students_file, 1).split()[1])
    def BrojIndeksa(self, ime_prezime):
        """ Pretrazuje self.students_file po imenu i vraca broj indeksa prvog studenta koji
        ima odgovarajuce ime ili prezime. """
        grupa = 1
        with open(self.students_file, encoding='utf-8') as st_file:
            for line in st_file:
                line = line.strip()
                if line == '--':            # Separator grupa
                    grupa += 1
                else:
                    try:
                        ime, prezime, indeks = line.split()
                    except:
                        pass
                    else:
                        if ime in ime_prezime.split() or prezime in ime_prezime.split():
                            print(ime, prezime, grupa, indeks)
                            return indeks
        return None

    def FilterByNumberFailed(self, max_failed):
        """ Vraca listu studenata koji su polozili najmanje min_polozio predmeta. """
        # Ako trazimo nekoga ko je polozio vise od ukupnog broja predmeta
        lista = []
        with open(self.students_file, encoding='utf-8') as st_file:
            for line in st_file:
                try:
                    ime, prezime, indeks = line.split()
                    prosjek, polozio, nije_polozio, smjer = self.CalculateAverage(indeks)
                    if max_failed >= nije_polozio:
                        lista.append((ime + ' ' + prezime, prosjek, polozio, nije_polozio, smjer))
                except:
                    pass
        return lista
    def SortirajPoProsjeku(self, output_file_name='sortirani'):
        pass
    @staticmethod
    def GetCourseName(file_name):
        with open(file_name, 'r', encoding='utf-8') as a_file:
            for line in a_file:
                line = line.strip()
                if line[:4] == '<h1>':      # U <h1> se nalazi ime predmeta
                    return line.strip('<h1>').strip('</')

    # Funkcija treba bolje ime!  Sada radi mnogo vise od samo CalcAvg.
    def CalculateAverage(self, indeks, report_predmete=False):
        """ Funkcija vraca prosjek, broj polozenih, broj nepolozenih predmeta
        i smjer studenta sa brojem indeksa indeks.  Ako je flag report_predmete
        True, onda ispisuje ocjene studenta iz svih predmeta. """
        # Predpostavljamo da je file u trenutnom radnom direktoriju
        search_for = '<td>' + str(indeks) + '</td>'

        suma_ocjena = 0
        nepolozeni_predmeti = set()
        polozeni_predmeti = set()
        for godina in range(self.godina, 2010):
            if report_predmete:
                print()
            proslo_semestara = (godina - self.godina + 1) * 2
            for semestar in ETFStats.zamger_kodovi_predmeta[:proslo_semestara]:
                for course in semestar:
                    if course in polozeni_predmeti:
                        continue
                    # Provjeri da li je polozen predmet u godini godina
                    file_name = str(course) + '-' + str(godina)[-2:]
                    with open(file_name, encoding='utf-8') as a_file:
                        found = False
                        prev_line = None
                        for line in a_file:
                            line = line.strip()
                            if found:
                                if line == '</tr>':        # Linija poslije ocjene!
                                    try:
                                        ocjena = int(prev_line.strip('</td>'))
                                    except:
                                        ocjena = 'Nije polozio'
                                        nepolozeni_predmeti.add(course)
                                    else:
                                        suma_ocjena += ocjena
                                        if course in nepolozeni_predmeti:
                                            nepolozeni_predmeti.remove(course)
                                        polozeni_predmeti.add(course)
                                    if report_predmete:
                                        print(ETFStats.GetCourseName(file_name), '--', ocjena, str(godina) + '/' + str(godina + 1))
                                    break
                                else:
                                    prev_line = line
                                    continue
                            elif line == search_for:
                                found = True
                                prev_line = line
        if len(polozeni_predmeti) != 0:
            return (suma_ocjena / len(polozeni_predmeti),
                    len(polozeni_predmeti),
                    len(nepolozeni_predmeti),
                    ETFStats.IdentificirajSmjer(polozeni_predmeti.union(nepolozeni_predmeti)))
        else:
            return 'Nista', 0, nije_polozio
    def FetchCourseData(self, course_code, godina=None):
        """ Gets the html files from zamger with students' scores """
        if godina == None:
            godina = self.godina
        import httplib2
        # Odrediti ag -- godina za koju trazimo podatke o kursu
        # Predstavlja broj godina od godine kad se poceo korisiti zamger?
        # U svakom slucaju ide od 1 na vise
        OFFSET = 2004       # za godinu (prva godina za koju imaju podaci u
                            #            zamgeru je 2005/2006)
        semestar_predmeta = None
        for i, semestar in enumerate(ETFStats.zamger_kodovi_predmeta):
            if course_code in semestar:
                semestar_predmeta = i
                break
        if semestar_predmeta == None:
            raise Exception("Kod predmeta " + str(course_code) + " nije pronadjen.")
        ag = godina - OFFSET
        if ag <= 0:
            raise Exception("Nepostojeca skolska godina.")
        # Query URL na zamgeru
        A_URL = 'https://zamger.etf.unsa.ba/?sta=izvjestaj/predmet&skrati=da&predmet={0}&ag={1}'
        # Novi Http objekat gdje je cache directory = .cache
        print(course_code, end='...')
        h = httplib2.Http('.cache')
        response, content = h.request(A_URL.format(course_code, ag))
        if response.status == 200:      # OK
            with open(str(course_code) + '-' + str(godina)[-2:], 'w',
                    encoding='utf-8') as a_file:
                a_file.write(content.decode('utf-8'))
            print('OK ({0})'.format(response.status))
        else:
            print('Error ({0})'.format(response.status))
            
    def UpdateAllCourseData(self):
        for godina in range(self.godina, 2010):
            print(godina)
            print('----')
            proslo_semestara = (godina - self.godina + 1) * 2
            for semestar in ETFStats.zamger_kodovi_predmeta[:proslo_semestara]:
                for course in semestar:
                    self.FetchCourseData(course, godina)
        print('Finished.')

    @staticmethod
    def IdentificirajSmjer(kodovi_predmeta):
        """ Prima set kodova predmeta i vraca naziv smjera koji odgovara tim
        predmetima. """
        karakteristicni = { (42, 4, 43, 11, 9): 'RI',
                            (51, 37, 15, 45, 49): 'EE',
                            (38, 29, 34, 16, 57): 'TK',
                            (35, 14, 61, 36, 52): 'AE',
        }
        for lista in karakteristicni:
            total = 0
            for i in lista:
                if i in kodovi_predmeta:
                    total += 1
            if total > 2:
                return karakteristicni[lista]
        return 'WTFGodina'

    def MaksimalanBrojPredmeta(self, smjer):
        if 2010 - self.godina == 1:
            return 10
        elif 2010 - self.godina == 2:
            if smjer == 'EE':
                return 21
            else:
                return 22
        elif 2010 - self.godina == 3:
            pass        # :TODO: Add support for older peeps

def Ocistili(file_name):
    Stats = ETFStats('indeksi')
    lista = Stats.FilterByNumberFailed(0)
    with open(file_name, 'w', encoding='utf-8') as a_file:
        for indeks, record in enumerate(lista):
            a_file.write(str(indeks + 1) + '. ' + 
                    record[0] + ' ' + str(record[1]) + ' ' + record[4] + '\r\n')
    return len(lista)

if __name__ == '__main__':
    print(Ocistili('ocistili.txt'))

