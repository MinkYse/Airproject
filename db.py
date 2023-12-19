import psycopg2

from contextlib import closing


def get_data(ticket_no, lang):
    data = []
    with closing(psycopg2.connect(
            host="localhost",
            port=5432,
            database="demo",
            user="postgres",
            password="postgres"
    )) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT F.scheduled_departure, F.scheduled_arrival, F.departure_airport, F.arrival_airport
                        FROM Ticket_flights AS TF
                        INNER JOIN Flights AS F ON TF.flight_id = F.flight_id
                        WHERE ticket_no = %s;""", (ticket_no, ))
            row = cursor.fetchone()
            scheduled_departure = row[0]
            scheduled_arrival = row[1]
            departure_airport = row[2]
            arrival_airport = row[3]
        with conn.cursor() as cursor:
            cursor.execute("""SELECT airport_name->%s
                            FROM airports_data
                            WHERE airport_code = %s;""", (lang, departure_airport,))
            row = cursor.fetchone()
            departure_airport = row[0]
        with conn.cursor() as cursor:
            cursor.execute("""SELECT airport_name->%s
                            FROM airports_data
                            WHERE airport_code = %s;""", (lang, arrival_airport,))
            row = cursor.fetchone()
            arrival_airport = row[0]
    return [scheduled_departure, scheduled_arrival, departure_airport, arrival_airport]


if __name__ == '__main__':
    data = get_data('0005434861552', 'ru')
    print(data)