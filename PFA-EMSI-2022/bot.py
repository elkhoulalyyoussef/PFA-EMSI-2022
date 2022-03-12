import discord
import pickle
import pandas as pd
import datetime
import nltk
####### email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

########

f = open('my_classifier.pickle', 'rb')
classifier = pickle.load(f)
f.close()

TOKEN = 'OTUxNDI4NjcwMjA2MTE1ODYx.YinU_w.4ObZx_hUz_GMB3MDF8kIb_sdNlE'
server_name = 'Serveur PFE'

client = discord.Client()

channels = {
    "id": [],
    "name": []
}
channel_names = []
author = []
message = []
created_at = []
pos_neg = []
realtime = False


async def send_mail(toaddr=None):
    fromaddr = "omarbgali@gmail.com"
    if toaddr is None:
        toaddr = "elkhoulalyy@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Report discord:" + str(datetime.datetime.now())
    total = len(pos_neg);
    pos = len([p for p in pos_neg if p == "Positive"])
    neg = len([n for n in pos_neg if n == "Negative"])
    posT = f"{((pos * 100) / total):.2f}"
    negT = f"{((neg * 100) / total):.2f}"
    body = "ToTal : " + str(total) + "\n" \
                                     "Positive messages :" + str(pos) + " ==> " + str(posT) + "%\n" \
                                                                                              "Negative messages :" + str(
        neg) + " ==> " + str(negT) + "%\n" \
                                     "and please check the discord's server report fro  " + server_name + " from " + str(
        client.user)
    msg.attach(MIMEText(body, 'plain'))

    filename = "Report.csv"

    attachment = open(filename, "rb")

    p = MIMEBase('application', 'octet-stream')

    p.set_payload((attachment).read())

    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(p)

    s = smtplib.SMTP('smtp.gmail.com', 587)

    s.starttls()

    s.login(fromaddr, "123@OMAR")

    text = msg.as_string()

    s.sendmail(fromaddr, toaddr, text)

    s.quit()


def extract_features(word_list):
    return dict([(word, True) for word in word_list])


async def msgByChannel(channelId, limit):
    channel = client.get_channel(int(channelId))
    messages = await channel.history(limit=limit).flatten()
    for msg in messages:
        if msg.author != client.user and msg.content != "!real_time" and msg.content.startswith("!report") == False:
            channel_names.append(channel.name)
            author.append(msg.author)
            message.append(msg.content)
            created_at.append(msg.created_at)
            probdist = classifier.prob_classify(extract_features(msg.content.split()))
            pos_neg.append(probdist.max())


async def Report(information):
    channel_names.clear()
    author.clear()
    message.clear()
    created_at.clear()
    pos_neg.clear()
    info = information.content.split()
    limit = None
    if len(info) == 2 or len(info) == 3:
        limit = int(info[1])
    for channel in channels["id"]:
        await msgByChannel(channel, limit)
    report = pd.DataFrame(
        {
            "channel names": channel_names,
            "author": author,
            "message": message,
            "created at": created_at,
            "pos_neg": pos_neg
        },
        columns=["channel names", "author", "message", "created at", "pos_neg"]
    )
    report.sort_values(by=['channel names', 'pos_neg', 'created at'], inplace=True)
    report.to_csv('Report.csv', header=1, index=False)


@client.event
async def on_ready():
    # nltk.download('punkt')
    server = discord.utils.get(client.guilds, name=server_name)
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{server.name}(id: {server.id})'
    )
    for channel in server.channels:
        if str(channel.type) == "text":
            channels["name"].append(channel.name)
            channels["id"].append(channel.id)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!real_time"):
        global realtime
        realtime = not realtime
        await message.channel.send("Real time : " + str(realtime))
    if realtime and message.content.startswith("!real_time") == False:
        probdist = classifier.prob_classify(extract_features(message.content.split()))
        await message.channel.send(probdist.max())
    if message.content.startswith("!report"):
        await Report(message)
        m = message.content.split()

        if len(m) == 2:
            if m[1].endswith("@gmail.com"):
                await  send_mail(m[1])
            else:
                await send_mail()
        else:
            if len(m) == 3:
                await send_mail(m[2])
            else:
                await send_mail()


client.run(TOKEN)
