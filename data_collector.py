from pyyoutube import Client
from youtubesearchpython import *
from db import *


def get_comments(youtube, video_id):
    res = []
    video_response = youtube.commentThreads.list(part='snippet', video_id=video_id).to_dict()
    while "nextPageToken" in video_response and len(res) < 3000:
        for item in video_response['items']:
            # comment = item['snippet']['topLevelComment']
            # text = comment['snippet']['textDisplay']
            # comments.append(text)
            res.append(item['snippet'])
            # print(comments[-1]['topLevelComment']['snippet']['textDisplay'])
        video_response = youtube.commentThreads.list(part='snippet',
                                                     video_id=video_id,
                                                     pageToken=video_response['nextPageToken']).to_dict()
    return res


def count_comments(comments, stop=True):
    n = len(comments.comments['result'])
    while (n < 1000 or not stop) and comments.hasMoreComments:
        try:
            comments.getNextComments()
        except:
            break
        n += len(comments.comments['result'])
        print(n)
    return n + (comments.hasMoreComments > 0) * stop


def get_video_data(video_id):
    return


def collect_data(start=0):
    db_size = 0
    search = CustomSearch('', VideoSortOrder.viewCount)
    # search = VideosSearch('')
    while db_size < 1000:
        for vid in search.result()['result']:
            video_id = vid['id']
            print(db_size, video_id)
            try:
                comments = Comments(video_id)
            except:
                continue
            comment_cnt = count_comments(comments)
            if comment_cnt >= 1000:
                videos.append((video_id, comment_cnt))
                db_size += 1
            else:
                print(f"only ({comment_cnt}) comments...")
        print(db_size / 10, "%")
        with open('data', 'w') as f:
            print(videos, file=f)
        search.next()
    print("Search is completed!")
    return


with open('data286', 'r') as f:
    videos = eval(f.read())

con = sqlite3.connect("youtube.db")
cur = con.cursor()

with open("key", "r") as f:
    API_KEY = f.read()
client = Client(api_key=API_KEY)


for i in range(len(videos)):
    video_id = videos[i][0]
    vid = Video.get(video_id, mode = ResultMode.json, get_upload_date=True)
    # comments = Comments(video_id)

    date = vid['publishDate']
    date = int(date[0:4] + date[5:7] + date[8:10])
    preview = vid['thumbnails'][-2]['url']

    comments = get_comments(client, video_id)
    n = len(comments)
    for k in range(n):
        msg = comments[k]['topLevelComment']
        msg_id = msg['id']
        text = msg['snippet']['textDisplay']
        msg_date = msg['snippet']['publishedAt']
        try:
            user_id = msg['snippet']['authorChannelId']['value']
        except:
            continue
        username = msg['snippet']['authorDisplayName']
        pfp = msg['snippet']['authorProfileImageUrl']
        pfp = pfp[:pfp.rfind('=')]
        cur.execute(f"INSERT INTO messages(id, text, date, user_id, video_id)\
                      VALUES (?, ?, ?, ?, ?)", (msg_id, text, msg_date, user_id, video_id))
        cur.execute(f"INSERT INTO users(id, name, username, pfp)\
                      VALUES (?, NULL, ?, ?)", (user_id, username, pfp))
    cur.execute(f"INSERT INTO videos(id, date, preview, msg_cnt) VALUES ('{video_id}', {date}, '{preview}', {n})")
    con.commit()
    print(i, video_id)
