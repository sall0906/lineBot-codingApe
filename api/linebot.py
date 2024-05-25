from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, CarouselColumn,
                            CarouselTemplate, MessageAction, URIAction, ImageCarouselColumn, ImageCarouselTemplate,
                            ImageSendMessage, ButtonsTemplate)
import os
import requests
from bs4 import BeautifulSoup
import random

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def newest_movie():
    movie_info = []
    response = requests.get('https://movies.yahoo.com.tw/movie_thisweek.html')
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find_all('div', class_ = 'release_info_text')

    for index, info in enumerate(data[:10]):
        movie_name = info.find('div', class_ = 'release_movie_name').find('a').text
        movie_name = movie_name.strip()

        try:
            trailerUrl = soup.find_all('div',class_='release_btn color_btnbox')[index].find_all('a')[1]['href']
        except:
            trailerUrl = 'Yahoo電影沒有這部的預告片喔!'

        imgSrc = soup.find_all('div',class_='release_foto')[index].find('img')['data-src']
        temp = [movie_name, trailerUrl, imgSrc] #把一部電影的資訊整理成清單
        movie_info.append(temp) #再把清單加到movie_info
    return movie_info

def movie_rank(url):
    soup = BeautifulSoup(requests.get(url).text)
    first = soup.find('dl', class_ = 'rank_list_box').find('h2').text
    movie_rank = '第1名：' + first + '\n'

    movie_list = soup.find_all('div', class_ = 'rank_txt')
    for index, info in enumerate(movie_list):
        movie = info.text
        movie_rank += '第{}名：{}\n'.format(str(index + 2), movie)

    return movie_rank

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    if event.message.text == '新片':

        movie_info = newest_movie()
        #從movie_info大清單裡，挑三個
        movie_list = random.sample(movie_info, k = 3)

        movie_template = TemplateSendMessage(
            alt_text = 'movie template',
            template = ImageCarouselTemplate(
                columns = [
                    ImageCarouselColumn(
                        image_url = movie_list[0][2],
                        action = URIAction(
                            label = movie_list[0][0],
                            uri = movie_list[0][1])),

                    ImageCarouselColumn(
                        image_url = movie_list[1][2],
                        action = URIAction(
                            label = movie_list[1][0],
                            uri = movie_list[1][1])),

                    ImageCarouselColumn(
                        image_url = movie_list[2][2],
                        action = URIAction(
                            label = movie_list[2][0],
                            uri = movie_list[2][1]))
                ])
            )
        line_bot_api.reply_message(event.reply_token, movie_template)

    if event.message.text == '排行':
        button_template = TemplateSendMessage(
            alt_text = 'button template',
            template = ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/a5MK3cu.jpeg',
                title='Yahoo電影排行榜',
                text='請選擇',
                actions = [
                    MessageAction(
                        label='台灣排行榜',
                        text='台灣排行榜'
                    ),
                    MessageAction(
                        label='全美排行榜',
                        text='全美排行榜'
                    ),
                    MessageAction(
                        label='年度排行榜',
                        text='年度排行榜'
                    )
                ])
            )
        line_bot_api.reply_message(event.reply_token, button_template)

    if event.message.text == '台灣排行榜':
        taiwan_movie_rank = movie_rank('https://movies.yahoo.com.tw/chart.html')
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = taiwan_movie_rank))
    if event.message.text == '全美排行榜':
        US_movie_rank = movie_rank('https://movies.yahoo.com.tw/chart.html?cate=us')
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = US_movie_rank))
    if event.message.text == '年度排行榜':
        year_movie_rank = movie_rank('https://movies.yahoo.com.tw/chart.html?cate=year')
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = year_movie_rank))

if __name__ == "__main__":
    app.run()