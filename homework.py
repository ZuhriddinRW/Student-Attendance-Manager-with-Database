import psycopg2
from datetime import datetime


class Student :
    def __init__(self, name, surname, std_id) :
        self.name = name
        self.surname = surname
        self.std_id = std_id


class AttendanceSystem :
    def __init__(self) :
        self.students = []
        self.attendance = []
        self.conn = self.connect_db ()
        self.add_default_students ()

    def connect_db(self) :
        try :
            conn = psycopg2.connect (
                dbname="Attendance System",
                user="postgres",
                password="uniquepincode2026",
                host="localhost"
            )
            self.cur = conn.cursor ()
            self.cur.execute ( '''CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY, name TEXT, surname TEXT, std_id TEXT UNIQUE)''' )
            self.cur.execute ( '''CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY, std_id TEXT, date TEXT, status TEXT,
                UNIQUE(std_id, date))''' )
            conn.commit ()
            self.load_from_db ()
            print ( "Database connected!" )
            return conn
        except :
            print ( "Using memory only" )
            return None

    def load_from_db(self) :
        try :
            self.cur.execute ( "SELECT * FROM students" )
            for r in self.cur.fetchall () :
                self.students.append ( Student ( r[1], r[2], r[3] ) )

            self.cur.execute ( "SELECT * FROM attendance" )
            for r in self.cur.fetchall () :
                self.attendance.append ( {'std_id' : r[1], 'date' : r[2], 'status' : r[3]} )
        except :
            pass

    def save_to_db(self, query, params) :
        if self.conn :
            try :
                self.cur.execute ( query, params )
                self.conn.commit ()
            except :
                pass

    def add_default_students(self) :
        if self.students :
            return

        default = [
            ("Ali", "Valiyev", "STD001"), ("Aziza", "Karimova", "STD002"),
            ("Bobur", "Toshmatov", "STD003"), ("Dilnoza", "Rahimova", "STD004"),
            ("Eldor", "Abdullayev", "STD005"), ("Feruza", "Sherova", "STD006"),
            ("Jasur", "Alimov", "STD007"), ("Kamila", "Yusupova", "STD008"),
            ("Otabek", "Hasanov", "STD009"), ("Zarina", "Rustamova", "STD010")
        ]

        for name, surname, std_id in default :
            self.students.append ( Student ( name, surname, std_id ) )
            self.save_to_db ( "INSERT INTO students (name, surname, std_id) VALUES (%s,%s,%s)",
                              (name, surname, std_id) )
        print ( "10 students added!" )

    def show_students(self) :
        print ( "\n" + "=" * 50 + "\nSTUDENTS\n" + "=" * 50 )
        for i, s in enumerate ( self.students, 1 ) :
            print ( f"{i}. {s.name} {s.surname} ({s.std_id})" )

    def get_statuses(self, prompt) :
        att_input = input ( prompt ).strip ()
        if not att_input :
            return None

        att_list = [x.strip ().lower () for x in att_input.split ( ',' )]
        if len ( att_list ) != len ( self.students ) :
            print ( f"Error! Need {len ( self.students )} values, got {len ( att_list )}" )
            return None

        statuses = []
        for val in att_list :
            if val in ['true', 't', '1', 'yes', 'y'] :
                statuses.append ( "Present" )
            elif val in ['false', 'f', '0', 'no', 'n'] :
                statuses.append ( "Absent" )
            else :
                print ( f"Invalid value: {val}" )
                return None
        return statuses

    def save_attendance(self, date, statuses) :
        for s, status in zip ( self.students, statuses ) :
            self.attendance.append ( {'std_id' : s.std_id, 'date' : date, 'status' : status} )
            self.save_to_db ( "INSERT INTO attendance (std_id, date, status) VALUES (%s,%s,%s)",
                              (s.std_id, date, status) )

    def mark_attendance(self) :
        date = input ( "\nDate (YYYY-MM-DD) [today]: " ).strip () or datetime.now ().strftime ( "%Y-%m-%d" )

        if any ( a['date'] == date for a in self.attendance ) :
            print ( f"\nWarning: Attendance for {date} already exists!" )
            if input ( "1. Edit | 2. Cancel\nChoice: " ).strip () == "1" :
                self.edit_attendance_by_date ( date )
            return

        self.show_students ()
        print ( "\n" + "=" * 50 + "\nEnter: True,False,True,... (comma separated)\n" + "=" * 50 )

        statuses = self.get_statuses ( f"Attendance for {len ( self.students )} students: " )
        if not statuses :
            return

        print ( "\n=== Preview ===" )
        for i, (s, st) in enumerate ( zip ( self.students, statuses ), 1 ) :
            print ( f"{i}. {s.name} {s.surname} - {st} [{'+' if st == 'Present' else '-'}]" )

        if input ( "\nSave? (y/n): " ).lower () == 'y' :
            self.save_attendance ( date, statuses )
            present = sum ( 1 for st in statuses if st == "Present" )
            print (
                f"\n{'=' * 50}\nAttendance saved!\nPresent: {present} | Absent: {len ( statuses ) - present}\n{'=' * 50}" )

    def edit_attendance(self) :
        if not self.attendance :
            print ( "No records" )
            return

        choice = input ( "\n1. Edit by date | 2. Edit by student\nChoice: " ).strip ()
        date = input ( "\nDate (YYYY-MM-DD) [today]: " ).strip () or datetime.now ().strftime ( "%Y-%m-%d" )

        if choice == "1" :
            self.edit_attendance_by_date ( date )
        elif choice == "2" :
            self.edit_attendance_by_student ()

    def edit_attendance_by_date(self, date) :
        records = [a for a in self.attendance if a['date'] == date]
        if not records :
            print ( f"No records for {date}" )
            return

        print ( f"\n=== Current Attendance {date} ===" )
        for i, s in enumerate ( self.students, 1 ) :
            r = next ( (r for r in records if r['std_id'] == s.std_id), None )
            if r :
                print ( f"{i}. {s.name} {s.surname} - {r['status']} [{'+' if r['status'] == 'Present' else '-'}]" )

        print ( "\n" + "=" * 50 + "\nEnter new attendance: True,False,True,...\n" + "=" * 50 )
        statuses = self.get_statuses ( f"New attendance for {len ( self.students )} students: " )

        if statuses and input ( "\nUpdate? (y/n): " ).lower () == 'y' :
            self.attendance = [a for a in self.attendance if a['date'] != date]
            self.save_to_db ( "DELETE FROM attendance WHERE date = %s", (date,) )
            self.save_attendance ( date, statuses )
            print ( "\nAttendance updated!" )

    def edit_attendance_by_student(self) :
        self.show_students ()
        idx = int ( input ( "\nSelect student: " ) ) - 1
        if idx < 0 or idx >= len ( self.students ) :
            return

        s = self.students[idx]
        records = [a for a in self.attendance if a['std_id'] == s.std_id]
        if not records :
            print ( f"No records for {s.name} {s.surname}" )
            return

        print ( f"\n=== {s.name} {s.surname} Records ===" )
        for i, r in enumerate ( records, 1 ) :
            print ( f"{i}. {r['date']} - {r['status']} [{'+' if r['status'] == 'Present' else '-'}]" )

        rec_idx = int ( input ( "\nSelect record: " ) ) - 1
        if rec_idx < 0 or rec_idx >= len ( records ) :
            return

        old = records[rec_idx]
        new_status = "Present" if input ( "\n1. Present | 2. Absent\nNew status: " ).strip () == "1" else "Absent"

        for a in self.attendance :
            if a['std_id'] == old['std_id'] and a['date'] == old['date'] :
                a['status'] = new_status
                break

        self.save_to_db ( "UPDATE attendance SET status=%s WHERE std_id=%s AND date=%s",
                          (new_status, old['std_id'], old['date']) )
        print ( f"\nUpdated: {old['date']} - {new_status}" )

    def clear_attendance(self) :
        if not self.attendance :
            print ( "No records" )
            return

        print ( "\nWARNING: This will delete records!" )
        choice = input ( "1. Clear all | 2. By date | 3. By student | 0. Cancel\nChoice: " ).strip ()

        if choice == "1" :
            if input ( "\nType 'YES' to confirm: " ) == "YES" :
                self.attendance = []
                self.save_to_db ( "DELETE FROM attendance", () )
                print ( "All cleared!" )

        elif choice == "2" :
            date = input ( "\nDate (YYYY-MM-DD): " ).strip ()
            if date and any ( a['date'] == date for a in self.attendance ) :
                if input ( f"\nDelete records from {date}? (y/n): " ).lower () == 'y' :
                    self.attendance = [a for a in self.attendance if a['date'] != date]
                    self.save_to_db ( "DELETE FROM attendance WHERE date=%s", (date,) )
                    print ( f"Attendance for {date} cleared!" )

        elif choice == "3" :
            self.show_students ()
            idx = int ( input ( "\nSelect student: " ) ) - 1
            if idx >= 0 and idx < len ( self.students ) :
                s = self.students[idx]
                if input ( f"\nDelete records for {s.name} {s.surname}? (y/n): " ).lower () == 'y' :
                    self.attendance = [a for a in self.attendance if a['std_id'] != s.std_id]
                    self.save_to_db ( "DELETE FROM attendance WHERE std_id=%s", (s.std_id,) )
                    print ( f"Attendance for {s.name} {s.surname} cleared!" )

    def view_attendance(self) :
        if not self.attendance :
            print ( "No records" )
            return

        choice = input ( "\n1. By student | 2. By date\nChoice: " ).strip ()
        if choice == "1" :
            self.view_by_student ()
        elif choice == "2" :
            self.view_by_date ()

    def view_by_student(self) :
        self.show_students ()
        idx = int ( input ( "\nSelect student: " ) ) - 1
        if idx < 0 or idx >= len ( self.students ) :
            return

        s = self.students[idx]
        records = [a for a in self.attendance if a['std_id'] == s.std_id]
        if not records :
            print ( f"No records for {s.name} {s.surname}" )
            return

        print ( f"\n=== {s.name} {s.surname} ===" )
        for r in records :
            print ( f"{r['date']} - {r['status']} [{'+' if r['status'] == 'Present' else '-'}]" )

        present = sum ( 1 for r in records if r['status'] == "Present" )
        print ( f"\nTotal: {len ( records )} | Present: {present} | Rate: {present / len ( records ) * 100:.1f}%" )

    def view_by_date(self) :
        date = input ( "\nDate (YYYY-MM-DD) [today]: " ).strip () or datetime.now ().strftime ( "%Y-%m-%d" )
        records = [a for a in self.attendance if a['date'] == date]
        if not records :
            print ( f"No records for {date}" )
            return

        print ( f"\n=== Attendance {date} ===" )
        for r in records :
            s = next ( (st for st in self.students if st.std_id == r['std_id']), None )
            if s :
                print ( f"{s.name} {s.surname} - {r['status']} [{'+' if r['status'] == 'Present' else '-'}]" )

        present = sum ( 1 for r in records if r['status'] == "Present" )
        print ( f"\nPresent: {present}/{len ( records )} ({present / len ( records ) * 100:.1f}%)" )

    def statistics(self) :
        if not self.attendance :
            print ( "No records" )
            return

        total = len ( self.attendance )
        present = sum ( 1 for a in self.attendance if a['status'] == "Present" )

        print ( "\n" + "=" * 50 + "\nSTATISTICS\n" + "=" * 50 )
        print ( f"Total: {total}\nPresent: {present} ({present / total * 100:.1f}%)" )
        print ( f"Absent: {total - present} ({(total - present) / total * 100:.1f}%)" )

        stats = {}
        for s in self.students :
            recs = [a for a in self.attendance if a['std_id'] == s.std_id]
            if recs :
                stats[s] = sum ( 1 for r in recs if r['status'] == "Present" ) / len ( recs ) * 100

        print ( "\nTop Students:" )
        for i, (s, rate) in enumerate ( sorted ( stats.items (), key=lambda x : x[1], reverse=True )[:5], 1 ) :
            print ( f"{i}. {s.name} {s.surname} - {rate:.1f}%" )

    def close_db(self) :
        if self.conn :
            try :
                self.cur.close ()
                self.conn.close ()
                print ( "Database closed!" )
            except :
                pass


def main() :
    system = AttendanceSystem ()

    while True :
        print ( "\n" + "=" * 40 + "\nATTENDANCE SYSTEM\n" + "=" * 40 )
        print ( "1. View students\n2. Mark attendance\n3. View attendance" )
        print ( "4. Edit attendance\n5. Clear attendance\n6. Statistics\n0. Exit" )
        print ( "-" * 40 )

        choice = input ( "Choice: " ).strip ()

        if choice == "1" :
            system.show_students ()
        elif choice == "2" :
            system.mark_attendance ()
        elif choice == "3" :
            system.view_attendance ()
        elif choice == "4" :
            system.edit_attendance ()
        elif choice == "5" :
            system.clear_attendance ()
        elif choice == "6" :
            system.statistics ()
        elif choice == "0" :
            system.close_db ()
            print ( "Goodbye!" )
            break


if __name__ == "__main__" :
    main ()
