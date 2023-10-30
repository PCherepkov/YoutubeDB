import sqlite3


# TODO
# GUI DB Viewer
# Save images (userpics?)
# Search by time interval / video / word
# Sort
# Filter users by the numbder of comments
# Direct request


def video_table():
    # con = sqlite3.connect("youtube.db")
    # cur = con.cursor()
    cur.execute("CREATE TABLE videos(id varchar(30), date int, preview varchar(255), msg_cnt int)")
    cur.execute("CREATE TABLE messages(id varchar(30), text varchar(10000), date int, user_id varchar(30), video_id varchar(30))")
    cur.execute("CREATE TABLE users(id varchar(30), name varchar(30), username varchar(30), pfp varchar(255))")


def create_table():
    con = sqlite3.connect("youtube.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE comments(text, id, username, firstname, lastname, date)")

if __name__ == '__main__':
    con = sqlite3.connect("youtube.db")
    cur = con.cursor()

    if input("new db? y/n") == 'y':
        video_table()

    inp = input()
    while inp != "exit":
        try:
            res = cur.execute(inp)
        except Exception as e:
            print(e)
            inp = input()
            continue
        rows = cur.fetchall()
        for row in rows:
            print(row)
        inp = input()
    con.commit()
